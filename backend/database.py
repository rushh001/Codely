import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "context_index.db")

class CodebaseDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._cached_topology: Optional[List[Dict[str, Any]]] = None
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Base table for code symbols
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                name TEXT NOT NULL,
                symbol_type TEXT NOT NULL, -- function, class, method, variable, interface
                signature TEXT,
                docstring TEXT,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                code_snippet TEXT NOT NULL,
                language TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table for codebase macro topology (module level abstractions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS codebase_topology (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_path TEXT NOT NULL UNIQUE,
                module_name TEXT NOT NULL,
                summary TEXT NOT NULL,
                symbol_count INTEGER NOT NULL,
                key_symbols TEXT NOT NULL, -- JSON list of top symbols/classes/functions
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # FTS5 Virtual Table for sub-millisecond BM25 keyword & symbol search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
                name,
                symbol_type,
                signature,
                docstring,
                relative_path,
                code_snippet,
                content='symbols',
                content_rowid='id',
                tokenize='porter unicode61'
            )
        """)

        # Triggers to keep FTS index synced with symbols table
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
                INSERT INTO symbols_fts(rowid, name, symbol_type, signature, docstring, relative_path, code_snippet)
                VALUES (new.id, new.name, new.symbol_type, new.signature, new.docstring, new.relative_path, new.code_snippet);
            END;
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
                INSERT INTO symbols_fts(symbols_fts, rowid, name, symbol_type, signature, docstring, relative_path, code_snippet)
                VALUES('delete', old.id, old.name, old.symbol_type, old.signature, old.docstring, old.relative_path, old.code_snippet);
            END;
        """)

        # Table for project metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()

    def clear_index(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM symbols_fts")
        cursor.execute("DELETE FROM codebase_topology")
        conn.commit()
        conn.close()
        self._cached_topology = None

    def insert_symbols_batch(self, symbols: List[Dict[str, Any]]):
        if not symbols:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.executemany("""
            INSERT INTO symbols (
                file_path, relative_path, name, symbol_type,
                signature, docstring, start_line, end_line,
                code_snippet, language
            ) VALUES (
                :file_path, :relative_path, :name, :symbol_type,
                :signature, :docstring, :start_line, :end_line,
                :code_snippet, :language
            )
        """, symbols)
        
        conn.commit()
        conn.close()

    def save_topology(self, modules: List[Dict[str, Any]]):
        if not modules:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM codebase_topology")
        for m in modules:
            cursor.execute("""
                INSERT INTO codebase_topology (
                    module_path, module_name, summary, symbol_count, key_symbols
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                m["module_path"],
                m["module_name"],
                m["summary"],
                m["symbol_count"],
                json.dumps(m.get("key_symbols", []))
            ))
        conn.commit()
        conn.close()
        self._cached_topology = modules

    def get_topology(self) -> List[Dict[str, Any]]:
        if self._cached_topology:
            return self._cached_topology
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT module_path, module_name, summary, symbol_count, key_symbols FROM codebase_topology ORDER BY symbol_count DESC")
        rows = cursor.fetchall()
        topology = []
        for r in rows:
            topology.append({
                "module_path": r["module_path"],
                "module_name": r["module_name"],
                "summary": r["summary"],
                "symbol_count": r["symbol_count"],
                "key_symbols": json.loads(r["key_symbols"]) if r["key_symbols"] else []
            })
        conn.close()
        self._cached_topology = topology
        return topology

    def get_symbols_by_modules(self, module_prefixes: List[str], limit: int = 35) -> List[Dict[str, Any]]:
        if not module_prefixes:
            return []
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build dynamic LIKE clauses
        clauses = []
        params = []
        for p in module_prefixes:
            norm_p = p.replace("\\", "/").strip("/")
            clauses.append("relative_path LIKE ?")
            params.append(f"%{norm_p}%")
        
        sql = f"""
            SELECT id, name, symbol_type, relative_path, start_line, end_line, signature, docstring, code_snippet, language
            FROM symbols
            WHERE {' OR '.join(clauses)}
            ORDER BY CASE WHEN symbol_type = 'class' THEN 1 WHEN symbol_type = 'function' THEN 2 ELSE 3 END
            LIMIT ?
        """
        params.append(limit)
        cursor.execute(sql, params)
        results = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return results

    def search_symbols(self, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        # Sanitize query for FTS5 (escape special chars)
        clean_tokens = [f'"{token}"*' for token in query.replace('"', '').replace("'", "").split() if token.strip()]
        if not clean_tokens:
            conn.close()
            return []

        fts_query = " OR ".join(clean_tokens)

        try:
            cursor.execute("""
                SELECT s.*, rank
                FROM symbols_fts f
                JOIN symbols s ON f.rowid = s.id
                WHERE symbols_fts MATCH ?
                ORDER BY CASE WHEN s.symbol_type = 'class' THEN 0 WHEN s.symbol_type = 'function' THEN 1 ELSE 2 END, rank
                LIMIT ?
            """, (fts_query, limit))
            
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            conn.close()
            return results
        except sqlite3.OperationalError:
            like_query = f"%{query.strip()}%"
            cursor.execute("""
                SELECT * FROM symbols
                WHERE name LIKE ? OR relative_path LIKE ? OR signature LIKE ?
                LIMIT ?
            """, (like_query, like_query, like_query, limit))
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            conn.close()
            return results

    def get_symbol_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM symbols")
        count = cursor.fetchone()["count"]
        conn.close()
        return count

    def get_indexed_summary(self) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total_symbols, COUNT(DISTINCT relative_path) as total_files FROM symbols")
        row = cursor.fetchone()
        
        cursor.execute("SELECT symbol_type, COUNT(*) as cnt FROM symbols GROUP BY symbol_type")
        types = {r["symbol_type"]: r["cnt"] for r in cursor.fetchall()}
        
        cursor.execute("SELECT language, COUNT(*) as cnt FROM symbols GROUP BY language")
        languages = {r["language"]: r["cnt"] for r in cursor.fetchall()}
        
        conn.close()
        return {
            "total_symbols": row["total_symbols"],
            "total_files": row["total_files"],
            "types": types,
            "languages": languages,
            "topology_modules": len(self.get_topology())
        }
