"""Stack matching before/after renders into one labelled JPEG, and report how much changed.

  python3 tools/compose_before_after.py renders/broadleaf_library BEFORE_AFTER_B "Pass-1 broadleaf" "Broadleaf library"

Reads <dir>/before/<name>.png and <dir>/after/<name>.png for every name present in both, writes
renders/<prefix><name>.jpg, and prints the fraction of pixels that differ by more than 8/255 in any
channel. That fraction is the honest measure of what a change actually did: a camera that sees none
of the changed thing should score near zero, and one that does should not.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


# PIL's built-in bitmap font has no em-dash and is unreadably small on a 1280-wide plate.
_FONT = None
for _p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
           '/usr/share/fonts/truetype/freefont/FreeSans.ttf'):
    if Path(_p).exists():
        _FONT = ImageFont.truetype(_p, 17)
        break


def label(img, text):
    bar = 30 if _FONT else 26
    out = Image.new('RGB', (img.width, img.height + bar), (16, 16, 16))
    out.paste(img.convert('RGB'), (0, bar))
    ImageDraw.Draw(out).text((12, 7), text, fill=(235, 235, 235), font=_FONT)
    return out


def main():
    base = Path(sys.argv[1])
    prefix = sys.argv[2] if len(sys.argv) > 2 else 'BEFORE_AFTER_'
    ltext = sys.argv[3] if len(sys.argv) > 3 else 'before'
    rtext = sys.argv[4] if len(sys.argv) > 4 else 'after'
    bdir, adir = base / 'before', base / 'after'

    def find(d, stem):
        for ext in ('.png', '.jpg', '.jpeg'):
            if (d / (stem + ext)).exists():
                return d / (stem + ext)
        return None

    names = sorted({p.stem for p in bdir.iterdir()
                    if p.suffix.lower() in ('.png', '.jpg', '.jpeg') and find(adir, p.stem)})
    if not names:
        print('no matching pairs in', bdir, 'and', adir)
        return 1
    for n in names:
        b = Image.open(find(bdir, n))
        a = Image.open(find(adir, n))
        if b.size != a.size:
            print(f'{n}: size mismatch {b.size} vs {a.size}, skipped')
            continue
        db = np.asarray(b.convert('RGB')).astype(np.int16)
        da = np.asarray(a.convert('RGB')).astype(np.int16)
        changed = (np.abs(da - db).max(axis=2) > 8).mean()
        left, right = label(b, f'{ltext} — {n}'), label(a, f'{rtext} — {n}')
        sheet = Image.new('RGB', (left.width, left.height * 2 + 4), (16, 16, 16))
        sheet.paste(left, (0, 0))
        sheet.paste(right, (0, left.height + 4))
        out = ROOT / 'renders' / f'{prefix}{n}.jpg'
        sheet.save(out, quality=88)
        print(f'{n:26} pixels changed {changed*100:5.1f}%   -> {out.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
