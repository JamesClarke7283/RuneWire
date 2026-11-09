"""Compose and render RuneWire's three music loops into assets/audio/music/.

    cd <project root>
    env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/make_music.py
    # one track only:  ... make_music.py -- town      (town | combat | menu, add --nopreview)

16-bit 44.1 kHz stereo WAVs with a 'smpl' loop chunk spanning the whole file.
Every note, echo and reverb tail is rendered into a circular buffer exactly one
loop long, so the end flows straight back into the start.

  music_town   G major, 112 BPM, light swing, 32 bars (68.6 s): pizzicato
               oom-pah, flute tune, clarinet counter-line, harp, glockenspiel,
               soft string pad, shaker/woodblock/tambourine.
  music_combat D minor, 150 BPM, 48 bars (76.8 s): synth bass and spiccato
               string ostinato, brass stabs, horn-section melody, kit + taiko,
               a square-wave "clockwork" arpeggio breakdown with snare-roll build.
  music_menu   D Lydian, 72 BPM, 24 bars (80 s): glassy pad, celesta and harp
               arpeggios, soft flute melody, sub bass, twinkles, big reverb.
"""
import math
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import synth as S  # noqa: E402
import instruments as I  # noqa: E402
import music as M  # noqa: E402
from synth import ns  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'music')


def f_(m):
    return float(S.mtof(m))


def chord_map(song, syms):
    """Per-bar chord symbols (a bar may hold 'Am7 D7' = two half-bar chords) ->
    list of (start_beat, beats, Chord)."""
    out = []
    for b, s in enumerate(syms):
        parts = s.split()
        span = song.bpb / len(parts)
        for i, p in enumerate(parts):
            out.append((song.bar(b) + i * span, span, M.Chord(p)))
    return out


def low_note(p, lo, hi):
    m = lo + ((p - lo) % 12)
    return m if m <= hi else m - 12


def chord_at(cm, beat):
    for b0, d, ch in cm:
        if b0 <= beat < b0 + d:
            return ch
    return cm[-1][2]


# ---------------------------------------------------------------------------
# cached note renderers
# ---------------------------------------------------------------------------

def pluck(song, kind, m, dur, vel, var=0):
    key = ('pluck', kind, int(m), round(dur, 2), round(vel, 2), var % 3)
    return song.cached(key, lambda: I.pluck(f_(m), dur, kind, vel))


def bell(song, kind, m, dur, vel, t60):
    key = ('bell', kind, int(m), round(dur, 2), round(vel, 2), t60)
    return song.cached(key, lambda: I.bell(f_(m), dur, kind, t60=t60, vel=vel))


def flute_line(ev):
    return I.mono_line(ev, I.FLUTE, vib_depth=0.0065, vib_delay=0.22, attack=0.05, breath=0.045, chiff=0.14)


def soft_flute_line(ev):
    sig, t0 = I.mono_line(ev, I.FLUTE, vib_depth=0.005, vib_delay=0.3, attack=0.09, release=0.25,
                          breath=0.06, chiff=0.06, bright_vel=0.8)
    return S.lp(sig, 5000), t0


def clarinet_line(ev):
    sig, t0 = I.mono_line(ev, I.CLARINET, vib_depth=0.0015, attack=0.04, breath=0.015, chiff=0.05, trem=0.0)
    return S.lp(sig, 3800), t0


def horn_line(detune=0.0):
    def r(ev):
        sig, t0 = I.mono_line(ev, brass=6.5, vib_depth=0.0045, vib_delay=0.25, attack=0.045, release=0.12,
                              breath=0.008, chiff=0.0, trem=0.15, glide=0.03, detune=detune)
        return S.lp(sig, 7000), t0
    return r


def pad_chord(song, notes, dur, kind='warm', attack=0.5, release=1.0, bright=3.0, rate=0.5, mix=0.55):
    key = ('pad', kind, tuple(notes), round(dur, 2), attack, release, bright)

    def mk():
        x = sum(I.pad(f_(m), dur, kind, attack=attack, release=release, bright=bright) for m in notes)
        return S.chorus(x, 3, base_ms=14, depth_ms=3, rate=rate, mix=mix, stereo=True)
    return song.cached(key, mk)


# ---------------------------------------------------------------------------
# music_town
# ---------------------------------------------------------------------------

