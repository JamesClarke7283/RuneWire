"""RuneWire music engine: a tiny circular sequencer, note/chord parsing, voicing,
note caching, mixdown with a shared convolution reverb, and mastering.

Everything is rendered into one circular stereo buffer whose length is exactly
the loop, so note tails, echoes and the reverb wrap around the loop point and
the file loops seamlessly.
"""
import itertools
import math
import zlib

import numpy as np

import synth as S
import instruments as I
from synth import ns

QUAL = {
    '': (0, 4, 7), 'm': (0, 3, 7), '7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11), 'm7': (0, 3, 7, 10),
    'sus4': (0, 5, 7), 'sus2': (0, 2, 7), '7sus4': (0, 5, 7, 10), 'add9': (0, 4, 7, 14),
    'madd9': (0, 3, 7, 14), 'dim': (0, 3, 6), 'aug': (0, 4, 8), '6': (0, 4, 7, 9), 'm6': (0, 3, 7, 9),
    'maj9': (0, 4, 7, 11, 14), 'm9': (0, 3, 7, 10, 14), '5': (0, 7),
}
_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def pc(name):
    return (_PC[name[0]] + name[1:].count('#') - name[1:].count('b')) % 12


class Chord:
    def __init__(self, sym):
        self.sym = sym
        s = sym
        bass = None
        if '/' in s:
            s, b = s.split('/')
            bass = pc(b)
        i = 2 if len(s) > 1 and s[1] in '#b' else 1
        self.root = pc(s[:i])
        self.ivs = QUAL[s[i:]]
        self.bass = self.root if bass is None else bass
        self.pcs = [(self.root + iv) % 12 for iv in self.ivs]

    def tone(self, degree, near):
        """MIDI note of chord tone index `degree` (0 root, 1 third, 2 fifth, 3 seventh...)
        closest to midi `near`."""
        p = self.pcs[degree % len(self.pcs)]
        return near + ((p - near + 6) % 12) - 6

    def bass_note(self, lo=38, hi=50):
        m = lo + ((self.bass - lo) % 12)
        return m if m <= hi else m - 12

    def fifth_note(self, lo=38, hi=52):
        p = (self.root + 7) % 12
        m = lo + ((p - lo) % 12)
        return m if m <= hi else m - 12


def voice(ch, lo=55, hi=76, prev=None, center=65, drop_root=False):
    """Close voicing of a chord's pitch classes in [lo, hi], led smoothly from prev."""
    pcs = list(dict.fromkeys(ch.pcs))
    if drop_root and len(pcs) >= 4:
        pcs = pcs[1:]
    opts = [[m for m in range(lo, hi + 1) if m % 12 == p] for p in pcs]
    best = None
    for combo in itertools.product(*opts):
        c = sorted(combo)
        if c[-1] - c[0] > 14:
            continue
        if prev:
            cost = sum(min(abs(a - b) for b in prev) for a in c) + 0.15 * abs(np.mean(c) - center)
        else:
            cost = abs(np.mean(c) - center)
        if best is None or cost < best[0]:
            best = (cost, c)
    return best[1]


def _num(d):
    if '/' in d:
        a, b = d.split('/')
        return float(a) / float(b)
    return float(d)


def parse(text, bpb=4, transpose=0, check=True):
    """'D5:1 G5:.5_ A5:.5 | r:2 E5:2' -> [(beat, dur, midi, slur, accent)], total beats.
    '_' after the duration slurs into the next note, '!' after the pitch accents it.
    Every bar (between '|') must add up to bpb beats."""
    notes = []
    b = 0.0
    for bi, bar in enumerate(text.split('|')):
        toks = bar.split()
        if not toks:
            continue
        start = b
        for tok in toks:
            p, d = tok.split(':')
            slur = d.endswith('_')
            d = d.rstrip('_')
            acc = p.endswith('!')
            p = p.rstrip('!')
            dur = _num(d)
            if p != 'r':
                notes.append((b, dur, int(S.midi(p)) + transpose, slur, acc))
            b += dur
        if check and abs((b - start) - bpb) > 1e-6:
            raise ValueError('bar %d has %.3f beats: %s' % (bi, b - start, bar.strip()))
    return notes, b


