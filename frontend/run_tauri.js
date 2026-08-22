import os from 'os';
import path from 'path';
import { spawn } from 'child_process';

// Prepend ~/.cargo/bin to PATH so Tauri CLI always finds cargo and rustc
const cargoBin = path.join(os.homedir(), '.cargo', 'bin');
const env = { 
  ...process.env, 
  PATH: `${cargoBin}${path.delimiter}${process.env.PATH}`,
  CARGO_TARGET_DIR: path.join(os.homedir(), '.cargo', 'cluely-target')
};

const args = process.argv.slice(2);
const cmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';

const child = spawn(cmd, ['tauri', ...args], {
  env,
  stdio: 'inherit',
  shell: true,
  cwd: path.resolve(import.meta.dirname || process.cwd())
});

child.on('exit', (code) => {
  process.exit(code || 0);
});
