import os
import re
import sys
import time
import zipfile
import shutil
import subprocess
import urllib.request
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Optional

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript

    PY_LANGUAGE = Language(tree_sitter_python.language())
    JS_LANGUAGE = Language(tree_sitter_javascript.language())
    TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
    TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())
    TREE_SITTER_AVAILABLE = True
except Exception as e:
    print(f"[Warning] Tree-sitter native bindings error: {e}. Fallback parser will be used.", file=sys.stderr)
    TREE_SITTER_AVAILABLE = False

from database import CodebaseDB

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
    ".next", ".turbo", ".cache", "target", ".idea", ".vscode", "coverage",
    ".pytest_cache", "site-packages", ".cargo", "bin", "obj"
}

IGNORE_EXTENSIONS = {
    ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".lock",
    ".json", ".map", ".exe", ".dll", ".so", ".dylib", ".wasm", ".zip",
    ".tar", ".gz", ".db", ".sqlite", ".sqlite3", ".env", ".pdf", ".mp4",
    ".woff", ".woff2", ".ttf", ".eot"
}

SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".java": "java",
}


def resolve_target_codebase(target: str) -> Path:
    """
    Resolves local directories, ZIP archives, or public GitHub repository URLs.
    - Clones public GitHub repos to ~/.cluely/github_repos/<owner>_<repo>
    - Auto-extracts .zip files or virtual zip paths (e.g. from Windows Explorer)
    - Resolves and validates local filesystem paths
    """
    clean_target = target.strip().strip('"').strip("'").strip()
    if not clean_target:
        raise ValueError("Repository path or GitHub URL cannot be empty")

    # 1. Check for GitHub Repository URL
    gh_match = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_\-\.]+)\/([a-zA-Z0-9_\-\.]+)', clean_target)
    if gh_match:
        owner = gh_match.group(1)
        repo = gh_match.group(2).replace(".git", "")
        cache_dir = Path.home() / ".cluely" / "github_repos" / f"{owner}_{repo}"
        cache_dir.parent.mkdir(parents=True, exist_ok=True)

        if cache_dir.exists() and any(cache_dir.iterdir()):
            print(f"[Indexer] Using cached GitHub repository: {cache_dir}")
            return cache_dir

        print(f"[Indexer] Cloning public GitHub repo '{owner}/{repo}' into {cache_dir}...")
        clone_url = f"https://github.com/{owner}/{repo}.git"
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(cache_dir)],
                check=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return cache_dir
        except Exception as git_err:
            print(f"[Indexer] Git clone failed ({git_err}), attempting direct ZIP download fallback...")
            # Fallback: Download ZIP from GitHub
            for branch in ["main", "master"]:
                try:
                    zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
                    req = urllib.request.Request(zip_url, headers={'User-Agent': 'Cluely-Context-Engine'})
                    zip_temp = cache_dir.parent / f"{owner}_{repo}_{branch}.zip"
                    with urllib.request.urlopen(req, timeout=30) as response, open(zip_temp, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                    with zipfile.ZipFile(zip_temp, 'r') as zf:
                        zf.extractall(cache_dir.parent)
                    zip_temp.unlink(missing_ok=True)
                    # GitHub zip extracts to <repo>-<branch>
                    extracted_folder = cache_dir.parent / f"{repo}-{branch}"
                    if extracted_folder.exists():
                        if cache_dir.exists():
                            shutil.rmtree(cache_dir)
                        extracted_folder.rename(cache_dir)
                        return cache_dir
                except Exception:
                    continue
            raise ValueError(f"Could not clone or download GitHub repository '{owner}/{repo}'. Please ensure the repo is public.")

    # 2. Check for Standard Local Directory
    p = Path(clean_target)
    if p.exists() and p.is_dir():
        return p.resolve()

    # 3. Check for Direct .ZIP Archive File
    if p.exists() and p.is_file() and p.suffix.lower() == ".zip":
        extract_dir = p.parent / p.stem
        if not extract_dir.exists() or not any(extract_dir.iterdir()):
            print(f"[Indexer] Auto-extracting ZIP archive: {p} -> {extract_dir}")
            with zipfile.ZipFile(p, 'r') as zf:
                zf.extractall(extract_dir)
        return extract_dir.resolve()

    # 4. Check for Virtual ZIP Path (e.g. Windows Explorer C:\path\file.zip\subfolder)
    parts = p.parts
    if parts:
        accum = Path(parts[0])
        for idx, part in enumerate(parts[1:], start=1):
            accum = accum / part
            if accum.suffix.lower() == ".zip" and accum.exists() and accum.is_file():
                extract_root = accum.parent / accum.stem
                if not extract_root.exists() or not any(extract_root.iterdir()):
                    print(f"[Indexer] Auto-extracting parent ZIP: {accum} -> {extract_root}")
                    with zipfile.ZipFile(accum, 'r') as zf:
                        zf.extractall(extract_root)
                
                remaining = parts[idx + 1:]
                if remaining:
                    sub_candidate = extract_root.joinpath(*remaining)
                    if sub_candidate.exists() and sub_candidate.is_dir():
                        return sub_candidate.resolve()
                return extract_root.resolve()

    raise ValueError(
        f"Path '{clean_target}' does not exist on disk. Please enter a valid local folder path, .zip file, or public GitHub URL."
    )


class CodebaseIndexer:
    def __init__(self, db: Optional[CodebaseDB] = None):
        self.db = db or CodebaseDB()
        self.parsers = {}
        if TREE_SITTER_AVAILABLE:
            try:
                p_py = Parser(PY_LANGUAGE)
                self.parsers["python"] = (p_py, "python")
                
                p_js = Parser(JS_LANGUAGE)
                self.parsers["javascript"] = (p_js, "javascript")
                
                p_ts = Parser(TS_LANGUAGE)
                self.parsers["typescript"] = (p_ts, "typescript")
                
                p_tsx = Parser(TSX_LANGUAGE)
                self.parsers["tsx"] = (p_tsx, "tsx")
            except Exception as e:
                print(f"[Warning] Parser init error: {e}")

    def index_directory(self, root_dir: str) -> Dict[str, Any]:
        start_time = time.time()
        root_path = resolve_target_codebase(root_dir)

        all_symbols: List[Dict[str, Any]] = []
        indexed_files_count = 0

        self.db.clear_index()

        for current_root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file_name in files:
                ext = Path(file_name).suffix.lower()
                if ext in IGNORE_EXTENSIONS or ext not in SUPPORTED_LANGUAGES:
                    continue

                full_path = os.path.join(current_root, file_name)
                rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")
                
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        source_code = f.read()

                    lang = SUPPORTED_LANGUAGES[ext]
                    symbols = self.parse_file(full_path, rel_path, source_code, lang, ext)
                    if symbols:
                        all_symbols.extend(symbols)
                    indexed_files_count += 1
                except Exception as ex:
                    print(f"Error parsing file {rel_path}: {ex}", file=sys.stderr)

        # Batch insert all raw AST symbols
        self.db.insert_symbols_batch(all_symbols)

        # Build Macro Topology Map
        topology = self._build_macro_topology(all_symbols)
        self.db.save_topology(topology)

        elapsed = time.time() - start_time

        summary = self.db.get_indexed_summary()
        summary["elapsed_seconds"] = round(elapsed, 3)
        summary["root_path"] = str(root_path)
        summary["resolved_path"] = str(root_path)
        return summary

    def _build_macro_topology(self, all_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups codebase symbols into cohesive, granular sub-modules / subsystems and generates
        a high-density topology summary for the Tier-1 Router.
        """
        module_groups = defaultdict(list)
        for sym in all_symbols:
            rel = sym["relative_path"].replace("\\", "/")
            dir_path = os.path.dirname(rel)
            if not dir_path or dir_path == ".":
                mod_key = rel  # Top-level standalone file
            else:
                parts = [p for p in dir_path.split("/") if p]
                if len(parts) <= 3:
                    mod_key = "/".join(parts)
                else:
                    mod_key = "/".join(parts[:3])
            module_groups[mod_key].append(sym)

        topology = []
        for mod_path, syms in module_groups.items():
            classes = [s["name"] for s in syms if s["symbol_type"] == "class"]
            functions = [s["name"] for s in syms if s["symbol_type"] in ["function", "method"] and not s["name"].startswith("_")]
            
            # Extract sample docstring keywords
            doc_samples = [s["docstring"][:120] for s in syms if s.get("docstring")]
            
            key_exports = classes[:10] + [f for f in functions if not f.startswith("_")][:10]
            
            summary_parts = []
            if classes:
                summary_parts.append(f"Classes: {', '.join(classes[:8])}")
            if functions:
                top_fns = [f for f in functions if not f.startswith("_")][:8]
                if top_fns:
                    summary_parts.append(f"Functions: {', '.join(top_fns)}")
            if doc_samples:
                clean_doc = doc_samples[0].replace("\n", " ").strip()
                summary_parts.append(f"Docs: {clean_doc}")

            summary_text = " | ".join(summary_parts) if summary_parts else f"{len(syms)} code symbols"

            topology.append({
                "module_path": mod_path,
                "module_name": mod_path.replace("/", " > "),
                "summary": summary_text,
                "symbol_count": len(syms),
                "key_symbols": key_exports[:15]
            })

        return sorted(topology, key=lambda x: x["symbol_count"], reverse=True)

    def parse_file(self, full_path: str, rel_path: str, source_code: str, lang: str, ext: str) -> List[Dict[str, Any]]:
        symbols = []
        source_bytes = source_code.encode("utf-8")

        # Try Tree-Sitter first if available
        if TREE_SITTER_AVAILABLE and lang in ["python", "javascript", "typescript"]:
            parser_key = "tsx" if ext == ".tsx" else lang
            if parser_key in self.parsers:
                try:
                    parser, _ = self.parsers[parser_key]
                    tree = parser.parse(source_bytes)
                    symbols = self._extract_tree_sitter_symbols(tree.root_node, source_bytes, source_code, full_path, rel_path, lang)
                    if symbols:
                        return symbols
                except Exception as e:
                    print(f"Tree-sitter parse error for {rel_path}: {e}, falling back to regex")

        # Robust Regex / AST heuristic fallback
        return self._extract_regex_symbols(source_code, full_path, rel_path, lang)

    def _extract_tree_sitter_symbols(self, root_node, source_bytes: bytes, source_code: str, full_path: str, rel_path: str, lang: str) -> List[Dict[str, Any]]:
        symbols = []
        lines = source_code.splitlines()

        def get_node_text(node) -> str:
            return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")

        def traverse(node, current_class=None):
            node_type = node.type

            # Python AST Nodes
            if lang == "python":
                if node_type == "function_definition":
                    name_node = node.child_by_field_name("name")
                    params_node = node.child_by_field_name("parameters")
                    name = get_node_text(name_node) if name_node else "anonymous"
                    params = get_node_text(params_node) if params_node else "()"
                    
                    symbol_type = "method" if current_class else "function"
                    full_name = f"{current_class}.{name}" if current_class else name
                    signature = f"def {full_name}{params}"
                    
                    docstring = ""
                    body_node = node.child_by_field_name("body")
                    if body_node and len(body_node.children) > 0:
                        first_stmt = body_node.children[0]
                        if first_stmt.type == "expression_statement" and len(first_stmt.children) > 0:
                            if first_stmt.children[0].type == "string":
                                docstring = get_node_text(first_stmt.children[0]).strip(" '\"\n\t")

                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    snippet = "\n".join(lines[start_line - 1:end_line])

                    symbols.append({
                        "file_path": full_path,
                        "relative_path": rel_path,
                        "name": full_name,
                        "symbol_type": symbol_type,
                        "signature": signature,
                        "docstring": docstring,
                        "start_line": start_line,
                        "end_line": end_line,
                        "code_snippet": snippet[:1500],
                        "language": lang
                    })

                elif node_type == "class_definition":
                    name_node = node.child_by_field_name("name")
                    superclasses = node.child_by_field_name("superclasses")
                    name = get_node_text(name_node) if name_node else "AnonymousClass"
                    bases = get_node_text(superclasses) if superclasses else ""
                    signature = f"class {name}{bases}"

                    docstring = ""
                    body_node = node.child_by_field_name("body")
                    if body_node and len(body_node.children) > 0:
                        first_stmt = body_node.children[0]
                        if first_stmt.type == "expression_statement" and len(first_stmt.children) > 0:
                            if first_stmt.children[0].type == "string":
                                docstring = get_node_text(first_stmt.children[0]).strip(" '\"\n\t")

                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    snippet = "\n".join(lines[start_line - 1:min(end_line, start_line + 30)])

                    symbols.append({
                        "file_path": full_path,
                        "relative_path": rel_path,
                        "name": name,
                        "symbol_type": "class",
                        "signature": signature,
                        "docstring": docstring,
                        "start_line": start_line,
                        "end_line": end_line,
                        "code_snippet": snippet[:1500],
                        "language": lang
                    })
                    
                    for child in node.children:
                        traverse(child, current_class=name)
                    return

            # JS / TS AST Nodes
            elif lang in ["javascript", "typescript"]:
                if node_type in ["function_declaration", "method_definition", "arrow_function", "function"]:
                    name_node = node.child_by_field_name("name")
                    name = get_node_text(name_node) if name_node else None
                    
                    if not name and node.parent and node.parent.type == "variable_declarator":
                        var_name_node = node.parent.child_by_field_name("name")
                        name = get_node_text(var_name_node) if var_name_node else "anonymous"

                    if name:
                        symbol_type = "method" if (current_class or node_type == "method_definition") else "function"
                        full_name = f"{current_class}.{name}" if current_class else name
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1
                        snippet = "\n".join(lines[start_line - 1:end_line])
                        first_line = lines[start_line - 1].strip()

                        symbols.append({
                            "file_path": full_path,
                            "relative_path": rel_path,
                            "name": full_name,
                            "symbol_type": symbol_type,
                            "signature": first_line[:120],
                            "docstring": "",
                            "start_line": start_line,
                            "end_line": end_line,
                            "code_snippet": snippet[:1500],
                            "language": lang
                        })

                elif node_type in ["class_declaration", "interface_declaration"]:
                    name_node = node.child_by_field_name("name")
                    name = get_node_text(name_node) if name_node else "AnonymousClass"
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    snippet = "\n".join(lines[start_line - 1:min(end_line, start_line + 30)])
                    sym_type = "interface" if "interface" in node_type else "class"

                    symbols.append({
                        "file_path": full_path,
                        "relative_path": rel_path,
                        "name": name,
                        "symbol_type": sym_type,
                        "signature": lines[start_line - 1].strip()[:120],
                        "docstring": "",
                        "start_line": start_line,
                        "end_line": end_line,
                        "code_snippet": snippet[:1500],
                        "language": lang
                    })

                    for child in node.children:
                        traverse(child, current_class=name)
                    return

            for child in node.children:
                traverse(child, current_class)

        traverse(root_node)
        return symbols

    def _extract_regex_symbols(self, source_code: str, full_path: str, rel_path: str, lang: str) -> List[Dict[str, Any]]:
        symbols = []
        lines = source_code.splitlines()

        patterns = [
            (r'^(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)(?:\s*->\s*[^:]+)?:', 'function', 'def {name}({args})'),
            (r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\((.*?)\))?:', 'class', 'class {name}({args})'),
            (r'^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)', 'function', 'function {name}({args})'),
            (r'^(?:export\s+)?(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>', 'function', 'const {name} = ({args}) =>'),
            (r'^(?:export\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'class', 'class {name}'),
            (r'^(?:export\s+)?interface\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'interface', 'interface {name}'),
            (r'^(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:<.*?>)?\s*\((.*?)\)', 'function', 'fn {name}({args})'),
            (r'^(?:pub\s+)?struct\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'struct', 'struct {name}'),
            (r'^func\s+(?:\(.*?\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)', 'function', 'func {name}({args})'),
            (r'^type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+struct', 'struct', 'type {name} struct'),
        ]

        for i, line in enumerate(lines):
            stripped = line.strip()
            for regex, sym_type, sig_template in patterns:
                match = re.search(regex, stripped)
                if match:
                    name = match.group(1)
                    args = match.group(2) if len(match.groups()) > 1 and match.group(2) is not None else ""
                    signature = sig_template.format(name=name, args=args)
                    
                    start_line = i + 1
                    end_line = min(len(lines), start_line + 25)
                    snippet = "\n".join(lines[start_line - 1:end_line])

                    symbols.append({
                        "file_path": full_path,
                        "relative_path": rel_path,
                        "name": name,
                        "symbol_type": sym_type,
                        "signature": signature[:120],
                        "docstring": "",
                        "start_line": start_line,
                        "end_line": end_line,
                        "code_snippet": snippet[:1500],
                        "language": lang
                    })
                    break

        return symbols
