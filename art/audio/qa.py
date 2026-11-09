"""QA for RuneWire audio: stats plus waveform/spectrogram contact sheets (PNG).

Reads the written WAV files back, so it checks what Godot will import.
Standalone use (all files, writes art/previews/audio/*.png and prints a table):

    env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/qa.py
"""
import math
import os
import struct
import sys
import zlib

import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PREV = os.path.join(ROOT, 'art', 'previews', 'audio')

_G = """
A .###. #...# #...# ##### #...# #...# #...#
B ####. #...# #...# ####. #...# #...# ####.
C .###. #...# #.... #.... #.... #...# .###.
D ###.. #..#. #...# #...# #...# #..#. ###..
E ##### #.... #.... ####. #.... #.... #####
F ##### #.... #.... ####. #.... #.... #....
G .###. #...# #.... #.### #...# #...# .####
H #...# #...# #...# ##### #...# #...# #...#
I .###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.
J ..### ...#. ...#. ...#. ...#. #..#. .##..
K #...# #..#. #.#.. ##... #.#.. #..#. #...#
L #.... #.... #.... #.... #.... #.... #####
M #...# ##.## #.#.# #.#.# #...# #...# #...#
N #...# #...# ##..# #.#.# #..## #...# #...#
O .###. #...# #...# #...# #...# #...# .###.
P ####. #...# #...# ####. #.... #.... #....
Q .###. #...# #...# #...# #.#.# #..#. .##.#
R ####. #...# #...# ####. #.#.. #..#. #...#
S .#### #.... #.... .###. ....# ....# ####.
T ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# #...# #...# .###.
V #...# #...# #...# #...# #...# .#.#. ..#..
W #...# #...# #...# #.#.# #.#.# #.#.# .#.#.
X #...# #...# .#.#. ..#.. .#.#. #...# #...#
Y #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
Z ##### ....# ...#. ..#.. .#... #.... #####
0 .###. #...# #..## #.#.# ##..# #...# .###.
1 ..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.
2 .###. #...# ....# ...#. ..#.. .#... #####
3 ##### ...#. ..#.. ...#. ....# #...# .###.
4 ...#. ..##. .#.#. #..#. ##### ...#. ...#.
5 ##### #.... ####. ....# ....# #...# .###.
6 ..##. .#... #.... ####. #...# #...# .###.
7 ##### ....# ...#. ..#.. .#... .#... .#...
8 .###. #...# #...# .###. #...# #...# .###.
9 .###. #...# #...# .#### ....# ...#. .##..
_ ..... ..... ..... ..... ..... ..... #####
- ..... ..... ..... ##### ..... ..... .....
. ..... ..... ..... ..... ..... .##.. .##..
: ..... .##.. .##.. ..... .##.. .##.. .....
/ ....# ....# ...#. ..#.. .#... #.... #....
( ...#. ..#.. .#... .#... .#... ..#.. ...#.
) .#... ..#.. ...#. ...#. ...#. ..#.. .#...
% ##..# ##..# ...#. ..#.. .#... #..## #..##
+ ..... ..#.. ..#.. ##### ..#.. ..#.. .....
= ..... ..... ##### ..... ##### ..... .....
, ..... ..... ..... ..... .##.. ..#.. .#...
? .###. #...# ....# ...#. ..#.. ..... ..#..
"""
FONT = {}
for _line in _G.strip().splitlines():
    _c, *_rows = _line.split(' ')
    FONT[_c] = _rows
FONT[' '] = ['.....'] * 7


def save_png(path, img):
    img = np.ascontiguousarray(img, dtype=np.uint8)
    h, w, _ = img.shape
    raw = b''.join(b'\x00' + img[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) \
        + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b'')
    with open(path, 'wb') as fh:
        fh.write(png)


def text(img, x, y, s, color=(235, 235, 235), scale=1):
    for ch in s.upper():
        g = FONT.get(ch, FONT['?'])
        for r, row in enumerate(g):
            for c, px in enumerate(row):
                if px == '#':
                    y0, x0 = y + r * scale, x + c * scale
                    if 0 <= y0 < img.shape[0] - scale and 0 <= x0 < img.shape[1] - scale:
                        img[y0:y0 + scale, x0:x0 + scale] = color
        x += 6 * scale


_CM = np.array([[0.0, 10, 10, 24], [0.25, 50, 18, 100], [0.5, 165, 40, 110],
                [0.72, 240, 120, 40], [0.9, 255, 215, 90], [1.0, 255, 255, 220]])


