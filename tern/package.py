"""Zip a built Tern into tern-win/ with the same file list Chromium's own archives use.

The list comes from chrome/tools/build/win/FILES.cfg: every entry for official
builds that goes into the main archive (no 'archive' key). Optional entries and
entries this build did not produce (tests, installer) are skipped; the browser's
core files must be present.

Usage: python -I package.py <src> <out dir> <zip path>
"""
import ast
import glob
import sys
import zipfile
from pathlib import Path

REQUIRED = ['chrome.exe', 'chrome.dll', 'chrome_elf.dll', 'ffmpeg.dll', 'resources.pak',
            'chrome_100_percent.pak', 'icudtl.dat', 'v8_context_snapshot.bin', 'locales/en-US.pak',
            'credits.html', 'LICENSE']
TOP = 'tern-win'


def file_list(src):
    text = (Path(src) / 'chrome/tools/build/win/FILES.cfg').read_text(encoding='utf-8')
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == 'FILES':
            return ast.literal_eval(node.value)
    sys.exit('package: no FILES list in FILES.cfg')


def main(src, out, zip_path):
    out = Path(out)
    names = set()
    for e in file_list(src):
        if 'official' in e.get('buildtype', []) and 'archive' not in e:
            for p in glob.glob(str(out / e['filename']), recursive=True):
                names.add(Path(p).relative_to(out).as_posix())
    names.update(n for n in ('credits.html', 'ffmpeg.dll', 'LICENSE') if (out / n).exists())
    missing = [r for r in REQUIRED if r not in names]
    if missing:
        sys.exit(f'package: missing from the build: {missing}')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for n in sorted(names):
            p = out / n
            if p.is_dir():
                for f in sorted(p.rglob('*')):
                    if f.is_file():
                        z.write(f, f'{TOP}/{f.relative_to(out).as_posix()}')
            else:
                z.write(p, f'{TOP}/{n}')
    print(f'package: {len(names)} entries -> {zip_path}')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
