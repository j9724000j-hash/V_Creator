// Local bundled Chromium for HyperFrames on lean Linux hosts without libnss.
// This only extracts the already-installed @sparticuz/chromium npm package.
import chromium from '@sparticuz/chromium';
import {readFileSync, writeFileSync, existsSync, mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {brotliDecompressSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';

if (process.platform !== 'linux') {
  console.error('Use HyperFrames browser ensure or HYPERFRAMES_BROWSER_PATH on this platform.');
  process.exit(1);
}
const root = resolve(import.meta.dirname, '..');
const libDir = resolve(root, '.cache/chromium-libs');
if (!existsSync(resolve(libDir, 'lib/libnss3.so'))) {
  mkdirSync(libDir, {recursive: true});
  const archive = resolve(root, 'node_modules/@sparticuz/chromium/bin/al2023.tar.br');
  const tarPath = resolve(libDir, 'al2023.tar');
  writeFileSync(tarPath, brotliDecompressSync(readFileSync(archive)));
  execFileSync('tar', ['-xf', tarPath, '-C', libDir]);
}
console.log(await chromium.executablePath());
