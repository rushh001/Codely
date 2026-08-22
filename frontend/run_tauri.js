import os from 'os';
import path from 'path';
import fs from 'fs';
import { spawn } from 'child_process';

const cargoTargetDir = path.join(os.homedir(), '.cargo', 'cluely-target');
const cargoBin = path.join(os.homedir(), '.cargo', 'bin');

const env = { 
  ...process.env, 
  PATH: `${cargoBin}${path.delimiter}${process.env.PATH}`,
  CARGO_TARGET_DIR: cargoTargetDir
};

const args = process.argv.slice(2);
const isBuild = args.includes('build');
const cmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';

const child = spawn(cmd, ['tauri', ...args], {
  env,
  stdio: 'inherit',
  shell: true,
  cwd: path.resolve(import.meta.dirname || process.cwd())
});

child.on('exit', (code) => {
  if (code === 0 && isBuild) {
    try {
      // Copy bundles to project root ./dist-installers/
      const projectRoot = path.resolve(import.meta.dirname || process.cwd(), '..');
      const distInstallers = path.join(projectRoot, 'dist-installers');
      
      if (!fs.existsSync(distInstallers)) {
        fs.mkdirSync(distInstallers, { recursive: true });
      }

      const bundleSrcDir = path.join(cargoTargetDir, 'release', 'bundle');
      if (fs.existsSync(bundleSrcDir)) {
        copyRecursiveSync(bundleSrcDir, distInstallers);
        console.log('\n======================================================');
        console.log('🎉 Installers copied directly to your project directory:');
        console.log(`📁 ${distInstallers}`);
        console.log('======================================================\n');
      }
    } catch (err) {
      console.warn('[Warning] Could not copy bundles to project root:', err.message);
    }
  }
  process.exit(code || 0);
});

function copyRecursiveSync(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();
  if (isDirectory) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    fs.readdirSync(src).forEach((childItemName) => {
      copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}
