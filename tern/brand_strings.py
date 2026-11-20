"""Replace the product name "Chromium" with Tern's name in the browser's UI strings.

Chromium's translations (.xtb) are keyed by a fingerprint of the English text, so
changing the English text alone would orphan every translation. This script uses
grit (Chromium's own resource tool) to compute each message's id before and after
the change, then rewrites the translations with the new ids and the new name.

Usage: python -I brand_strings.py <chromium src dir> <product name>
"""
import re
import sys
from pathlib import Path

GRDS = ['chrome/app/chromium_strings.grd']  # its <part> grdp files are found by grit
KEEP = re.compile(r'Chromium (Authors|OS|Projects?)\b|ChromiumOS|chromium\.org')
WORD = re.compile(r'\bChromium\b')


def rename(text, name):
    """Replace "Chromium" with name, except in names that must stay (authors, OS, URLs)."""
    keep = {}

    def hold(m):
        keep[f'\0{len(keep)}\0'] = m.group(0)
        return f'\0{len(keep) - 1}\0'

    text = KEEP.sub(hold, text)
    text = WORD.sub(name, text)
    for k, v in keep.items():
        text = text.replace(k, v)
    return text


def rename_bodies(xml, tag, name):
    """Rename inside <tag ...>body</tag> bodies only, never in attributes."""
    pat = re.compile(r'(<%s\b[^>]*>)(.*?)(</%s>)' % (tag, tag), re.S)
    return pat.sub(lambda m: m.group(1) + rename(m.group(2), name) + m.group(3), xml)


def message_ids(grd):
    from grit import grd_reader
    from grit.node import message
    # Every message, also those inside <if> for other platforms, keyed by its
    # position (the same name can appear in several <if> branches).
    text = '\n'.join(f.read_text(encoding='utf-8') for f in [grd, *_part_files(grd)])
    names = set(re.findall(r'[A-Za-z_]\w*', ' '.join(re.findall(r'expr="([^"]*)"', text))))
    names -= {'and', 'or', 'not', 'in', 'True', 'False', 'lang', 'context', 'pp_if', 'pp_ifdef'}
    defines = {v: 'for_testing' not in v for v in names if not v.startswith('is_')}
    root = grd_reader.Parse(str(grd), debug=False, defines=defines)
    return [n.GetCliques()[0].GetMessage().GetId()
            for n in root.Preorder() if isinstance(n, message.MessageNode)]


def main(src, name):
    src = Path(src)
    sys.path.insert(0, str(src / 'tools/grit'))
    total = {'messages': 0, 'translations': 0, 'xtb_files': 0}
    for rel in GRDS:
        grd = src / rel
        before = message_ids(grd)
        parts = [grd] + sorted({Path(p) for p in _part_files(grd)})
        for f in parts:
            f.write_text(rename_bodies(f.read_text(encoding='utf-8'), 'message', name), encoding='utf-8')
        after = message_ids(grd)
        if len(before) != len(after):
            sys.exit('brand_strings: message count changed while renaming')
        idmap = {b: a for b, a in zip(before, after) if b != a}
        total['messages'] += len(idmap)
        for xtb in sorted(set(_xtb_files(grd))):
            text = xtb.read_text(encoding='utf-8')

            def fix(m):
                old = m.group(2)
                if old not in idmap:
                    return m.group(0)
                total['translations'] += 1
                return m.group(1) + idmap[old] + m.group(3) + rename(m.group(4), name) + m.group(5)

            text = re.sub(r'(<translation id=")(\d+)("[^>]*>)(.*?)(</translation>)', fix, text, flags=re.S)
            xtb.write_text(text, encoding='utf-8')
            total['xtb_files'] += 1
    left = sum(len(WORD.findall(rename_bodies_left(f))) for f in _all(src))
    print(f"renamed {total['messages']} messages, {total['translations']} translations in "
          f"{total['xtb_files']} xtb files; 'Chromium' left in message bodies: {left}")
    if total['messages'] == 0 or total['translations'] == 0:
        sys.exit('brand_strings: nothing renamed, the source layout changed')


def _part_files(grd):
    for m in re.finditer(r'<part file="([^"]+)"', grd.read_text(encoding='utf-8')):
        yield grd.parent / m.group(1)


def _xtb_files(grd):
    for m in re.finditer(r'<file path="([^"]+\.xtb)"', grd.read_text(encoding='utf-8')):
        yield grd.parent / m.group(1)


def _all(src):
    for rel in GRDS:
        grd = src / rel
        yield grd
        yield from _part_files(grd)


def rename_bodies_left(f):
    """Message bodies with the kept names removed, to count what was not renamed."""
    bodies = re.findall(r'<message\b[^>]*>(.*?)</message>', f.read_text(encoding='utf-8'), re.S)
    return KEEP.sub('', '\n'.join(bodies))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