TOWN_CHORDS = [
    'G', 'G/B', 'C', 'D7', 'G', 'Em', 'Am7 D7', 'G',          # A
    'G', 'G/B', 'C', 'Cm', 'G/D', 'E7', 'Am7 D7', 'G',        # A'
    'Em', 'C', 'G', 'D', 'Em', 'C', 'A7', 'D7',               # B
    'G', 'G/B', 'C', 'Cm', 'G/D', 'E7', 'Am7', 'D7',          # A''  (D7 turns back to the top)
]

TOWN_TUNE = """
r:1 D5:.5 G5:.5 B5:1 A5:.5_ G5:.5 | A5:1.5 B5:.5 G5:1 D5:1 | E5:.5 G5:.5 C6:1 B5:.5_ A5:.5 G5:1 |
A5:2 F#5:1 r:1 | r:1 D5:.5 G5:.5 B5:1 D6:1 | E6:1.5 D6:.5 B5:1 G5:1 |
C6:.5_ B5:.5 A5:.5_ G5:.5 F#5:1 A5:1 | G5:3 r:1 |
r:1 D5:.5 G5:.5 B5:1 A5:.5_ G5:.5 | A5:1.5 B5:.5 G5:1 E5:.5_ F#5:.5 | G5:.5 E5:.5 C6:1 B5:.5_ A5:.5 G5:.5 E5:.5 |
Eb5:2 G5:1 F5:1 | D5:1 G5:.5 B5:.5 D6:1 B5:1 | G#5:1.5 B5:.5 E6:1 D6:1 |
C6:1 A5:1 D6:.5_ C6:.5 A5:1 | B5:1 G5:.5_ A5:.5 G5:2 |
B5:1.5 E6:.5 E6:1 D6:.5_ B5:.5 | C6:2 G5:1 E5:1 | D6:1.5 B5:.5 G5:1 B5:1 | A5:2 F#5:1 A5:1 |
B5:1.5 E6:.5 G6:1 F#6:.5_ E6:.5 | E6:2 D6:1 C6:1 | C#6:1 E6:1 A5:1 G5:1 | F#5:1 A5:1 C6:1 D6:.5_ C6:.5 |
r:1 D5:.5 G5:.5 B5:1 A5:.5_ G5:.5 | A5:1.5 B5:.5 G5:1 D5:1 | E5:.5 G5:.5 C6:1 B5:.5_ A5:.5 G5:1 |
Eb5:2 G5:1 F5:1 | D5:1 G5:.5 B5:.5 D6:1 B5:1 | G#5:1.5 B5:.5 E6:1 D6:1 |
C6:1 B5:.5_ A5:.5 E5:1 G5:1 | A5:2 F#5:1 r:1
"""

TOWN_CLARINET_A2 = """
B3:2 D4:2 | D4:2 B3:1 C4:1 | C4:2 E4:2 | Eb4:2 C4:2 | B3:2 D4:1 G4:1 | G#4:2 E4:1 D4:1 |
E4:2 F#4:1 C4:1 | B3:2 r:2
"""
TOWN_CLARINET_B = """
G4:2 B4:2 | E4:2 G4:2 | D4:2 G4:1 B4:1 | F#4:2 D4:2 | G4:2 B4:2 | G4:2 E4:2 | E4:2 C#4:1 A3:1 |
A3:1 C4:1 D4:1 F#4:1
"""
TOWN_CLARINET_A3 = """
B3:2 D4:2 | D4:2 B3:1 C4:1 | C4:2 E4:2 | Eb4:2 C4:2 | B3:2 D4:1 G4:1 | G#4:2 E4:1 D4:1 |
E4:2 C4:2 | C4:2 A3:1 F#3:1
"""