class Song:
    def __init__(self, name, bpm, bars, bpb=4, swing=0.5, seed=1):
        self.name = name
        self.bpm = bpm
        self.bars = bars
        self.bpb = bpb
        self.spb = 60.0 / bpm
        self.N = ns(bars * bpb * self.spb)
        self.swing = swing
        self.mix = np.zeros((2, self.N))
        self.send = np.zeros(self.N)
        self.sends = {}
        self.energy = {}
        self.rng = np.random.default_rng(seed)
        self._cache = {}

    # --- time ---------------------------------------------------------------
    def bt(self, beat):
        """Absolute beat -> seconds, with 8th-note swing."""
        whole = math.floor(beat + 1e-9)
        frac = beat - whole
        if self.swing != 0.5:
            if frac < 0.5:
                frac = frac / 0.5 * self.swing
            else:
                frac = self.swing + (frac - 0.5) / 0.5 * (1.0 - self.swing)
        return (whole + frac) * self.spb

    def dur(self, beat, beats):
        return self.bt(beat + beats) - self.bt(beat)

    def bar(self, b):
        return b * self.bpb

    # --- notes --------------------------------------------------------------
    def cached(self, key, fn):
        if key not in self._cache:
            S.seed(zlib.crc32(repr(key).encode()))
            self._cache[key] = fn()
        return self._cache[key]

    def add(self, inst, x, beat=None, t=None, pan=0.0, gain=1.0, jitter=0.004, vary=0.06):
        """Place a note/event. jitter (s) and vary (relative gain) humanise repeats."""
        if t is None:
            t = self.bt(beat)
        if jitter:
            t += self.rng.uniform(-jitter, jitter)
        if vary:
            gain *= 1.0 + vary * self.rng.uniform(-1.0, 1.0)
        st = S.fade(x if x.ndim == 2 else S.pan(x, pan), 0.0, 0.004) * gain
        S.place(self.mix, st, t, circular=True)
        s = self.sends.get(inst, 0.0)
        if s:
            S.place(self.send, st.mean(axis=0) * s, t, circular=True)
        self.energy[inst] = self.energy.get(inst, 0.0) + float(np.sum(st * st))

    def line(self, inst, notes, bar0, render, pan=0.0, gain=1.0, art=0.9, vel=0.8, acc=1.0,
             gap=0.49, **kw):
        """Render parsed notes as legato phrases with a mono_line style renderer.
        Phrases split at rests >= gap beats. render(list_of(t0,dur,freq,vel)) -> (sig, t_first)."""
        base = self.bar(bar0)
        phrases, cur = [], []
        for i, (b, d, m, slur, accent) in enumerate(notes):
            if cur:
                pb, pd = cur[-1][0], cur[-1][1]
                if b - (pb + pd) >= gap:
                    phrases.append(cur)
                    cur = []
            cur.append((b, d, m, slur, accent))
        if cur:
            phrases.append(cur)
        for ph in phrases:
            ev = []
            for i, (b, d, m, slur, accent) in enumerate(ph):
                t0 = self.bt(base + b)
                nxt = ph[i + 1] if i + 1 < len(ph) else None
                full = self.dur(base + b, d)
                touching = nxt is not None and abs(nxt[0] - (b + d)) < 1e-6
                sd = full if (slur and touching) else full * art
                ev.append((t0, sd, float(S.mtof(m)), acc if accent else vel))
            sig, t_first = render(ev)
            self.add(inst, sig, t=t_first, pan=pan, gain=gain, jitter=0, vary=0)


def mixdown(song, ir, wet=1.0):
    """Mix plus the shared reverb (circular convolution of the mono send with a stereo IR)."""
    rev = S.convolve(song.send, ir, circular=True) * wet
    return song.mix + rev


def master(mix, target_lufs, ceiling=-1.0, lowcut=30.0):
    mix = S.filt(mix, lambda f: S.H_hp(f, lowcut, 2), circular=True)
    mix = mix - mix.mean(axis=1, keepdims=True)
    for _ in range(3):
        L = S.loudness_int(mix, circular=True)
        mix = mix * S.db2a(target_lufs - L)
        mix = S.limit(mix, ceiling, attack=0.003, release=0.2, circular=True)
    return mix


def report_energy(song):
    tot = sum(song.energy.values()) + 1e-12
    for k, v in sorted(song.energy.items(), key=lambda kv: -kv[1]):
        print('   %-12s %5.1f%%  %6.1f dB' % (k, 100 * v / tot, 10 * math.log10(v / tot + 1e-12)))