def colormap(v):
    v = np.clip(v, 0, 1)
    return np.stack([np.interp(v, _CM[:, 0], _CM[:, k]) for k in (1, 2, 3)], axis=-1).astype(np.uint8)


def draw_wave(img, x0, y0, w, h, x, color=(120, 220, 160)):
    img[y0:y0 + h, x0:x0 + w] = (18, 20, 28)
    n = len(x)
    mid = y0 + h // 2
    ref = S.db2a(-1.0)
    for yy in (mid - int(ref * (h // 2 - 1)), mid + int(ref * (h // 2 - 1))):
        img[yy, x0:x0 + w] = (90, 40, 40)
    img[mid, x0:x0 + w] = (50, 55, 70)
    edges = np.linspace(0, n, w + 1).astype(int)
    for c in range(w):
        a, b = edges[c], max(edges[c + 1], edges[c] + 1)
        seg = x[a:b]
        if len(seg) == 0:
            continue
        lo, hi = seg.min(), seg.max()
        r0 = mid - int(round(hi * (h // 2 - 1)))
        r1 = mid - int(round(lo * (h // 2 - 1)))
        r0, r1 = max(y0, min(r0, r1)), min(y0 + h - 1, max(r0, r1))
        col = (255, 80, 80) if max(abs(lo), abs(hi)) > 0.999 else color
        img[r0:r1 + 1, x0 + c] = col


def draw_spec(img, x0, y0, w, h, x, fmin=40.0, fmax=20000.0, rng_db=75.0):
    n = len(x)
    frame = 2048 if n > 4 * 44100 else 1024 if n > 22050 else 512
    xp = np.concatenate([np.zeros(frame), x, np.zeros(frame)])
    centers = np.linspace(frame, frame + n, w).astype(int)
    win = np.hanning(frame)
    idx = centers[:, None] + np.arange(frame)[None, :] - frame // 2
    F = np.abs(np.fft.rfft(xp[idx] * win, axis=1))
    freqs = np.fft.rfftfreq(frame, 1.0 / S.SR)
    rows = np.exp(np.linspace(math.log(fmax), math.log(fmin), h))
    # map each row to the max over the bins it covers
    edges = np.sqrt(rows[:-1] * rows[1:])
    edges = np.concatenate([[fmax * 1.02], edges, [fmin * 0.98]])
    M = np.zeros((h, w))
    for r in range(h):
        hi_, lo_ = edges[r], edges[r + 1]
        m = (freqs >= lo_) & (freqs < hi_)
        if m.any():
            M[r] = F[:, m].max(axis=1)
        else:
            M[r] = F[:, np.argmin(np.abs(freqs - rows[r]))]
    D = 20 * np.log10(M + 1e-9)
    D = (D - (D.max() - rng_db)) / rng_db
    img[y0:y0 + h, x0:x0 + w] = colormap(D)
    for fl in (100, 1000, 10000):  # grid ticks
        r = int(round((math.log(fmax) - math.log(fl)) / (math.log(fmax) - math.log(fmin)) * (h - 1)))
        img[y0 + r, x0:x0 + 4] = (200, 200, 200)


def analyze(path):
    a, sr, loop = S.read_wav(path)
    mono = a.mean(axis=0)
    n = a.shape[1]
    peak = float(np.max(np.abs(a)))
    rms = float(np.sqrt(np.mean(a ** 2)))
    st = dict(name=os.path.splitext(os.path.basename(path))[0], ch=a.shape[0], sr=sr, n=n,
              dur=n / sr, peak_db=float(S.a2db(peak)), rms_db=float(S.a2db(rms)), loop=loop is not None,
              loop_pts=loop, dc=float(np.mean(mono)))
    st['tp_db'] = float(S.a2db(S.true_peak(a if a.shape[0] > 1 else a[0])))
    F = np.abs(np.fft.rfft(mono)) ** 2
    fr = np.fft.rfftfreq(len(mono), 1.0 / sr)
    st['hf'] = float(100.0 * F[fr > 4000].sum() / (F.sum() + 1e-20))
    st['lo'] = float(100.0 * F[fr < 150].sum() / (F.sum() + 1e-20))
    if loop is not None:
        st['lufs'] = S.loudness_int(a if a.shape[0] > 1 else a[0], circular=True)
        # seam jump relative to the typical sample-to-sample change right around it
        d = np.abs(np.diff(mono))
        local = np.concatenate([d[:400], d[-400:]])
        seam = abs(mono[0] - mono[-1])
        st['seam'] = float(seam / (np.percentile(local, 90) + 1e-9))
    else:
        st['lufs'] = S.loudness_max(a if a.shape[0] > 1 else a[0], 0.2)
        st['seam'] = None
        st['start'] = float(abs(mono[0]))
        st['end'] = float(np.max(np.abs(mono[-16:])))
    return st, a


def panel(st, a, w=372):
    loop = st['loop']
    hw, hs, hz_ = 54, 64, (34 if loop else 0)
    H = 12 + hw + 2 + hs + (2 + hz_ if loop else 0) + 6
    img = np.zeros((H, w, 3), np.uint8)
    img[:] = (30, 32, 42)
    mono = a.mean(axis=0)
    text(img, 3, 3, st['name'][:30], (255, 230, 150))
    info = '%.2fS %s' % (st['dur'], 'LOOP' if loop else '')
    text(img, w - 6 * len(info) - 3, 3, info, (170, 200, 255))
    draw_wave(img, 2, 12, w - 4, hw, mono)
    lab = 'PK %.1f  RMS %.1f  L %.1f' % (st['peak_db'], st['rms_db'], st['lufs'])
    text(img, 5, 14, lab, (200, 200, 200))
    draw_spec(img, 2, 12 + hw + 2, w - 4, hs, mono)
    if loop:
        y0 = 12 + hw + 2 + hs + 2
        k = int(0.015 * st['sr'])
        seg = np.concatenate([mono[-k:], mono[:k]])
        mx = max(np.max(np.abs(seg)), 1e-6)
        draw_wave(img, 2, y0, w - 4, hz_, seg / mx, (150, 190, 255))
        img[y0:y0 + hz_, 2 + (w - 4) // 2] = (255, 90, 90)
        text(img, 5, y0 + 2, 'SEAM %.2f' % st['seam'], (255, 255, 255))
    return img


def sheet(panels, cols=3, title=None):
    w = panels[0].shape[1]
    rows = int(math.ceil(len(panels) / cols))
    hs = []
    for r in range(rows):
        hs.append(max(p.shape[0] for p in panels[r * cols:(r + 1) * cols]))
    top = 16 if title else 0
    img = np.zeros((top + sum(hs) + 4 * rows + 4, cols * (w + 4) + 4, 3), np.uint8)
    img[:] = (12, 12, 16)
    if title:
        text(img, 6, 4, title, (255, 255, 255))
    y = top + 4
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            if i >= len(panels):
                break
            p = panels[i]
            img[y:y + p.shape[0], 4 + c * (w + 4):4 + c * (w + 4) + w] = p
        y += hs[r] + 4
    return img


def music_sheet(st, a, w=1400):
    """Overview of a music loop: waveform, spectrogram, short-term loudness, seam."""
    mono = a.mean(axis=0)
    hw, hs, hl, hz_ = 110, 200, 70, 60
    H = 16 + hw + 4 + hs + 4 + hl + 4 + hz_ + 6
    img = np.zeros((H, w, 3), np.uint8)
    img[:] = (30, 32, 42)
    text(img, 4, 4, '%s  %.1fS  PK %.1f DBFS  TP %.1f  RMS %.1f  LUFS %.1f  SEAM %.2f' % (
        st['name'], st['dur'], st['peak_db'], st['tp_db'], st['rms_db'], st['lufs'], st['seam']),
        (255, 230, 150))
    y = 16
    draw_wave(img, 2, y, w - 4, hw // 2, a[0], (120, 220, 160))
    draw_wave(img, 2, y + hw // 2, w - 4, hw // 2, a[-1], (120, 200, 230))
    y += hw + 4
    draw_spec(img, 2, y, w - 4, hs, mono, 30.0, 20000.0, 80.0)
    y += hs + 4
    # short-term loudness (3 s windows), circular
    k = S.kweight(a, circular=True)
    p = (k ** 2).sum(axis=0)
    n = len(p)
    win = int(3 * st['sr'])
    c = np.concatenate([[0.0], np.cumsum(np.concatenate([p, p[:win]]))])
    xs = np.linspace(0, n - 1, w - 4).astype(int)
    lt = -0.691 + 10 * np.log10((c[xs + win] - c[xs]) / win + 1e-12)
    img[y:y + hl, 2:w - 2] = (18, 20, 28)
    for ref in (-10, -20, -30):
        r = y + int((-(ref) - 6) / 30.0 * hl)
        if y <= r < y + hl:
            img[r, 2:w - 2] = (60, 60, 80)
            text(img, 4, r - 8, '%d' % ref, (120, 120, 140))
    for i, v in enumerate(lt):
        r = y + int(np.clip((-(v) - 6) / 30.0, 0, 0.999) * hl)
        img[r:r + 2, 2 + i] = (255, 200, 90)
    y += hl + 4
    kk = int(0.05 * st['sr'])
    seg = np.concatenate([mono[-kk:], mono[:kk]])
    draw_wave(img, 2, y, w - 4, hz_, seg / max(np.max(np.abs(seg)), 1e-6), (150, 190, 255))
    img[y:y + hz_, 2 + (w - 4) // 2] = (255, 90, 90)
    text(img, 6, y + 3, 'LOOP SEAM +/-50MS', (255, 255, 255))
    return img


def fmt_row(st):
    return '%-22s %6.2fs %-4s pk %6.2f tp %6.2f rms %6.1f L %6.1f hf %4.1f%% lo %4.1f%% %s' % (
        st['name'], st['dur'], 'loop' if st['loop'] else '', st['peak_db'], st['tp_db'], st['rms_db'],
        st['lufs'], st['hf'], st['lo'], ('seam %.2f' % st['seam']) if st['seam'] is not None else
        ('ends %.4f/%.4f' % (st['start'], st['end'])))


def run_sfx(names=None, per_sheet=15, tag='sfx'):
    os.makedirs(PREV, exist_ok=True)
    d = os.path.join(ROOT, 'assets', 'audio', 'sfx')
    files = sorted(f for f in os.listdir(d) if f.endswith('.wav'))
    if names:
        files = [f for f in files if f[:-4] in names]
    stats, panels = [], []
    for f in files:
        st, a = analyze(os.path.join(d, f))
        stats.append(st)
        panels.append(panel(st, a))
        print(fmt_row(st))
    for i in range(0, len(panels), per_sheet):
        img = sheet(panels[i:i + per_sheet], 3, 'RUNEWIRE SFX %d' % (i // per_sheet + 1))
        save_png(os.path.join(PREV, '%s_%d.png' % (tag, i // per_sheet + 1)), img)
    return stats


def run_music(names=None):
    os.makedirs(PREV, exist_ok=True)
    d = os.path.join(ROOT, 'assets', 'audio', 'music')
    stats = []
    for f in sorted(os.listdir(d)):
        if not f.endswith('.wav') or (names and f[:-4] not in names):
            continue
        st, a = analyze(os.path.join(d, f))
        stats.append(st)
        print(fmt_row(st))
        save_png(os.path.join(PREV, st['name'] + '.png'), music_sheet(st, a))
    return stats


def manifest(path=os.path.join(ROOT, 'art', 'audio', 'SOUNDS.md')):
    """Write a markdown table of every generated file (stats measured from the WAVs)."""
    import make_sfx
    import make_music
    rows = ['# RuneWire audio manifest', '',
            'Generated by `art/audio/qa.py -- manifest` from the WAVs on disk. Peak and RMS are dBFS; '
            'L is max 200 ms loudness (one-shots) or integrated loudness (loops), in LUFS.', '',
            '| File | Group | Length | Loops | Peak | RMS | L | Description |',
            '|---|---|---|---|---|---|---|---|']
    d = os.path.join(ROOT, 'assets', 'audio', 'sfx')
    for name, e in make_sfx.REG.items():
        st, _ = analyze(os.path.join(d, name + '.wav'))
        rows.append('| `sfx/%s.wav` | %s | %.2f s | %s | %.1f | %.1f | %.1f | %s |' % (
            name, e['group'], st['dur'], 'yes' if st['loop'] else 'no', st['peak_db'], st['rms_db'],
            st['lufs'], e['desc']))
    d = os.path.join(ROOT, 'assets', 'audio', 'music')
    for name in ('music_town', 'music_combat', 'music_menu'):
        st, _ = analyze(os.path.join(d, name + '.wav'))
        rows.append('| `music/%s.wav` | music | %.2f s | %s | %.1f | %.1f | %.1f | %s |' % (
            name, st['dur'], 'yes' if st['loop'] else 'no', st['peak_db'], st['rms_db'], st['lufs'],
            make_music.DESC[name]))
    with open(path, 'w') as fh:
        fh.write('\n'.join(rows) + '\n')
    print('wrote', path)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if not argv or 'sfx' in argv:
        run_sfx()
    if not argv or 'music' in argv:
        run_music()
    if not argv or 'manifest' in argv:
        manifest()