def make_town():
    song = M.Song('music_town', 112, 32, swing=0.56, seed=11)
    song.sends = dict(flute=0.22, clarinet=0.22, glock=0.3, harp=0.3, pizz=0.18, bass=0.04, pad=0.3,
                      shaker=0.08, wood=0.15, tamb=0.12, kick=0.03, triangle=0.3)
    cm = chord_map(song, TOWN_CHORDS)
    beat_s = song.spb

    # --- melody ---------------------------------------------------------------
    tune, total = M.parse(TOWN_TUNE)
    assert abs(total - 128) < 1e-6
    song.line('flute', tune, 0, flute_line, pan=0.08, gain=0.5, art=0.88, vel=0.82, acc=0.95)
    for txt, b0 in ((TOWN_CLARINET_A2, 8), (TOWN_CLARINET_B, 16), (TOWN_CLARINET_A3, 24)):
        notes, _ = M.parse(txt)
        song.line('clarinet', notes, b0, clarinet_line, pan=-0.3, gain=0.3, art=0.92, vel=0.75)
    # glockenspiel: doubles the tune an octave up in A'', and taps the B section downbeats
    for b, d, m, slur, acc in tune:
        bar = int(b // 4)
        if bar >= 24 or (16 <= bar < 24 and abs(b % 4) < 1e-6):
            song.add('glock', bell(song, 'glock', m + 12, 1.2, 0.7, 1.0), b, pan=0.4, gain=0.8)

    # --- bass and pizzicato oom-pah -------------------------------------------
    prev = None
    for i, (b0, d, ch) in enumerate(cm):
        bar = int(b0 // 4)
        vo = M.voice(ch, 55, 71, prev, center=62)
        prev = vo
        bn = ch.bass_note(40, 51)
        second = ch.fifth_note(38, 50) if ch.bass == ch.root else low_note(ch.root, 40, 51)
        steps = [(0, bn)] if d <= 2 else [(0, bn), (2, second)]
        for off, m in steps:
            song.add('bass', pluck(song, 'bass', m, min(2.0, 2 * beat_s) + 0.1, 0.95, i), b0 + off, gain=1.5)
        for off in ((1,) if d <= 2 else (1, 3)):
            for j, m in enumerate(vo):
                song.add('pizz', pluck(song, 'pizz', m, 0.6, 0.72, i + j), b0 + off + 0.012 * j / beat_s,
                         pan=-0.35, gain=1.9)
        if d > 2 and bar >= 8 and bar % 2 == 1:
            for j, m in enumerate(vo):
                song.add('pizz', pluck(song, 'pizz', m, 0.5, 0.5, i + j + 1), b0 + 3.5, pan=-0.35, gain=1.9)

    # --- harp arpeggios (A' and A'') and B-section rolled chords --------------
    for b0, d, ch in cm:
        bar = int(b0 // 4)
        arp = [m for m in range(55, 84) if m % 12 in ch.pcs]
        if 8 <= bar < 16 or bar >= 24:
            pat = [0, 1, 2, 3, 4, 5, 4, 3]
            for k in range(int(d * 2)):
                m = arp[min(pat[k % 8], len(arp) - 1)]
                song.add('harp', pluck(song, 'harp', m, 1.4, 0.55 + (0.15 if k % 2 == 0 else 0), k),
                         b0 + 0.5 * k, pan=0.35, gain=1.1)
        elif 16 <= bar < 24 and d >= 2:
            for j, m in enumerate(arp[1:6]):
                song.add('harp', pluck(song, 'harp', m, 1.8, 0.6, j), b0, t=song.bt(b0) + 0.035 * j,
                         pan=0.35, gain=1.1)

    # --- soft string pad --------------------------------------------------------
    prev = None
    for b0, d, ch in cm:
        bar = int(b0 // 4)
        vo = M.voice(ch, 52, 69, prev, center=60)
        prev = vo
        lvl = 0.34 if 16 <= bar < 24 else 0.13 if bar < 4 else 0.21
        song.add('pad', pad_chord(song, vo, song.dur(b0, d), 'warm', attack=0.45, release=0.9, bright=3.0),
                 b0, gain=lvl)

    # --- percussion -------------------------------------------------------------
    kick = song.cached('kick', lambda: I.kick(1.0, 115, 50, 0.025, 0.3, 0.12, 1.2))
    shk = [song.cached(('shk', v), lambda: I.shaker(1.0, 0.07)) for v in range(3)]
    wb_hi = song.cached('wbh', lambda: I.woodblock(1250, 1.0))
    wb_lo = song.cached('wbl', lambda: I.woodblock(880, 1.0))
    tmb = [song.cached(('tmb', v), lambda: I.tamb(1.0)) for v in range(2)]
    tri = song.cached('tri', lambda: I.triangle_inst(1.0, 1250, 2.5))
    for bar in range(32):
        b0 = song.bar(bar)
        sec = bar // 8
        kp = (0, 2) if sec != 2 else (0, 1.5, 2)
        for k in kp:
            song.add('kick', kick, b0 + k, gain=0.84 * (1.0 if k == 0 else 0.8))
        if sec == 1 or sec == 3:
            if bar % 2 == 1:
                song.add('kick', kick, b0 + 2.5, gain=0.55)
        for k in range(8):
            v = 0.75 if k % 2 else 0.45
            song.add('shaker', shk[k % 3], b0 + 0.5 * k, pan=0.5,
                     gain=0.65 * v * (0.5 if bar < 4 else 0.75 if sec == 0 else 1.0))
        if sec >= 2:
            for k in (1, 3):
                song.add('wood', wb_hi if k == 1 else wb_lo, b0 + k, pan=-0.45, gain=0.8)
        if sec in (1, 3):
            song.add('tamb', tmb[bar % 2], b0 + 3, pan=0.3, gain=0.85)
        if bar % 8 == 0:
            song.add('triangle', tri, b0, pan=0.6, gain=0.42)
    # woodblock pickup fill into the loop point and into B
    for bar in (15, 31):
        b0 = song.bar(bar)
        for k in range(6):
            song.add('wood', wb_hi if k % 2 == 0 else wb_lo, b0 + 2.5 + 0.25 * k, pan=-0.45, gain=0.6 + 0.1 * k)
    return song, 'hall'


# ---------------------------------------------------------------------------
# music_combat
# ---------------------------------------------------------------------------

COMBAT_CHORDS = [
    'Dm', 'Dm', 'Bb', 'C', 'Dm', 'Dm', 'Gm', 'A',     # riff
    'Dm', 'Dm', 'Bb', 'C', 'Dm', 'Dm', 'Gm', 'A',     # theme
    'Bb', 'C', 'Dm', 'Dm', 'Bb', 'C', 'A', 'A',       # B
    'Dm', 'Bb', 'Gm', 'A', 'Dm', 'Bb', 'Gm', 'A',     # breakdown (clockwork arp, snare-roll build)
    'Dm', 'Dm', 'Bb', 'C', 'Dm', 'Dm', 'Gm', 'A',     # theme again with descant
    'Bb', 'C', 'Dm', 'Bb', 'Gm', 'A', 'Bb', 'A7',     # turnaround back to the riff
]

COMBAT_THEME = """
D5:1.5 A4:.5 D5:1 E5:1 | F5:1.5 E5:.5 D5:1 A4:1 | Bb4:1.5 C5:.5 D5:1 F5:1 | E5:3 C5:1 |
D5:1.5 A4:.5 D5:1 E5:1 | F5:1.5 G5:.5 A5:2 | Bb5:1.5 A5:.5 G5:1 F5:1 | E5:2 C#5:1 A4:1
"""
COMBAT_B = """
F5:1 Bb5:1 A5:1 F5:1 | G5:1.5 E5:.5 C5:2 | D5:.5_ E5:.5_ F5:.5_ G5:.5 A5:2 | D6:2 A5:2 |
Bb5:1.5 A5:.5 G5:1 F5:1 | G5:1.5 A5:.5 E5:2 | C#5:1 E5:1 A5:1 G5:1 | A5:3 r:1
"""
COMBAT_THEME2 = """
D5:1.5 A4:.5 D5:1 E5:1 | F5:1.5 E5:.5 D5:1 A4:1 | Bb4:1.5 C5:.5 D5:1 F5:1 | E5:3 C5:1 |
D5:1.5 A4:.5 D5:1 E5:1 | F5:1.5 G5:.5 A5:1 D6:1 | D6:1.5 C6:.5 Bb5:1 G5:1 | A5:2 E5:1 C#5:1
"""
COMBAT_OUTRO = """
F5:1 Bb5:1 A5:1 F5:1 | G5:1.5 E5:.5 C5:2 | D5:.5_ E5:.5_ F5:.5_ G5:.5 A5:2 | Bb5:2 D6:2 |
D6:1.5 C6:.5 Bb5:1 G5:1 | A5:2 E5:2 | F5:2 D5:2 | E5:2 C#5:1 r:1
"""
COMBAT_DESCANT = "A5:4 | F5:4 | D5:4 | E5:4 | F5:4 | A5:4 | G5:4 | E5:4"


def make_combat():
    song = M.Song('music_combat', 150, 48, seed=22)
    song.sends = dict(horn=0.2, strings=0.12, descant=0.25, bass=0.0, stabs=0.18, kick=0.02, snare=0.14,
                      hats=0.05, taiko=0.2, toms=0.15, crash=0.15, arp=0.25, pad=0.25)
    cm = chord_map(song, COMBAT_CHORDS)
    sec_of = lambda bar: bar // 8

    # --- horn-section melody (unison + octave below) ---------------------------
    for txt, b0 in ((COMBAT_THEME, 8), (COMBAT_B, 16), (COMBAT_THEME2, 32), (COMBAT_OUTRO, 40)):
        notes, _ = M.parse(txt)
        song.line('horn', notes, b0, horn_line(0.0), pan=0.12, gain=0.42, art=0.9, vel=0.9)
        song.line('horn', notes, b0, horn_line(7.0), pan=-0.12, gain=0.25, art=0.9, vel=0.85)
        low = [(b, d, m - 12, s, a) for (b, d, m, s, a) in notes]
        song.line('horn', low, b0, horn_line(-5.0), pan=0.0, gain=0.22, art=0.9, vel=0.8)
    notes, _ = M.parse(COMBAT_DESCANT)

    def descant(ev):
        t_first = ev[0][0]
        parts = [(t0 - t_first, I.strings(fr, d, v, voices=4, detune=10, attack=0.25, release=0.5, bright=5.0,
                                          sus=0.85, decay_t=0.5)) for (t0, d, fr, v) in ev]
        out = np.zeros(max(ns(off) + len(x) for off, x in parts))
        for off, x in parts:
            S.place(out, x, off)
        return out, t_first
    song.line('descant', notes, 32, descant, pan=-0.25, gain=0.7, art=0.97, vel=0.8)

    # --- bass, string ostinato, stabs, pad ---------------------------------------
    pat16 = [0, 0, 2, 0, 1, 0, 2, 0, 0, 0, 2, 0, 3, 2, 1, 2]
    prev = None
    for i, (b0, d, ch) in enumerate(cm):
        bar = int(b0 // 4)
        sec = sec_of(bar)
        root = ch.bass_note(36, 47)
        # bass
        if sec == 3 and bar < 30:
            song.add('bass', song.cached(('sb_long', root), lambda: I.synth_bass(f_(root), 4 * song.spb - 0.05,
                                                                                    0.6, bright=2.0)),
                     b0, gain=0.375)
        else:
            nxt = cm[(i + 1) % len(cm)][2]
            nroot = nxt.bass_note(36, 47)
            scale = [2, 4, 5, 7, 9, 10, 0] if nxt.root != 2 else [2, 4, 5, 7, 9, 10, 1]  # C# leads to D
            appr = max(m for m in range(nroot - 4, nroot) if m % 12 in scale)
            bpat = [root, root, root + 12, root, root, root + 12, root, appr if bar % 2 else root + 7]
            for k, m in enumerate(bpat):
                v = 1.0 if k in (0, 3, 6) else 0.75
                x = song.cached(('sb', m, v), lambda: I.synth_bass(f_(m), 0.5 * song.spb * 0.85, v))
                song.add('bass', x, b0 + 0.5 * k, gain=0.375)
        # spiccato strings
        tones = sorted(set(ch.tone(k, 62) for k in range(3)))
        tones = [tones[0], tones[1], tones[2], tones[0] + 12]
        if sec != 3:
            for k in range(16):
                m = tones[pat16[k]]
                v = 1.0 if k % 4 == 0 else 0.62
                x = song.cached(('stc', m, v), lambda: I.strings(f_(m), 0.075, v, voices=3, detune=9))
                song.add('strings', x, b0 + 0.25 * k, pan=-0.3, gain=0.75)
        # brass stabs
        vo = M.voice(ch, 57, 72, prev, center=64)
        prev = vo
        if sec in (0, 2, 5):
            for off, ln, v in ((0, 0.45, 1.0), (1.5, 0.4, 0.8), (3.0, 0.6, 0.9)):
                for m in vo:
                    x = song.cached(('stab', m, ln, v), lambda: I.brass(f_(m), ln * song.spb, v, voices=2,
                                                                        bright=6.0, attack=0.02, release=0.1))
                    song.add('stabs', x, b0 + off, pan=0.25, gain=0.39)
        elif sec in (1, 4):
            for m in vo:
                x = song.cached(('stab', m, 0.45, 0.8), lambda: I.brass(f_(m), 0.45 * song.spb, 0.8, voices=2,
                                                                        bright=6.0, attack=0.02, release=0.1))
                song.add('stabs', x, b0, pan=0.25, gain=0.35)
        # pad
        if sec in (2, 3, 4):
            pv = M.voice(ch, 50, 67, None, center=58)
            song.add('pad', pad_chord(song, pv, song.dur(b0, d), 'warm', attack=0.3, release=0.6, bright=2.5),
                     b0, gain=0.27)

    # --- clockwork square arpeggio (breakdown) -----------------------------------
    apat = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 4, 3, 2, 1]
    for bar in range(24, 32):
        b0 = song.bar(bar)
        ch = chord_at(cm, b0)
        arp = [m for m in range(74, 92) if m % 12 in ch.pcs]
        for k in range(16):
            m = arp[min(apat[k], len(arp) - 1)]
            v = 1.0 if k % 4 == 0 else 0.7

            def mk(m=m, v=v):
                n = ns(0.12)
                env = S.adsr(n, 0.002, 0.05, 0.35, 0.04, gate=0.07)
                return S.harm(f_(m), n, bright=2.5 + 2.5 * v, kind='square', even=0.25) * env * v
            x = song.cached(('arp', m, v), mk)
            song.add('arp', x, b0 + 0.25 * k, pan=0.35, gain=0.9)
            song.add('arp', x, b0 + 0.25 * k + 0.75, pan=-0.45, gain=0.34)

    # --- drums -------------------------------------------------------------------
    kick = song.cached('kick', lambda: I.kick(1.0, 150, 46, 0.03, 0.42, 0.3, 1.6))
    snr = [song.cached(('snr', v), lambda: I.snare(1.0)) for v in range(3)]
    hh = [song.cached(('hh', v), lambda: I.hat(1.0)) for v in range(3)]
    ohh = song.cached('ohh', lambda: I.hat(1.0, open_=True))
    tk_lo = song.cached('tkl', lambda: I.taiko(58, 1.0, 1.0))
    tk_hi = song.cached('tkh', lambda: I.taiko(82, 1.0, 0.7))
    toms = [song.cached(('tom', f), lambda: I.tom(f, 1.0, 0.45)) for f in (196, 147, 110)]
    crash = song.cached('crash', lambda: I.crash(1.0, 2.4))
    for bar in range(48):
        b0 = song.bar(bar)
        sec = sec_of(bar)
        if sec != 3:
            for k in (0, 0.75, 2, 2.5):
                song.add('kick', kick, b0 + k, gain=0.64 * (1.0 if k in (0, 2) else 0.75))
            for k in (1, 3):
                song.add('snare', snr[(bar + k) % 3], b0 + k, pan=0.05, gain=1.0)
            for k in range(8):
                if k == 7 and bar % 2 == 1:
                    song.add('hats', ohh, b0 + 3.5, pan=0.35, gain=0.95)
                else:
                    song.add('hats', hh[k % 3], b0 + 0.5 * k, pan=0.35, gain=1.25 * (1.0 if k % 2 else 0.6))
            if bar % 2 == 0:
                song.add('taiko', tk_lo, b0, pan=-0.1, gain=0.54)
        else:
            song.add('kick', kick, b0, gain=0.58)
            for k, lo in ((0, True), (1.5, False), (2, True), (3, False), (3.5, False)):
                song.add('taiko', tk_lo if lo else tk_hi, b0 + k, pan=-0.15 if lo else 0.15, gain=0.51)
            for k in range(4):
                song.add('hats', hh[k % 3], b0 + k + 0.5, pan=0.35, gain=0.5)
        # tom fills at the ends of sections
        if bar in (7, 15, 23, 39, 47):
            for k, ti in enumerate((0, 0, 1, 1, 2, 2, 1, 2)):
                song.add('toms', toms[ti], b0 + 2 + 0.25 * k, pan=(-0.3, 0.0, 0.3)[ti], gain=0.53 + 0.05 * k)
        if bar in (0, 8, 16, 32, 40):
            song.add('crash', crash, b0, pan=-0.3, gain=0.85)
    # snare-roll build out of the breakdown
    for k in range(16):
        song.add('snare', snr[k % 3], song.bar(30) + 0.25 * k, pan=0.05, gain=0.25 + 0.38 * k / 16)
    for k in range(32):
        song.add('snare', snr[k % 3], song.bar(31) + 0.125 * k, pan=0.05, gain=0.5 + 0.45 * k / 32)
    return song, 'combat'


# ---------------------------------------------------------------------------
# music_menu
# ---------------------------------------------------------------------------

MENU_CHORDS = [
    'Dmaj7', 'E/D', 'Bm7', 'Gmaj7', 'D/F#', 'Em7', 'Gmaj7', 'A7sus4',
    'Dmaj7', 'E/D', 'Bm7', 'Gmaj7', 'Bm7', 'F#m7', 'Gmaj7', 'A7sus4 A7',
    'Gmaj7', 'A/G', 'F#m7', 'Bm7', 'Em7', 'Gmaj7', 'Gmaj7', 'Asus4',
]
MENU_B = """
F#5:2 A5:1 E5:1 | G#5:3 F#5:1 | D5:1.5 E5:.5 F#5:2 | B4:3 r:1 |
F#5:2 A5:1 B5:1 | C#6:2 A5:1 F#5:1 | D6:1.5 C#6:.5 B5:1 A5:1 | G5:2 E5:1 C#5:1
"""
MENU_C = """
B5:1 D6:1 F#6:2 | E6:1.5 C#6:.5 A5:2 | C#6:2 E6:1 C#6:1 | D6:3 r:1 |
B5:1 G5:1 E5:1 F#5:1 | G5:1.5 A5:.5 B5:2 | F#5:2 D5:2 | E5:4
"""


def make_menu():
    song = M.Song('music_menu', 72, 24, seed=33)
    song.sends = dict(pad=0.45, celesta=0.45, harp=0.4, flute=0.4, sub=0.0, twinkle=0.6, triangle=0.5,
                      shimmer=0.5)
    cm = chord_map(song, MENU_CHORDS)

    # glassy pad throughout
    prev = None
    for b0, d, ch in cm:
        vo = M.voice(ch, 50, 69, prev, center=59)
        prev = vo
        song.add('pad', pad_chord(song, vo, song.dur(b0, d), 'glass', attack=1.0, release=1.8, bright=2.2,
                                  rate=0.35, mix=0.6), b0, gain=0.3)
        bn = ch.bass_note(36, 47)
        song.add('sub', song.cached(('sub', bn, d), lambda: I.pad(f_(bn), song.dur(b0, d), 'glass', attack=0.3,
                                                                  release=1.0, voices=1, bright=1.2)),
                 b0, gain=0.16)
    # celesta arpeggios in A and C, harp in B
    for b0, d, ch in cm:
        bar = int(b0 // 4)
        if bar < 8:
            arp = [m for m in range(62, 88) if m % 12 in ch.pcs]
            pat = [0, 1, 2, 3, 4, 3, 2, 1]
            for k in range(int(d * 2)):
                m = arp[min(pat[k % 8], len(arp) - 1)]
                song.add('celesta', bell(song, 'celesta', m, 2.2, 0.55 + (0.1 if k % 4 == 0 else 0), 1.8),
                         b0 + 0.5 * k, pan=0.3 if k % 2 else -0.1, gain=0.5)
        elif bar < 16:
            arp = [m for m in range(50, 77) if m % 12 in ch.pcs]
            pat = [0, 2, 1, 3, 2, 4, 3, 5]
            for k in range(int(d * 2)):
                m = arp[min(pat[k % 8], len(arp) - 1)]
                song.add('harp', pluck(song, 'harp', m, 2.2, 0.5 + (0.12 if k % 4 == 0 else 0), k), b0 + 0.5 * k,
                         pan=0.3, gain=1.14)
        else:
            arp = [m for m in range(55, 81) if m % 12 in ch.pcs]
            pat = [0, 2, 3, 1, 2, 4, 3, 2]
            for k in range(int(d * 2)):
                m = arp[min(pat[k % 8], len(arp) - 1)]
                song.add('harp', pluck(song, 'harp', m, 2.0, 0.42, k), b0 + 0.5 * k, pan=0.35, gain=0.88)
    # melodies
    notes, _ = M.parse(MENU_B)
    song.line('flute', notes, 8, soft_flute_line, pan=-0.1, gain=0.36, art=0.95, vel=0.75)
    notes, _ = M.parse(MENU_C)
    for b, d, m, s, a in notes:
        song.add('celesta', bell(song, 'celesta', m + 12, 2.5, 0.7, 2.2), song.bar(16) + b, pan=0.2, gain=0.6)
        song.add('celesta', bell(song, 'celesta', m, 2.5, 0.5, 2.0), song.bar(16) + b, pan=-0.2, gain=0.3)
    low = [(b, d, m - 12, s, a) for (b, d, m, s, a) in notes if b < 16]
    song.line('flute', low, 16, soft_flute_line, pan=-0.1, gain=0.22, art=0.95, vel=0.6)
    # twinkles and triangle accents
    for bar in range(0, 24, 2):
        tw = song.cached(('tw', bar % 6), lambda: I.sparkle(2.5, 10, 2500, 7000, root=62, scale=I.LYDIAN,
                                                            grain=(0.15, 0.6), jitter=0.5))
        song.add('twinkle', tw, song.bar(bar) + 1, pan=0.0, gain=0.22)
    tri = song.cached('tri', lambda: I.triangle_inst(1.0, 1180, 3.0))
    for bar in (0, 8, 16):
        song.add('triangle', tri, song.bar(bar), pan=0.5, gain=0.33)
    # high shimmer pad in the C section
    for b0, d, ch in cm:
        if b0 >= song.bar(16):
            vo = M.voice(ch, 74, 88, None, center=81)
            song.add('shimmer', pad_chord(song, vo, song.dur(b0, d), 'glass', attack=1.2, release=1.5,
                                          bright=1.5, rate=0.6, mix=0.7), b0, gain=0.17)
    return song, 'menu'


# ---------------------------------------------------------------------------

IRS = {
    'hall': lambda: S.make_ir(1.8, hf=0.45, lf=1.1, predelay=0.02, stereo=True, seed_=101),
    'combat': lambda: S.make_ir(1.3, hf=0.4, lf=1.0, predelay=0.012, stereo=True, seed_=102),
    'menu': lambda: S.make_ir(3.2, hf=0.6, lf=1.0, predelay=0.03, stereo=True, bright=11000.0, seed_=103),
}
TARGET = {'music_town': -16.0, 'music_combat': -15.0, 'music_menu': -18.0}
DESC = {
    'music_town': 'Cheerful whimsical town theme, G major 112 BPM swung: pizzicato oom-pah, flute tune, '
                  'clarinet counter-line, harp, glockenspiel, soft strings, shaker/woodblock/tambourine',
    'music_combat': 'Driving, tense-but-fun battle loop, D minor 150 BPM: synth bass + spiccato strings, '
                    'brass stabs, horn-section theme, kit + taiko, clockwork square-arp breakdown',
    'music_menu': 'Calm, magical menu loop, D Lydian 72 BPM: glassy pad, celesta and harp arpeggios, '
                  'soft flute melody, sub bass, twinkles, big reverb',
}
TRACKS = {'town': make_town, 'combat': make_combat, 'menu': make_menu}


def build(key):
    t0 = time.time()
    song, irk = TRACKS[key]()
    t1 = time.time()
    mix = M.mixdown(song, IRS[irk]())
    out = M.master(mix, TARGET[song.name])
    path = os.path.join(OUT, song.name + '.wav')
    S.write_wav(path, out, loop=True)
    print('%s: %d samples (%.2f s), compose %.1fs, mix %.1fs, LUFS %.1f, peak %.2f dBFS' % (
        song.name, song.N, song.N / S.SR, t1 - t0, time.time() - t1, S.loudness_int(out),
        S.a2db(np.max(np.abs(out)))))
    M.report_energy(song)
    return song.name


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    want = [a for a in argv if not a.startswith('--')] or list(TRACKS)
    names = [build(k) for k in want]
    if '--nopreview' not in argv:
        import qa
        qa.run_music(names)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
