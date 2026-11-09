"""Build every RuneWire sound effect into assets/audio/sfx/<name>.wav.

    cd <project root>
    env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/make_sfx.py
    # only some sounds (names or group names), skipping the preview sheets:
    env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/make_sfx.py -- coin_pickup reward --nopreview

All sounds are synthesised here; nothing is sampled. Output: 16-bit 44.1 kHz
mono. One-shots are loudness-matched per group, then peak-limited to -1 dBFS.
*_loop files carry a 'smpl' loop chunk and are built circularly (every
oscillator, filter, delay and reverb wraps), so the seam is inaudible.
"""
import math
import os
import sys
import time
import zlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import synth as S  # noqa: E402
import instruments as I  # noqa: E402
from synth import ns, times, TAU, hz  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'audio', 'sfx')

# Loudness targets in LUFS: one-shots use the max short-window (200 ms) loudness,
# loops use gated integrated loudness. A file is never limited by more than
# MAX_LIMIT dB; past that it is simply left quieter.
TARGETS = {
    'ui': -12.5, 'reward': -11.5, 'step_grass': -16.5, 'step_stone': -20.0, 'move': -14.0,
    'spell': -11.5, 'weapon': -11.0, 'tool': -13.0, 'impact': -12.0, 'enemy': -12.0,
    'tool_loop': -16.0, 'loop': -16.0, 'enemy_loop': -17.0, 'amb': -20.0,
}
MAX_LIMIT = 4.0
CEILING = -1.0

REG = {}


def sfx(name, group, desc, loop=False, gain=0.0):
    def deco(fn):
        REG[name] = dict(fn=fn, group=group, desc=desc, loop=loop, gain=gain)
        return fn
    return deco


_IR = {}


def ir(kind):
    if kind not in _IR:
        _IR[kind] = {
            'room': lambda: S.make_ir(0.45, hf=0.5, predelay=0.004, bright=9000.0, seed_=11),
            'hall': lambda: S.make_ir(1.6, hf=0.45, predelay=0.015, seed_=12),
            'magic': lambda: S.make_ir(2.4, hf=0.7, lf=0.9, predelay=0.02, bright=12000.0, seed_=13),
            'big': lambda: S.make_ir(2.6, hf=0.35, lf=1.3, predelay=0.01, bright=7000.0, seed_=14),
            'outdoor': lambda: S.make_ir(0.9, hf=0.4, predelay=0.03, early=3, seed_=15),
            'factory': lambda: S.make_ir(1.4, hf=0.45, predelay=0.02, seed_=16),
        }[kind]()
    return _IR[kind]


def rv(x, kind, wet, circular=False):
    return S.reverb(x, ir(kind), wet, circular=circular)


def env_t(n, pts, curve=None):
    return S.env_pts(pts, n, curve)


def cut(x, dur, fade=0.3):
    """Truncate to dur seconds with a raised-cosine fade over the last `fade` s
    (keeps an inaudible reverb tail from outlasting the sound)."""
    return S.fade(S.pad_to(x, ns(dur)), 0.0, fade)


# ===========================================================================
# UI
# ===========================================================================

@sfx('ui_click', 'ui', 'Soft wooden tock for button presses')
def ui_click():
    out = S.zeros(0.1)
    S.place(out, S.modal(ns(0.09), [(1450, 1.0, 0.045), (2950, 0.45, 0.03), (4600, 0.15, 0.02)]), 0)
    S.place(out, I.thump(520, 300, 0.09, 0.008, 0.04) * 0.5, 0)
    S.place(out, I.click(0.003, 4200, 0.9) * 0.8, 0)
    return out


@sfx('ui_hover', 'ui', 'Tiny soft rising tick for hovering a button', gain=-5.0)
def ui_hover():
    n = ns(0.06)
    t = times(n)
    f = 2300 + 500 * (1 - np.exp(-t / 0.01))
    return (S.sine(f, n) + 0.15 * S.sine(2 * f, n)) * S.decay(n, 0.05, attack=0.002)


@sfx('ui_buy', 'ui', 'Cha-ching: purse-clasp clack and a bright coin chord')
def ui_buy():
    out = S.zeros(1.0)
    cha = I.metal(1250, 0.12, t60=0.07, bright=0.8, click_amt=0.6) \
        + 0.6 * I.nburst(0.12, lo=1500, hi=7000, t60=0.04)
    S.place(out, cha * 0.7, 0)
    S.place(out, I.bell(hz('E6'), 0.9, 'coin', t60=0.7), 0.07)
    S.place(out, I.bell(hz('B6'), 0.9, 'coin', t60=0.6, vel=0.8) * 0.7, 0.075)
    S.place(out, I.bell(hz('E7'), 0.5, 'coin', t60=0.3, vel=0.6) * 0.35, 0.08)
    S.place(out, I.sparkle(0.6, 25, 4000, 10000, root=76) * 0.25, 0.08)
    return rv(out, 'room', 0.18)


@sfx('ui_error', 'ui', 'Friendly low bonk-bonk for an invalid action')
def ui_error():
    out = S.zeros(0.45)
    for f, t0 in ((hz('C4'), 0.0), (hz('A3'), 0.13)):
        n = ns(0.2)
        t = times(n)
        ff = f * (1 + 0.06 * np.exp(-t / 0.02))
        tone = S.harm(ff, n, bright=2.2, kind='square', even=0.15) * S.adsr(n, 0.004, 0.06, 0.5, 0.05, gate=0.1)
        S.place(out, tone, t0)
        S.place(out, I.wood(f * 2, 0.1, 0.04, click_amt=0.2) * 0.25, t0)
    return S.lp(out, 1800)


@sfx('ui_open', 'ui', 'Quick upward swish with a rising two-note marimba pluck (panel opens)')
def ui_open():
    out = S.zeros(0.6)
    S.place(out, I.whoosh(0.16, 700, 4500, q=1.4, peak=0.7) * 0.5, 0)
    S.place(out, I.bell(hz('G5'), 0.4, 'marimba', t60=0.35, vel=0.8) * 0.8, 0.03)
    S.place(out, I.bell(hz('D6'), 0.5, 'marimba', t60=0.4, vel=0.9), 0.095)
    return rv(out, 'room', 0.15)


@sfx('ui_close', 'ui', 'Downward swish with a falling two-note marimba pluck (panel closes)')
def ui_close():
    out = S.zeros(0.55)
    S.place(out, I.whoosh(0.15, 4000, 700, q=1.4, peak=0.3) * 0.5, 0)
    S.place(out, I.bell(hz('D6'), 0.4, 'marimba', t60=0.3, vel=0.8) * 0.8, 0.02)
    S.place(out, I.bell(hz('G5'), 0.5, 'marimba', t60=0.35, vel=0.9), 0.085)
    return rv(out, 'room', 0.15)


@sfx('ui_bag', 'ui', 'Inventory opens: buckle tick, leather satchel flap and a soft rustle')
def ui_bag():
    out = S.zeros(0.4)
    S.place(out, I.metal(2300, 0.05, 0.02, bright=0.6, click_amt=0.4) * 0.25, 0)
    n = ns(0.16)
    flap = S.filt(S.pink(n) * 3, lambda f: S.H_bp(f, 650, 0.8) * S.H_lp(f, 3000, 2))
    S.place(out, flap * env_t(n, [(0, 0), (0.012, 1), (0.16, 0)], curve=4) * 0.9, 0.02)
    S.place(out, I.thump(150, 80, 0.12, 0.015, 0.07) * 0.6, 0.025)
    m = ns(0.18)
    crinkle = np.clip(S.smooth_noise(m, 70.0), 0, None) ** 1.5
    rs = S.filt(S.white(m) * crinkle, lambda f: S.H_bp(f, 2600, 0.7) * S.H_lp(f, 7000, 2))
    S.place(out, rs * env_t(m, [(0, 0), (0.03, 1), (0.18, 0)], curve=2) * 0.35, 0.05)
    return cut(rv(out, 'room', 0.08), 0.32, 0.08)


@sfx('ui_equip', 'ui', 'Equip: crisp holster click-clack')
def ui_equip():
    out = S.zeros(0.25)
    # click: small latch
    S.place(out, I.metal(2500, 0.06, 0.03, bright=0.6, click_amt=0.3) * 0.45, 0)
    S.place(out, I.wood(700, 0.06, 0.03, bright=0.8, click_amt=0.2) * 0.35, 0)
    S.place(out, I.nburst(0.05, fc=1800, q=1.2, t60=0.04, attack=0.003) * 0.12, 0.02)
    # clack: the weapon seating in the holster, with more body
    S.place(out, I.metal(1100, 0.12, 0.08, bright=0.65, click_amt=0.3) * 0.5, 0.07)
    S.place(out, I.wood(300, 0.1, 0.07, bright=0.8, click_amt=0.2) * 0.6, 0.072)
    S.place(out, I.thump(260, 130, 0.09, 0.008, 0.07) * 0.8, 0.074)
    return cut(rv(out, 'room', 0.06), 0.25, 0.06)


@sfx('ui_sell', 'ui', 'Sell: coin clink and a light cash-register ka-ching')
def ui_sell():
    out = S.zeros(0.6)
    S.place(out, S.fade(I.bell(hz('E7'), 0.06, 'coin', t60=0.12, vel=0.8), 0.0, 0.015) * 0.45, 0)
    S.place(out, S.fade(I.bell(hz('B6'), 0.07, 'coin', t60=0.14, vel=0.8), 0.0, 0.015) * 0.45, 0.035)
    S.place(out, I.metal(1150, 0.1, 0.045, bright=0.65, click_amt=0.7) * 0.55, 0.08)
    S.place(out, I.nburst(0.04, fc=1700, q=0.9, t60=0.03) * 0.35, 0.08)
    S.place(out, I.thump(260, 140, 0.05, 0.008, 0.035) * 0.35, 0.08)
    S.place(out, I.bell(hz('A6'), 0.5, 'coin', t60=0.42, vel=0.9, detune=0.003) * 0.6, 0.125)
    S.place(out, I.bell(hz('C#7'), 0.4, 'glock', t60=0.3, vel=0.7) * 0.3, 0.13)
    S.place(out, I.sparkle(0.3, 28, 4000, 10000, root=69, env=lambda tt: math.exp(-tt / 0.1)) * 0.2, 0.13)
    return rv(out, 'room', 0.12)


@sfx('pouch_equip', 'ui', 'Pouch equip: leather pouch flap, buckle click and a little coin jingle')
def pouch_equip():
    out = S.zeros(0.45)
    # leather flap with a soft body thump
    n = ns(0.13)
    flap = S.filt(S.pink(n) * 3, lambda f: S.H_bp(f, 720, 0.8) * S.H_lp(f, 3200, 2))
    S.place(out, flap * env_t(n, [(0, 0), (0.01, 1), (0.13, 0)], curve=4) * 0.85, 0)
    S.place(out, I.thump(170, 85, 0.1, 0.012, 0.06) * 0.5, 0.004)
    # buckle: a bright tongue click and the frame settling
    S.place(out, I.metal(2450, 0.06, 0.028, bright=0.6, click_amt=0.5) * 0.42, 0.085)
    S.place(out, I.metal(1350, 0.08, 0.04, bright=0.6, click_amt=0.3) * 0.22, 0.09)
    # a few coins jingling inside
    r = S.rng()
    for k in range(5):
        f0 = r.uniform(2900, 4600)
        tink = S.modal(ns(0.16), [(f0, 1.0, r.uniform(0.07, 0.13)), (f0 * 1.47, 0.5, 0.06), (f0 * 2.21, 0.22, 0.04)])
        S.place(tink, I.click(0.002, 5000, 0.8) * 0.3, 0)
        S.place(out, tink * r.uniform(0.09, 0.17) * (1 - 0.1 * k), 0.12 + 0.034 * k + r.uniform(0, 0.012))
    return cut(rv(out, 'room', 0.08), 0.4, 0.1)


@sfx('objective_ping', 'ui', 'Objective updated: soft, short rising two-note chime (A5, D6)', gain=-2.0)
def objective_ping():
    out = S.zeros(0.6)
    for k, (nm, t0) in enumerate((('A5', 0.0), ('D6', 0.09))):
        f = hz(nm)
        S.place(out, I.bell(f, 0.42, 'celesta', t60=0.3 + 0.06 * k, vel=0.75 + 0.1 * k, mallet=0.08), t0)
        n = ns(0.36)
        glow = (S.sine(f, n) + 0.12 * S.sine(2 * f, n)) * S.decay(n, 0.3 + 0.06 * k, attack=0.006)
        S.place(out, glow * 0.22, t0)
    return cut(rv(out, 'room', 0.12), 0.45, 0.14)


# ===========================================================================
# rewards
# ===========================================================================

@sfx('coin_pickup', 'reward', 'Bright two-note coin chime (B5 then E6) with a little glitter')
def coin_pickup():
    out = S.zeros(0.8)
    a = S.fade(I.bell(hz('B5'), 0.085, 'coin', t60=0.3, vel=0.9), 0.0, 0.02)
    b = I.bell(hz('E6'), 0.65, 'coin', t60=0.55, detune=0.0025)
    S.place(out, a, 0)
    S.place(out, b, 0.075)
    S.place(out, I.sparkle(0.45, 18, 5000, 11000, root=76, grain=(0.03, 0.12)) * 0.2, 0.08)
    return rv(out, 'room', 0.15)


@sfx('coin_shower', 'reward', 'Cascade of clinking coins over a falling chime run')
def coin_shower():
    out = S.zeros(2.0)
    r = S.rng()
    K = 34
    for k in range(K):
        t0 = max(0.0, 1.35 * (k / K) ** 1.6 + r.uniform(-0.02, 0.02))
        f0 = r.uniform(2400, 4200)
        tink = S.modal(ns(0.3), [(f0, 1.0, r.uniform(0.1, 0.25)), (f0 * 1.48, 0.6, 0.12),
                                 (f0 * 2.18, 0.35, 0.08), (f0 * 2.75, 0.2, 0.05)])
        S.place(tink, I.click(0.003, 5000, 0.8) * 0.5, 0)
        S.place(out, tink * r.uniform(0.3, 1.0) * (1 - 0.5 * k / K), t0)
    for k, nm in enumerate(['E7', 'D7', 'B6', 'A6', 'G6', 'E6']):
        S.place(out, I.bell(hz(nm), 0.5, 'coin', t60=0.4, vel=0.7) * 0.35, 0.05 + 0.11 * k)
    S.place(out, I.sparkle(1.4, 30, 5000, 11000, root=76) * 0.3, 0)
    return rv(out, 'room', 0.2)


@sfx('quest_accept', 'reward', 'Parchment swish, harp arpeggio and soft glockenspiel: quest accepted')
def quest_accept():
    out = S.zeros(1.8)
    S.place(out, I.whoosh(0.25, 500, 2500, q=0.9, peak=0.6) * 0.25, 0)
    for k, nm in enumerate(['G4', 'C5', 'E5', 'G5']):
        S.place(out, I.pluck(hz(nm), 1.2, 'harp', vel=0.85 + 0.05 * k), 0.02 + 0.055 * k)
    S.place(out, I.bell(hz('C6'), 1.2, 'glock', t60=1.0, vel=0.8) * 0.6, 0.24)
    S.place(out, I.bell(hz('E6'), 1.2, 'glock', t60=1.0, vel=0.7) * 0.45, 0.245)
    padc = sum(I.pad(hz(nm), 0.5, 'warm', attack=0.15, release=0.6, bright=3.0) for nm in ['C4', 'E4', 'G4'])
    S.place(out, padc * 0.25, 0.2)
    return rv(out, 'hall', 0.22)


@sfx('quest_complete', 'reward', 'Short brass fanfare (C-E-G pickup to a held C major) with timpani and glitter')
def quest_complete():
    out = S.zeros(3.0)
    sp = 0.11
    for nm, t0, d in (('C5', 0.0, 0.09), ('E5', sp, 0.09), ('G5', 2 * sp, 0.09), ('C6', 3 * sp, 1.15)):
        S.place(out, I.brass(hz(nm), d, vel=1.0, voices=3, bright=7.0), t0)
    for nm in ['G5', 'E5', 'C5']:
        S.place(out, I.brass(hz(nm), 1.15, vel=0.8, voices=2, bright=5.0) * 0.5, 3 * sp)
    S.place(out, I.brass(hz('C4'), 1.15, vel=0.8, voices=2, bright=4.0) * 0.5, 3 * sp)
    S.place(out, I.timpani(hz('G2'), 0.6, t60=0.5) * 0.5, 2 * sp)
    S.place(out, I.timpani(hz('C3'), 1.0, t60=1.6) * 0.8, 3 * sp)
    S.place(out, I.crash(0.35, 2.0) * 0.4, 3 * sp)
    S.place(out, I.sparkle(1.4, 40, 3000, 10000, root=72, rise=1.0) * 0.25, 3 * sp)
    S.place(out, I.bell(hz('C7'), 1.2, 'glock', t60=1.0, vel=0.6) * 0.3, 3 * sp + 0.02)
    return rv(out, 'hall', 0.25)


@sfx('level_up', 'reward', 'Jingle: celesta/harp arpeggio racing up into a shimmering C add9 chord')
def level_up():
    out = S.zeros(3.2)
    run = ['C5', 'E5', 'G5', 'C6', 'E6', 'G6']
    for k, nm in enumerate(run):
        t0 = 0.065 * k
        S.place(out, I.bell(hz(nm), 0.8, 'celesta', t60=0.7, vel=0.9) * 0.8, t0)
        S.place(out, I.pluck(hz(nm) / 2, 0.8, 'harp', vel=0.7) * 0.5, t0)
    tc = 0.065 * len(run) + 0.03
    for nm in ['C6', 'E6', 'G6', 'D7']:
        S.place(out, I.bell(hz(nm), 2.0, 'celesta', t60=1.8, vel=0.8, detune=0.002) * 0.5, tc)
    chord = sum(I.pad(hz(nm), 1.0, 'glass', attack=0.05, release=1.2, bright=2.5) for nm in ['C4', 'G4', 'D5', 'E5'])
    S.place(out, S.chorus(chord, 3, rate=0.8, mix=0.6) * 0.35, tc)
    S.place(out, I.whoosh(0.5, 600, 6000, q=1.0, peak=0.85) * 0.3, 0)
    S.place(out, I.sparkle(1.8, 45, 3000, 11000, root=72, rise=0.7) * 0.3, tc - 0.05)
    S.place(out, I.timpani(hz('C3'), 0.6, 1.0) * 0.4, tc)
    return rv(out, 'magic', 0.25)


@sfx('notify', 'reward', 'Gentle two-tone vibraphone chime (A5, E6) for notifications', gain=-3.0)
def notify():
    out = S.zeros(1.3)
    S.place(out, I.bell(hz('A5'), 1.0, 'vibes', t60=0.9, vel=0.8, trem=0.25), 0)
    S.place(out, I.bell(hz('E6'), 1.0, 'vibes', t60=1.0, vel=0.85, trem=0.25), 0.14)
    return rv(out, 'hall', 0.18)


@sfx('talent_unlock', 'reward',
     'Talent unlocked: warm, triumphant three-note chime (D-G-B) over a soft brass swell, with a sparkle')
def talent_unlock():
    out = S.zeros(1.2)
    sp = 0.085
    for k, nm in enumerate(('D5', 'G5', 'B5')):
        last = k == 2
        f = hz(nm)
        d = 0.9 if last else 0.4
        S.place(out, I.bell(f, d, 'vibes', t60=0.75 if last else 0.3, vel=0.8 + 0.07 * k) * 0.5, sp * k)
        S.place(out, I.bell(f * 2, d, 'celesta', t60=0.55 if last else 0.25, vel=0.7) * 0.25, sp * k)
        S.place(out, I.pluck(f / 2, d, 'harp', vel=0.75) * 0.4, sp * k)
    tb = 2 * sp
    for nm in ('G4', 'B4', 'D5'):
        S.place(out, I.brass(hz(nm), 0.32, vel=0.75, voices=2, bright=4.5, attack=0.05, release=0.35) * 0.13, tb)
    S.place(out, I.brass(hz('G3'), 0.32, vel=0.7, voices=2, bright=3.5, attack=0.05, release=0.35) * 0.12, tb)
    S.place(out, I.sparkle(0.6, 50, 3000, 10000, root=67, rise=0.8, env=lambda tt: math.exp(-tt / 0.22)) * 0.28,
            tb + 0.02)
    S.place(out, I.bell(hz('G7'), 0.6, 'glock', t60=0.45, vel=0.55) * 0.12, tb + 0.03)
    return cut(rv(out, 'hall', 0.18), 0.95, 0.3)


# ===========================================================================
# loot, chests, gathering and crafting
# ===========================================================================

def creak(dur, f0, f1, rough=0.12, body=((650.0, 3.0, 1.0), (1400.0, 4.0, 0.6), (2600.0, 5.0, 0.3))):
    """Wooden stick-slip creak: a jittery low pulse buzz gliding f0 -> f1 Hz, rung
    through hollow-box resonances body = [(fc, q, gain), ...]."""
    n = ns(dur)
    t = times(n)
    f = f0 * (f1 / f0) ** (t / dur) * np.exp(rough * S.smooth_noise(n, 15.0))
    am = 0.65 + 0.35 * np.tanh(1.5 * S.smooth_noise(n, 45.0))
    src = S.harm(f, n, bright=14.0) * am
    return S.filt(src, lambda fr: sum(g * S.H_bp(fr, fc, q) for fc, q, g in body) * S.H_hp(fr, 200.0, 2))


def grind(dur, fc=300.0, judder=24.0):
    """Heavy stone sliding on stone: rough low-mid noise with a stick-slip judder and grit."""
    n = ns(dur)
    body = S.filt(S.pink(n) * 4, lambda f: S.H_bp(f, fc, 0.8) + 0.45 * S.H_bp(f, fc * 2.6, 1.6)
                  + 0.2 * S.H_bp(f, fc * 5.5, 2.0))
    ph = np.cumsum(judder * np.exp(0.25 * S.smooth_noise(n, 3.0))) / S.SR
    jud = (0.5 + 0.5 * np.sin(TAU * ph)) ** 2
    am = (0.35 + 0.65 * jud) * (0.8 + 0.2 * np.tanh(S.smooth_noise(n, 12.0)))
    return body * am + I.crackle(dur, rate=300, lo=800, hi=5000, size=(0.0005, 0.004)) * 0.5


def gulp(f0=220.0, dur=0.12):
    """Cartoon swallow: a soft wet throat knock and a rounded, rising 'ulp' bubble tone."""
    out = np.zeros(ns(dur + 0.03))
    n = ns(dur)
    t = times(n)
    f = f0 * (1 + 1.4 * (t / dur) ** 1.4)
    tone = S.sine(f, n) + 0.3 * S.sine(2 * f, n) + 0.1 * S.sine(3 * f, n)
    S.place(out, S.fade(tone * np.clip(t / 0.008, 0, 1) * np.exp(-t / (dur * 0.45)), 0.0, 0.03), 0)
    S.place(out, I.thump(170, 90, 0.06, 0.01, 0.04) * 0.6, 0)
    S.place(out, I.nburst(0.02, fc=900, q=1.0, t60=0.015) * 0.25, 0)
    return out


def anvil(f0, vel=1.0):
    """Small anvil strike: bright ringing tink with a hammer click."""
    return I.metal(f0, 0.45, 0.3, ratios=(1.0, 2.71, 5.14), amps=(1.0, 0.35, 0.12), bright=0.8, click_amt=0.5) * vel


@sfx('chest_open', 'reward', 'Chest opens: latch knock, wooden creak, then a rising sparkly chime (G major)')
def chest_open():
    out = S.zeros(1.2)
    S.place(out, I.wood(300, 0.12, 0.05, bright=0.8, click_amt=0.5) * 0.45, 0)
    S.place(out, I.metal(1900, 0.08, 0.035, bright=0.6, click_amt=0.4) * 0.2, 0.004)
    cr = creak(0.34, 48, 95)
    S.place(out, cr * env_t(len(cr), [(0, 0), (0.04, 1), (0.24, 0.9), (0.34, 0)]) * 1.6, 0.03)
    t0 = 0.3
    for k, nm in enumerate(['G5', 'B5', 'D6', 'G6']):
        S.place(out, I.bell(hz(nm), 0.7, 'celesta', t60=0.4 + 0.04 * k, vel=0.75 + 0.07 * k) * 0.55, t0 + 0.055 * k)
    S.place(out, I.bell(hz('D7'), 0.5, 'glock', t60=0.35, vel=0.6) * 0.15, t0 + 0.17)
    S.place(out, I.sparkle(0.45, 50, 3000, 8000, root=67, rise=0.8, env=lambda tt: math.exp(-tt / 0.18)) * 0.22,
            t0 + 0.05)
    S.place(out, I.whoosh(0.35, 800, 4000, q=1.0, peak=0.75) * 0.18, t0 - 0.12)
    return cut(rv(out, 'hall', 0.12), 1.2, 0.3)


@sfx('chest_locked', 'impact', 'Locked chest: lid rattles against the latch, then a dull thunk')
def chest_locked():
    out = S.zeros(0.55)
    r = S.rng()
    for k, t0 in enumerate((0.0, 0.05, 0.095, 0.13)):
        S.place(out, I.wood(r.uniform(260, 320), 0.12, 0.045, bright=0.75, click_amt=0.45) * (0.75 - 0.1 * k), t0)
        S.place(out, I.metal(r.uniform(1500, 2100), 0.07, 0.03, bright=0.6, click_amt=0.4) * 0.25 * (1 - 0.15 * k),
                t0 + 0.006)
    S.place(out, I.thump(150, 75, 0.2, 0.02, 0.1) * 0.9, 0.2)
    S.place(out, I.wood(150, 0.25, 0.08, bright=0.55, click_amt=0.25) * 0.8, 0.2)
    S.place(out, I.nburst(0.06, hi=900, t60=0.05, color='pink') * 0.4, 0.2)
    return cut(rv(S.lp(out, 6000), 'room', 0.08), 0.45, 0.12)


@sfx('vault_open', 'reward', 'Rune vault opens: heavy stone grind blooming into a shimmering D add9 chord')
def vault_open():
    out = S.zeros(2.0)
    S.place(out, I.thump(85, 40, 0.5, 0.04, 0.35) * 0.6, 0)
    S.place(out, I.nburst(0.08, hi=1500, t60=0.06, color='pink') * 0.4, 0)
    n = ns(0.85)
    S.place(out, grind(0.85) * env_t(n, [(0, 0), (0.05, 1), (0.45, 0.8), (0.85, 0)]) * 0.35, 0.02)
    S.place(out, S.lp(S.brown(n) * 4, 110) * env_t(n, [(0, 0), (0.1, 1), (0.5, 0.6), (0.85, 0)]) * 0.3, 0.02)
    tb = 0.5
    chord = sum(I.pad(hz(nm), 0.4, 'glass', attack=0.15, release=0.45, bright=2.5) for nm in ('D4', 'A4', 'E5', 'F#5'))
    chord *= 1 + 0.25 * np.sin(TAU * 6.0 * times(len(chord)))
    S.place(out, S.chorus(chord, 3, rate=1.2, depth_ms=3, mix=0.6) * 0.55, tb)
    for k, nm in enumerate(('D5', 'F#5', 'A5', 'D6', 'E6')):
        S.place(out, I.bell(hz(nm), 0.7, 'crystal', t60=0.5, vel=0.75) * 0.35, tb + 0.06 * k)
    S.place(out, I.sparkle(0.7, 50, 3000, 9000, root=62, rise=0.8,
                           env=lambda tt: math.sin(math.pi * min(tt / 0.7, 1.0))) * 0.35, tb)
    S.place(out, I.whoosh(0.55, 400, 4500, q=0.9, peak=0.85) * 0.25, tb - 0.35)
    return cut(rv(out, 'hall', 0.2), 1.75, 0.4)


@sfx('crystal_harvest', 'reward', 'Crystal harvest: small glassy crack and tinkling crystal chimes (E major)')
def crystal_harvest():
    out = S.zeros(0.8)
    r = S.rng()
    S.place(out, I.nburst(0.012, lo=2500, t60=0.008, attack=0.0002) * 0.7, 0)
    modes = [(r.uniform(2000, 6500), r.uniform(0.3, 1.0), r.uniform(0.02, 0.06)) for _ in range(10)]
    S.place(out, S.modal(ns(0.12), modes) * 0.18, 0)
    S.place(out, I.thump(450, 220, 0.05, 0.006, 0.03) * 0.35, 0)
    for k, (nm, dt) in enumerate((('B6', 0.03), ('E7', 0.07), ('G#6', 0.115), ('C#7', 0.16), ('E6', 0.21),
                                  ('B6', 0.3))):
        S.place(out, I.bell(hz(nm), 0.55, 'crystal', t60=0.38, vel=0.9 - 0.1 * k, mallet=0.1) * (0.4 - 0.045 * k), dt)
    S.place(out, I.sparkle(0.4, 40, 3500, 9000, root=76, env=lambda tt: math.exp(-tt / 0.14)) * 0.2, 0.02)
    return cut(rv(out, 'hall', 0.1), 0.75, 0.25)


@sfx('scavenge', 'reward', 'Scavenging scrap: rummaging clinks of loose bolts and metal bits')
def scavenge():
    out = S.zeros(0.75)
    r = S.rng()
    n = ns(0.55)
    rub = S.filt(S.pink(n) * 3, lambda f: S.H_bp(f, 1800, 0.8)) * (0.5 + 0.5 * np.abs(S.smooth_noise(n, 25.0)))
    S.place(out, rub * env_t(n, [(0, 0), (0.05, 1), (0.4, 0.6), (0.55, 0)]) * 0.25, 0)
    for c0, k in ((0.0, 7), (0.24, 6)):
        for _ in range(k):
            S.place(out, I.metal(r.uniform(900, 3800), 0.15, r.uniform(0.04, 0.1), bright=0.6, click_amt=0.4)
                    * r.uniform(0.15, 0.4), c0 + 0.16 * r.uniform() ** 1.3)
    S.place(out, I.metal(520, 0.25, 0.12, bright=0.6, click_amt=0.3) * 0.35, 0.02)
    S.place(out, I.thump(220, 120, 0.08, 0.01, 0.05) * 0.3, 0.02)
    return rv(out, 'room', 0.1)


@sfx('craft', 'reward', 'Crafting: tink-tink-TING on a small anvil, then a rising sparkle shimmer')
def craft():
    out = S.zeros(1.1)
    for t0, f0, v in ((0.0, hz('G6'), 0.6), (0.13, hz('G6'), 0.7), (0.29, hz('C7'), 1.0)):
        S.place(out, anvil(f0, v), t0)
        S.place(out, I.thump(300, 150, 0.06, 0.008, 0.04) * 0.25 * v, t0)
    ts = 0.33
    S.place(out, I.sparkle(0.45, 60, 3000, 8000, root=72, rise=0.6, env=lambda tt: math.exp(-tt / 0.2)) * 0.35, ts)
    S.place(out, I.bell(hz('G6'), 0.5, 'celesta', t60=0.35, vel=0.7) * 0.25, ts + 0.04)
    S.place(out, I.bell(hz('C7'), 0.5, 'celesta', t60=0.35, vel=0.7) * 0.25, ts + 0.08)
    S.place(out, I.whoosh(0.4, 1200, 6000, q=1.0, peak=0.6) * 0.15, ts - 0.05)
    return rv(out, 'room', 0.15)


@sfx('pickup_weapon', 'reward', 'Weapon pickup: bright, quick rising three-note arpeggio (A major)')
def pickup_weapon():
    out = S.zeros(0.5)
    S.place(out, I.metal(1500, 0.08, 0.04, bright=0.6, click_amt=0.6) * 0.3, 0)
    for k, nm in enumerate(['A5', 'C#6', 'E6']):
        f = hz(nm)
        last = k == 2
        n = ns(0.35 if last else 0.1)
        sq = S.harm(f, n, bright=3.0, kind='square', even=0.25) * S.decay(n, 0.22 if last else 0.09, attack=0.002)
        S.place(out, sq * 0.25, 0.045 * k)
        S.place(out, I.bell(f, 0.35 if last else 0.15, 'glock', t60=0.22 if last else 0.12, vel=0.85) * 0.7, 0.045 * k)
    S.place(out, I.sparkle(0.25, 30, 4000, 10000, root=69, env=lambda tt: math.exp(-tt / 0.1)) * 0.15, 0.09)
    return rv(out, 'room', 0.1)


@sfx('pickup_rare', 'reward', 'Rare loot: short magical fanfare sting (celesta run into a brassy D major chord)')
def pickup_rare():
    out = S.zeros(1.3)
    for k, nm in enumerate(['A5', 'D6', 'F#6']):
        S.place(out, I.bell(hz(nm), 0.4, 'celesta', t60=0.3, vel=0.85) * 0.5, 0.05 * k)
        S.place(out, I.pluck(hz(nm) / 2, 0.4, 'harp', vel=0.7) * 0.35, 0.05 * k)
    th = 0.16
    for nm in ('D5', 'F#5', 'A5'):
        S.place(out, I.brass(hz(nm), 0.28, vel=0.9, voices=2, bright=6.0, release=0.2) * 0.3, th)
    S.place(out, I.brass(hz('D4'), 0.28, vel=0.8, voices=2, bright=4.0, release=0.2) * 0.3, th)
    S.place(out, I.bell(hz('D7'), 0.7, 'glock', t60=0.6, vel=0.7) * 0.25, th)
    S.place(out, I.bell(hz('A6'), 0.7, 'celesta', t60=0.6, vel=0.7) * 0.3, th + 0.01)
    chord = sum(I.pad(hz(nm), 0.25, 'glass', attack=0.04, release=0.35, bright=2.5) for nm in ('D5', 'A5', 'E6'))
    S.place(out, S.chorus(chord, 3, rate=1.0, mix=0.6) * 0.25, th)
    S.place(out, I.sparkle(0.6, 50, 3000, 9000, root=74, rise=0.8, env=lambda tt: math.exp(-tt / 0.22)) * 0.3, th)
    S.place(out, I.timpani(hz('D3'), 0.6, t60=0.5) * 0.4, th)
    return cut(rv(out, 'hall', 0.15), 1.25, 0.35)


@sfx('drink', 'reward', 'Potion drink: cartoony gulp-gulp and a bubbly fizz')
def drink():
    out = S.zeros(0.65)
    S.place(out, gulp(240), 0.0)
    S.place(out, gulp(270) * 0.9, 0.17)
    n = ns(0.32)
    fz = I.crackle(0.32, rate=1400, lo=3500, hi=11000, size=(0.0002, 0.0007), env=lambda tt: math.exp(-tt / 0.12))
    S.place(out, fz * 0.5, 0.3)
    S.place(out, I.hiss(0.32, 4000, 10000, 0.3, 40) * S.decay(n, 0.3, attack=0.02) * 0.06, 0.3)
    r = S.rng()
    for _ in range(8):
        m = ns(r.uniform(0.006, 0.012))
        tm = times(m)
        f = r.uniform(2000, 4500) * (1 + 0.6 * tm / (m / S.SR))
        S.place(out, S.sine(f, m) * np.sin(np.pi * tm / (m / S.SR)) * r.uniform(0.04, 0.1), 0.3 + r.uniform(0, 0.22))
    return rv(out, 'room', 0.08)


def blip(f0, dur, rise=0.9):
    """Liquid bubble: a short sine whose pitch rises as it nears the surface."""
    n = ns(dur)
    t = times(n)
    return S.sine(f0 * (1 + rise * (t / dur) ** 1.2), n) * np.sin(np.pi * t / dur) ** 1.5


@sfx('forge_smelt', 'reward', 'Forge smelt: bellows puff, molten sizzle and two ringing anvil clangs')
def forge_smelt():
    out = S.zeros(1.35)
    # bellows: a little leather creak and a soft, breathy whuff
    cr = creak(0.1, 55, 68, rough=0.1, body=((480.0, 3.0, 1.0), (1150.0, 4.0, 0.5)))
    S.place(out, cr * env_t(len(cr), [(0, 0), (0.015, 1), (0.1, 0)]) * 0.3, 0)
    n = ns(0.34)
    puff = S.filt(S.pink(n) * 3, lambda f: S.H_lp(f, 1500, 2) * S.H_hp(f, 110, 2) * S.H_bell(f, 420, 4.0, 1.5))
    S.place(out, puff * env_t(n, [(0, 0), (0.07, 1), (0.34, 0)], curve=2.5) * 0.8, 0.03)
    S.place(out, I.thump(110, 62, 0.2, 0.03, 0.14) * 0.3, 0.05)
    # molten metal: hot sizzle, crackle and a couple of thick blorps
    ts = 0.22
    m = ns(0.55)
    gate = (S.smooth_noise(m, 110) > 0.2) * (0.6 + 0.4 * S.white(m))
    sz = S.filt(S.white(m) * gate, lambda f: S.H_bp(f, 5200, 0.7))
    S.place(out, sz * env_t(m, [(0, 0), (0.04, 1), (0.25, 0.5), (0.55, 0)], curve=1.5) * 0.24, ts)
    S.place(out, I.crackle(0.5, rate=200, lo=2000, hi=8000, env=lambda tt: math.exp(-tt / 0.2)) * 0.5, ts)
    for t0, f0 in ((ts + 0.03, 130.0), (ts + 0.16, 165.0)):
        S.place(out, blip(f0, 0.06, rise=1.2) * 0.35, t0)
    # two anvil clangs: a bright ting over a heavier ringing body
    for t0, f0, v in ((0.58, hz('D6'), 0.8), (0.8, hz('G6'), 1.0)):
        S.place(out, anvil(f0, v) * 0.9, t0)
        S.place(out, I.metal(f0 * 0.37, 0.6, 0.35, ratios=(1.0, 2.43, 3.9, 5.6), amps=(1, .7, .45, .25),
                             bright=0.75, click_amt=0.3) * 0.35 * v, t0)
        S.place(out, I.thump(240, 120, 0.08, 0.008, 0.05) * 0.35 * v, t0)
    return cut(rv(out, 'room', 0.15), 1.15, 0.3)


@sfx('alchemy_brew', 'reward', 'Alchemy brew: bubbling glass flask, a cork pop and a little magical sparkle')
def alchemy_brew():
    out = S.zeros(1.25)
    r = S.rng()
    # bubbling: liquid blips knocking a thin glass flask
    for k in range(18):
        S.place(out, blip(r.uniform(380, 950), r.uniform(0.012, 0.03)) * r.uniform(0.12, 0.3),
                0.5 * k / 18 + r.uniform(0, 0.03))
    glass = ((2650.0, 1.0, 0.25), (4300.0, 0.5, 0.15), (6900.0, 0.25, 0.08))
    for t0 in (0.06, 0.21, 0.37):
        S.place(out, S.modal(ns(0.3), [(f * r.uniform(0.99, 1.01), a, d) for f, a, d in glass])
                * r.uniform(0.04, 0.07), t0)
    n = ns(0.55)
    simmer = S.filt(S.pink(n) * 2, lambda f: S.H_bp(f, 900, 1.0))
    S.place(out, simmer * env_t(n, [(0, 0), (0.05, 1), (0.45, 0.7), (0.55, 0)]) * 0.05, 0)
    # cork pop: a resonant bottle-neck 'pok' with a quick upward blip
    tp = 0.6
    m = ns(0.07)
    tm = times(m)
    f = 380 * np.exp(np.log(1150 / 380) * np.clip(tm / 0.018, 0, 1))
    S.place(out, (S.sine(f, m) + 0.2 * S.sine(2 * f, m)) * S.decay(m, 0.06, attack=0.0008) * 0.6, tp)
    S.place(out, I.nburst(0.05, fc=850, q=3.0, t60=0.035, attack=0.0003) * 0.7, tp)
    S.place(out, I.click(0.003, 3000, 0.8) * 0.8, tp)
    S.place(out, I.thump(300, 160, 0.05, 0.006, 0.03) * 0.3, tp)
    # a little magical sparkle as the brew is done
    S.place(out, I.sparkle(0.45, 55, 3000, 9000, root=76, rise=0.8, env=lambda tt: math.exp(-tt / 0.18)) * 0.28,
            tp + 0.03)
    S.place(out, I.bell(hz('E6'), 0.5, 'celesta', t60=0.38, vel=0.7) * 0.22, tp + 0.05)
    S.place(out, I.bell(hz('B6'), 0.5, 'celesta', t60=0.38, vel=0.7) * 0.18, tp + 0.11)
    return cut(rv(out, 'room', 0.12), 1.05, 0.3)


@sfx('enchant', 'reward',
     'Enchant: shimmering glass chord gliding up and swelling, with rising crystal chimes (D add9)')
def enchant():
    out = S.zeros(1.7)
    n = ns(1.15)
    t = times(n)
    glide = 2 ** (-(2.0 / 12) * np.exp(-t / 0.12))            # scoops up a whole tone into tune
    r = S.rng()
    chord = np.zeros(n)
    for nm in ('D4', 'A4', 'E5', 'F#5'):
        for c in (-6.0, 0.0, 6.0):
            f = hz(nm) * 2 ** (c / 1200.0) * glide
            chord += 0.75 * S.sine(f, n, r.uniform()) + 0.3 * S.harm(f, n, bright=2.2, kind='square', ph0=r.uniform())
    chord *= env_t(n, [(0, 0), (0.03, 0.35), (0.32, 1.0), (0.7, 0.85), (1.15, 0)]) \
        * (1 + 0.2 * np.sin(TAU * 6.5 * t)) / 12
    S.place(out, S.chorus(chord, 3, rate=1.1, depth_ms=3, mix=0.6) * 0.6, 0)
    for k, nm in enumerate(('D6', 'F#6', 'A6', 'D7', 'E7')):
        S.place(out, I.bell(hz(nm), 0.8, 'crystal', t60=0.6, vel=0.65 + 0.06 * k, mallet=0.1) * 0.3, 0.07 * k)
    S.place(out, I.sparkle(0.9, 55, 3000, 10000, root=62, rise=1.0,
                           env=lambda tt: math.sin(math.pi * min(0.15 + tt / 0.9, 1.0))) * 0.3, 0.0)
    S.place(out, I.whoosh(0.5, 500, 5000, q=0.9, peak=0.4) * 0.18, 0)
    return cut(rv(out, 'magic', 0.25), 1.3, 0.35)


@sfx('loom_weave', 'reward', 'Loom weave: quick wooden shuttle clacks, a thread zip and a soft beater thunk')
def loom_weave():
    out = S.zeros(0.9)
    # the shuttle clacking into its boxes
    for t0, f0, v in ((0.0, 640.0, 0.85), (0.085, 560.0, 0.75), (0.17, 610.0, 0.95)):
        S.place(out, I.wood(f0, 0.12, 0.05, bright=0.85, click_amt=0.5) * 0.6 * v, t0)
        S.place(out, I.wood(f0 * 2.3, 0.05, 0.018, bright=0.8, click_amt=0.2) * 0.18 * v, t0 + 0.003)
        S.place(out, I.thump(220, 140, 0.05, 0.006, 0.03) * 0.25 * v, t0)
    # thread zip: a tight, buzzy whizz rising in pitch
    tz, D = 0.29, 0.17
    n = ns(D)
    u = times(n) / D
    pulses = (0.5 + 0.5 * np.cos(TAU * np.cumsum(160 + 260 * u) / S.SR)) ** 6
    zz = S.sweep(S.white(n) * (0.25 + pulses), 'bp', 1800 + 3200 * u, q=1.3)
    S.place(out, zz * env_t(n, [(0, 0), (0.02, 1), (0.14, 0.9), (D, 0)]) * 0.5, tz)
    # the beater settles the weft
    S.place(out, I.wood(200, 0.2, 0.07, bright=0.7, click_amt=0.3) * 0.45, 0.5)
    S.place(out, I.thump(150, 90, 0.12, 0.012, 0.08) * 0.35, 0.5)
    return cut(rv(out, 'room', 0.1), 0.8, 0.15)


@sfx('mine_ore', 'reward', 'Mining ore: two pickaxe-on-rock clinks and a small crumble of pebbles')
def mine_ore():
    out = S.zeros(0.75)
    r = S.rng()
    for t0, f0, v in ((0.0, 2300.0, 0.8), (0.19, 2550.0, 1.0)):
        S.place(out, I.metal(f0, 0.3, 0.17, ratios=(1.0, 1.72, 2.63, 3.9), amps=(1, .6, .4, .2), bright=0.75,
                             click_amt=0.45) * 0.42 * v, t0)
        S.place(out, I.nburst(0.05, hi=3000, t60=0.03, attack=0.0005, color='pink') * 0.6 * v, t0)
        S.place(out, I.nburst(0.12, hi=1600, t60=0.07, attack=0.001, color='pink') * 0.45 * v, t0)   # rock chunk
        S.place(out, I.thump(220, 110, 0.09, 0.008, 0.06) * 0.55 * v, t0)
        S.place(out, I.crackle(0.06, rate=300, lo=1500, hi=6000, env=lambda tt: math.exp(-tt / 0.02)) * 0.4 * v,
                t0 + 0.002)
    # a small crumble: grit, a dull trickle and a few pebbles
    tc = 0.21
    S.place(out, I.crackle(0.32, rate=220, lo=900, hi=5000, env=lambda tt: math.exp(-tt / 0.1)) * 0.95, tc)
    S.place(out, I.nburst(0.22, hi=1500, t60=0.16, attack=0.01, color='pink') * 0.35, tc + 0.01)
    for _ in range(6):
        S.place(out, S.modal(ns(0.05), [(r.uniform(2000, 4500), 1, r.uniform(0.02, 0.04))]) * r.uniform(0.08, 0.18),
                tc + r.uniform(0.04, 0.3))
    return cut(rv(out, 'room', 0.1), 0.6, 0.15)


@sfx('herb_pick', 'reward', 'Herb pick: leafy rustle and a soft pluck-pop')
def herb_pick():
    out = S.zeros(0.5)
    m = ns(0.2)
    crinkle = np.clip(S.smooth_noise(m, 90.0), 0, None) ** 1.5
    rs = S.filt(S.white(m) * crinkle, lambda f: S.H_bp(f, 3300, 0.7) * S.H_lp(f, 8000, 2))
    S.place(out, rs * env_t(m, [(0, 0), (0.025, 1), (0.2, 0)], curve=2) * 0.55, 0)
    k = ns(0.14)
    leaf = S.filt(S.pink(k) * 3, lambda f: S.H_bp(f, 1300, 0.9))
    S.place(out, leaf * env_t(k, [(0, 0), (0.02, 1), (0.14, 0)], curve=3) * 0.3, 0.01)
    # the stem snaps and the sprig pops free
    tp = 0.14
    S.place(out, I.click(0.003, 2600, 0.8) * 0.35, tp)
    S.place(out, I.wood(950, 0.05, 0.02, bright=0.8, click_amt=0.2) * 0.18, tp)
    n = ns(0.1)
    t = times(n)
    f = 230 * np.exp(np.log(640 / 230) * np.clip(t / 0.03, 0, 1))
    S.place(out, (S.sine(f, n) + 0.2 * S.sine(2 * f, n)) * S.decay(n, 0.08, attack=0.002) * 0.5, tp + 0.004)
    S.place(out, I.thump(170, 95, 0.06, 0.01, 0.04) * 0.3, tp)
    S.place(out, I.bell(hz('G6'), 0.25, 'marimba', t60=0.18, vel=0.5, mallet=0.05) * 0.1, tp + 0.02)
    return cut(rv(out, 'room', 0.08), 0.4, 0.1)


# ===========================================================================
# movement
# ===========================================================================

def footstep_grass(i):
    r = S.rng()
    out = S.zeros(0.26)
    for t0, a, ln in ((0.0, 1.0, 0.07), (r.uniform(0.045, 0.07), 0.7, 0.09)):
        n = ns(ln)
        t = times(n)
        env = np.clip(t / 0.006, 0, 1) * np.exp(-t / (ln * 0.35))
        fc = r.uniform(2200, 3400)
        nz = S.filt(S.white(n), lambda f: S.H_bp(f, fc, 0.6) * S.H_hp(f, 400, 2)) * env
        S.place(out, nz * a, t0)
    S.place(out, I.crackle(0.16, rate=320, lo=2500, hi=8000, size=(0.0003, 0.0015),
                           env=lambda tt: math.exp(-tt / 0.07)) * 0.45, 0.005)
    S.place(out, I.thump(110, 70, 0.08, 0.01, 0.06) * 0.4, 0)
    return S.lp(out, 7000)


def footstep_stone(i):
    r = S.rng()
    out = S.zeros(0.24)
    f0 = r.uniform(190, 250)
    # heel: dull thud (filtered noise + damped body) and a crisp hard-sole click
    S.place(out, I.nburst(0.05, hi=900, t60=0.035, attack=0.0005, color='pink') * 0.9, 0)
    S.place(out, S.modal(ns(0.08), [(f0, 1.0, 0.028), (f0 * 2.6, 0.4, 0.02), (f0 * 4.1, 0.2, 0.015)]) * 0.6, 0)
    S.place(out, I.click(0.004, r.uniform(2800, 3800), 0.8) * 1.3, 0)
    toe_t = r.uniform(0.04, 0.06)
    S.place(out, I.nburst(0.03, hi=1500, t60=0.02, attack=0.0005, color='pink') * 0.4, toe_t)
    S.place(out, I.click(0.003, r.uniform(3500, 4500), 0.8) * 0.7, toe_t)
    S.place(out, I.crackle(0.05, rate=400, lo=3000, hi=8000, env=lambda tt: math.exp(-tt / 0.02)) * 0.3,
            toe_t + 0.003)
    return out


for _i in range(4):
    sfx('footstep_grass_%d' % (_i + 1), 'step_grass',
        'Soft grass crunch footstep, variant %d' % (_i + 1))(lambda i=_i: footstep_grass(i))
    sfx('footstep_stone_%d' % (_i + 1), 'step_stone',
        'Hard heel-toe tap on stone, variant %d' % (_i + 1))(lambda i=_i: footstep_stone(i))


@sfx('jump', 'move', 'Cloth whoosh with a light springy hop tone')
def jump():
    out = S.zeros(0.4)
    S.place(out, I.whoosh(0.22, 500, 2200, q=0.9, peak=0.35) * 0.7, 0)
    n = ns(0.16)
    t = times(n)
    f = 260 * np.exp(np.log(560 / 260) * np.clip(t / 0.12, 0, 1))
    tone = (S.sine(f, n) + 0.2 * S.sine(2 * f, n)) * S.adsr(n, 0.01, 0.05, 0.6, 0.06, gate=0.09)
    S.place(out, tone * 0.4, 0.01)
    S.place(out, I.nburst(0.05, lo=300, hi=3000, t60=0.04) * 0.4, 0)
    return S.lp(out, 4000)


@sfx('land', 'move', 'Soft body thud with a puff of dust')
def land():
    out = S.zeros(0.45)
    S.place(out, I.thump(120, 45, 0.3, 0.025, 0.2), 0)
    S.place(out, I.nburst(0.25, hi=1500, t60=0.18, color='pink', attack=0.002) * 0.6, 0)
    S.place(out, I.crackle(0.12, rate=120, lo=1500, hi=6000) * 0.4, 0.005)
    S.place(out, I.whoosh(0.15, 1500, 600, q=0.8, peak=0.2) * 0.25, 0)
    return out


# ===========================================================================
# spells
# ===========================================================================

@sfx('spell_arcane_cast', 'spell', 'Violet shimmer swell released with a crystal ping and a trailing whoosh')
def spell_arcane_cast():
    D = 0.18
    out = S.zeros(1.6)
    n = ns(D + 0.12)
    t = times(n)
    f = 330 * 2 ** np.clip(t / D, 0, 1)
    env = np.sin(0.5 * np.pi * np.clip(t / D, 0, 1)) ** 2 * np.where(t < D, 1.0, np.exp(-(t - D) / 0.04))
    tone = (S.harm(f, n, bright=3.0) + 0.6 * S.harm(f * 1.5, n, bright=2.5) + 0.5 * S.tri(f * 2, n)) * env
    S.place(out, S.chorus(tone, 3, base_ms=12, depth_ms=3, rate=1.3, mix=0.6) * 0.35, 0)
    S.place(out, I.whoosh(D + 0.06, 600, 5000, q=1.4, peak=0.85, curve=1.5) * 0.5, 0)
    S.place(out, I.sparkle(D + 0.05, 90, 2500, 9000, root=74, rise=1.0) * 0.3, 0)
    S.place(out, I.bell(hz('A6'), 1.0, 'crystal', t60=0.8) * 0.45, D)
    S.place(out, I.bell(hz('E7'), 0.8, 'crystal', t60=0.6, vel=0.7) * 0.2, D + 0.005)
    S.place(out, I.thump(300, 90, 0.2, 0.02, 0.12) * 0.5, D)
    S.place(out, I.whoosh(0.45, 3500, 900, q=1.0, peak=0.08) * 0.45, D)
    S.place(out, I.sparkle(0.6, 40, 3000, 9000, root=74, rise=-0.5, env=lambda tt: math.exp(-tt / 0.2)) * 0.25, D)
    return rv(out, 'magic', 0.3)


@sfx('spell_arcane_hit', 'spell', 'Arcane impact: soft boom, crystal shatter and falling glitter')
def spell_arcane_hit():
    out = S.zeros(1.6)
    S.place(out, I.thump(180, 55, 0.4, 0.025, 0.3), 0)
    r = S.rng()
    modes = [(r.uniform(1500, 7000), r.uniform(0.3, 1.0), r.uniform(0.08, 0.45)) for _ in range(14)]
    S.place(out, S.modal(ns(0.6), modes) * 0.25, 0)
    S.place(out, I.nburst(0.12, lo=2000, hi=10000, t60=0.08) * 0.5, 0)
    S.place(out, I.sparkle(0.8, 50, 2500, 9000, root=74, rise=-1.0, env=lambda tt: math.exp(-tt / 0.3)) * 0.4, 0.01)
    n = ns(0.45)
    t = times(n)
    f = 880 * 2 ** (-2 * np.clip(t / 0.35, 0, 1))
    sw = (S.tri(f, n) + 0.5 * S.tri(f * 1.5, n)) * S.decay(n, 0.45, attack=0.003)
    S.place(out, S.chorus(sw, 3, rate=2.0, depth_ms=4, mix=0.6) * 0.35, 0)
    return rv(out, 'magic', 0.28)


@sfx('spell_fireball_cast', 'spell', 'Fiery fwoosh with crackle as a fireball launches')
def spell_fireball_cast():
    n = ns(1.0)
    t = times(n)
    fc = lambda tt: 900 + 3200 * np.clip(tt / 0.1, 0, 1) * np.exp(-np.maximum(tt - 0.1, 0) / 0.35)
    body = S.sweep(S.pink(n) * 4, 'lp', fc)
    out = body * np.clip(t / 0.03, 0, 1) ** 2 * np.exp(-np.maximum(t - 0.06, 0) / 0.28)
    S.place(out, I.crackle(0.8, rate=90, lo=1500, hi=6500, env=lambda tt: math.exp(-tt / 0.35)) * 1.2, 0.02)
    S.place(out, I.thump(110, 50, 0.3, 0.04, 0.2) * 0.6, 0)
    S.place(out, I.whoosh(0.7, 900, 350, q=1.2, peak=0.25) * 0.6, 0.08)
    return rv(out, 'room', 0.15)


@sfx('explosion_fire', 'spell', 'Fiery boom: roaring burst with a crackling, smouldering tail')
def explosion_fire():
    out = S.zeros(2.4)
    n = ns(2.4)
    t = times(n)
    S.place(out, I.nburst(0.02, lo=800, t60=0.015), 0)
    S.place(out, S.drive(I.thump(75, 32, 1.4, 0.08, 1.0), 1.8), 0)
    body = S.sweep(S.pink(n) * 4, 'lp', lambda tt: 300 + 4500 * np.exp(-np.maximum(tt, 0) / 0.25))
    S.place(out, body * np.clip(t / 0.008, 0, 1) * np.exp(-t / 0.45) * 0.9, 0)
    S.place(out, I.crackle(2.0, rate=70, lo=1200, hi=6000, env=lambda tt: math.exp(-tt / 0.7)), 0.05)
    S.place(out, I.whoosh(1.4, 1200, 300, q=0.8, peak=0.1) * 0.5, 0.02)
    return rv(out, 'big', 0.25)


@sfx('spell_lightning', 'spell', 'Crackling charge, sharp electric crack and rolling thunder')
def spell_lightning():
    out = S.zeros(2.2)
    k = ns(0.12)
    S.place(out, I.zap(0.12, 150, 0.3, 800, 8000, 2.0, sizzle=0.8) * np.linspace(0, 1, k) ** 2 * 0.4, 0)
    t0 = 0.1
    S.place(out, I.nburst(0.03, lo=1800, t60=0.025) * 1.3, t0)
    S.place(out, I.zap(0.45, 95, 0.4, 250, 7000, 3.5, sizzle=0.6) * S.decay(ns(0.45), 0.45, attack=0.002) * 0.8, t0)
    S.place(out, I.crackle(0.5, rate=200, lo=2500, hi=9000, env=lambda tt: math.exp(-tt / 0.15)) * 0.6, t0)
    n = ns(1.6)
    tt = times(n)
    th = S.lp(S.brown(n) * 4, 260) * (1 + 0.6 * S.smooth_noise(n, 6)) * np.clip(tt / 0.05, 0, 1) * np.exp(-tt / 0.6)
    S.place(out, th * 0.9, t0 + 0.05)
    S.place(out, I.thump(90, 35, 0.6, 0.05, 0.5) * 0.6, t0)
    return rv(out, 'big', 0.2)


@sfx('spell_heal', 'spell', 'Soothing harp glissando, warm glassy pad and rising sparkles', gain=-1.5)
def spell_heal():
    out = S.zeros(2.8)
    for k, nm in enumerate(['C5', 'D5', 'E5', 'G5', 'A5', 'C6', 'D6', 'E6', 'G6']):
        S.place(out, I.pluck(hz(nm), 1.5, 'harp', vel=0.6 + 0.04 * k) * 0.6, 0.04 * k)
    chord = sum(I.pad(hz(nm), 1.0, 'glass', attack=0.35, release=1.0, bright=2.0) for nm in ['C4', 'E4', 'G4', 'D5'])
    S.place(out, S.chorus(chord, 3, rate=0.7, mix=0.6) * 0.5, 0.05)
    S.place(out, I.sparkle(1.8, 35, 3000, 10000, root=72, rise=1.0,
                           env=lambda tt: math.sin(math.pi * min(tt / 1.8, 1.0))) * 0.3, 0.1)
    S.place(out, I.whoosh(1.0, 800, 4000, q=0.8, peak=0.5) * 0.15, 0.0)
    return rv(out, 'magic', 0.3)


@sfx('mana_empty', 'spell', 'Fizzle: sputtering puff and a sad descending bwomp')
def mana_empty():
    out = S.zeros(0.9)
    S.place(out, I.nburst(0.12, lo=600, hi=5000, t60=0.1, attack=0.01) * 0.4, 0)
    for k, t0 in enumerate((0.03, 0.09, 0.16, 0.22)):
        S.place(out, I.crackle(0.04, rate=400, lo=2000, hi=7000) * (0.7 - 0.15 * k), t0)
    n = ns(0.45)
    t = times(n)
    f = hz('E4') * 2 ** (-(4 / 12) * np.clip((t - 0.12) / 0.2, 0, 1))
    b = S.harm(f, n, bright=1.6, kind='square', even=0.2) * S.adsr(n, 0.01, 0.1, 0.7, 0.12, gate=0.3)
    S.place(out, S.lp(b, 1200) * 0.7, 0.08)
    return rv(out, 'room', 0.15)


# ===========================================================================
# weapons
# ===========================================================================

@sfx('gun_arc_pistol', 'weapon', 'Retro ray-gun zap: resonant falling pew with electric crackle')
def gun_arc_pistol():
    out = S.zeros(0.6)
    n = ns(0.3)
    t = times(n)
    f = 250 + 1700 * np.exp(-t / 0.045)
    src = S.square(f, n, pw=0.3) * S.decay(n, 0.28, attack=0.0008)
    y = S.svf(src, 900 + 6000 * np.exp(-t / 0.05), q=3.0, mode='lp')
    S.place(out, y * 0.8, 0)
    S.place(out, I.zap(0.08, 140, 0.4, 1500, 9000, 2.5) * S.decay(ns(0.08), 0.08) * 0.4, 0)
    S.place(out, I.thump(200, 70, 0.15, 0.015, 0.1) * 0.6, 0)
    S.place(out, I.click(0.003, 5000, 0.7) * 0.8, 0)
    return rv(out, 'room', 0.12)


@sfx('gun_rivet', 'weapon', 'Pneumatic rivet shot: punchy chuk, metal ting and action clack')
def gun_rivet():
    out = S.zeros(0.4)
    S.place(out, I.thump(150, 65, 0.15, 0.012, 0.08), 0)
    S.place(out, I.nburst(0.05, fc=1300, q=0.7, t60=0.03, attack=0.0005) * 1.4, 0)
    S.place(out, I.nburst(0.02, lo=3000, t60=0.012) * 0.5, 0)
    S.place(out, S.modal(ns(0.2), [(2900, 1, 0.12), (4650, 0.6, 0.08), (6950, 0.3, 0.05)]) * 0.25, 0.004)
    S.place(out, I.metal(1600, 0.1, 0.05, bright=0.7, click_amt=0.5) * 0.35, 0.045)
    return rv(out, 'room', 0.12)


@sfx('gun_mortar', 'weapon', 'Hollow tube thoomp of the hand mortar')
def gun_mortar():
    out = S.zeros(1.0)
    S.place(out, S.drive(I.thump(140, 45, 0.6, 0.03, 0.35), 1.6), 0)
    S.place(out, I.nburst(0.06, hi=900, t60=0.05, attack=0.001, color='pink') * 0.8, 0)
    S.place(out, I.nburst(0.15, fc=330, q=5, t60=0.12, attack=0.003), 0.003)
    S.place(out, I.metal(420, 0.5, 0.3, bright=0.6, click_amt=0.1) * 0.15, 0.01)
    S.place(out, I.whoosh(0.4, 1500, 600, q=1.0, peak=0.15) * 0.25, 0.02)
    return rv(out, 'room', 0.15)


@sfx('explosion_big', 'weapon', 'Big boom: sub thump, crunchy blast, rumble and scattered debris')
def explosion_big():
    out = S.zeros(3.2)
    n = ns(2.6)
    t = times(n)
    S.place(out, I.nburst(0.025, lo=600, t60=0.02) * 1.2, 0)
    S.place(out, S.drive(I.thump(65, 26, 2.2, 0.1, 1.6), 2.0), 0)
    mid = S.sweep(S.drive(S.pink(n) * 4, 2.5), 'lp', lambda tt: 350 + 6000 * np.exp(-np.maximum(tt, 0) / 0.2))
    S.place(out, mid * np.clip(t / 0.004, 0, 1) * np.exp(-t / 0.5) * 0.8, 0)
    rum = S.lp(S.brown(n) * 4, 140) * (1 + 0.5 * S.smooth_noise(n, 4)) * np.clip(t / 0.05, 0, 1) * np.exp(-t / 0.9)
    S.place(out, rum * 0.9, 0)
    r = S.rng()
    for _ in range(10):
        td = r.uniform(0.3, 1.9)
        kind = r.integers(3)
        if kind == 0:
            d = I.wood(r.uniform(250, 600), 0.2, 0.06)
        elif kind == 1:
            d = I.metal(r.uniform(900, 2200), 0.3, 0.15, bright=0.6, click_amt=0.2)
        else:
            d = I.nburst(0.05, lo=1500, hi=6000, t60=0.03)
        S.place(out, d * r.uniform(0.04, 0.12) * math.exp(-td / 1.2), td)
    return rv(out, 'big', 0.25)


@sfx('reload', 'weapon', 'Mechanical reload: release click, mag out, clack in, bolt cha-chk')
def reload():
    out = S.zeros(1.0)
    S.place(out, I.metal(2200, 0.08, 0.03, bright=0.6, click_amt=0.6) * 0.5, 0.0)
    S.place(out, I.whoosh(0.09, 3000, 1800, q=2.0, peak=0.3) * 0.25, 0.04)
    S.place(out, I.wood(240, 0.15, 0.05) * 0.3, 0.30)
    S.place(out, I.metal(950, 0.2, 0.08, bright=0.65, click_amt=0.6) * 0.6, 0.30)
    S.place(out, I.nburst(0.06, fc=1800, q=1.2, t60=0.04) * 0.4, 0.55)
    S.place(out, I.metal(1250, 0.15, 0.07, bright=0.6, click_amt=0.4) * 0.4, 0.56)
    S.place(out, I.metal(2600, 0.15, 0.06, bright=0.7, click_amt=0.8) * 0.55, 0.68)
    S.place(out, I.thump(260, 120, 0.06, 0.01, 0.04) * 0.4, 0.68)
    return rv(out, 'room', 0.1)


@sfx('gun_scatter', 'weapon', 'Brass blunderbuss: big punchy boom, brassy barrel ring and a short pellet rattle')
def gun_scatter():
    out = S.zeros(0.9)
    S.place(out, S.drive(I.thump(125, 40, 0.6, 0.028, 0.32), 1.8), 0.002)
    S.place(out, I.nburst(0.03, lo=900, t60=0.02, attack=0.0004) * 0.8, 0)
    n = ns(0.35)
    t = times(n)
    blast = S.sweep(S.drive(S.pink(n) * 4, 2.2), 'lp', lambda tt: 350 + 5000 * np.exp(-np.maximum(tt, 0) / 0.05))
    S.place(out, S.fade(blast * np.clip(t / 0.002, 0, 1) * np.exp(-t / 0.08), 0.0, 0.05) * 0.9, 0)
    S.place(out, I.metal(620, 0.6, 0.55, ratios=(1.0, 2.02, 2.97, 4.1, 5.3), amps=(1, .7, .5, .32, .18),
                         bright=0.8, click_amt=0.0) * 0.32, 0.004)
    r = S.rng()
    K = 14
    for k in range(K):
        f0 = r.uniform(2200, 4800)
        tk = S.modal(ns(0.06), [(f0, 1.0, r.uniform(0.02, 0.05)), (f0 * 1.53, 0.5, 0.02)])
        S.place(tk, I.click(0.002, 5000, 0.8) * 0.3, 0)
        S.place(out, tk * r.uniform(0.08, 0.2) * (1 - 0.6 * k / K), 0.05 + 0.3 * (k / K) ** 1.4 + r.uniform(-0.01, 0.01))
    return rv(out, 'room', 0.14)


@sfx('scatter_pump', 'weapon', 'Blunderbuss pump: two-stage clack-chunk of the slide racking back and forward')
def scatter_pump():
    out = S.zeros(0.4)
    # back: a short slide 'shk' that stops in a bright clack
    S.place(out, I.nburst(0.04, fc=1800, q=1.2, t60=0.035, attack=0.012) * 0.2, 0.0)
    S.place(out, I.metal(2100, 0.08, 0.04, bright=0.65, click_amt=0.7) * 0.6, 0.03)
    S.place(out, I.nburst(0.03, fc=2400, q=1.0, t60=0.02) * 0.45, 0.03)
    S.place(out, I.wood(380, 0.06, 0.03, bright=0.8, click_amt=0.3) * 0.3, 0.03)
    # forward: slide, then a heavier, lower chunk as it locks
    S.place(out, I.nburst(0.04, fc=1500, q=1.2, t60=0.035, attack=0.012) * 0.18, 0.12)
    S.place(out, I.metal(900, 0.12, 0.06, bright=0.6, click_amt=0.6) * 0.6, 0.155)
    S.place(out, I.thump(240, 110, 0.09, 0.012, 0.05) * 0.7, 0.155)
    S.place(out, I.wood(200, 0.1, 0.045, bright=0.7, click_amt=0.3) * 0.35, 0.155)
    S.place(out, I.nburst(0.04, fc=1300, q=0.9, t60=0.03) * 0.5, 0.155)
    return cut(rv(out, 'room', 0.08), 0.4, 0.12)


@sfx('lance_charge', 'weapon',
     'Tesla Lance charging: rising electric whine and quickening crackle, peaking in a bright high tone', gain=-3.0)
def lance_charge():
    D = 1.2
    out = S.zeros(D + 0.3)
    n = ns(D)
    t = times(n)
    u = t / D
    rise = np.clip(t / 1.0, 0, 1)
    f = 110.0 * 2 ** (3.0 * (1 - (1 - rise) ** 1.6))          # 110 -> 880 Hz, easing into the top
    B = 1.5 + 3.5 * u
    whine = S.harm(f, n, bright=B, kind='square', even=0.3) * 0.5 + S.sine(2 * f, n) * 0.45 * u ** 1.5 \
        + S.sine(3 * f, n) * 0.12 * u ** 3
    rate = 7 + 23 * u ** 1.5                                   # pulsing speeds up as it charges
    whine *= 0.72 + 0.28 * np.sin(TAU * np.cumsum(rate) / S.SR)
    env = env_t(n, [(0, 0), (0.05, 0.3), (1.0, 1.0), (1.08, 1.0), (1.18, 0)])
    S.place(out, whine * env, 0)
    S.place(out, I.zap(D, f / 2, 0.3, 400, 7000, 2.0, sizzle=0.6) * env * u * 0.35, 0)
    cr = I.crackle(D, rate=420, lo=2000, hi=8000, size=(0.0005, 0.003), env=lambda tt: 0.15 + 0.85 * (tt / D) ** 1.5)
    S.place(out, cr * env_t(n, [(0, 0.6), (1.0, 1.0), (1.08, 1.0), (1.18, 0)]) * 1.6, 0)
    r = S.rng()
    for _ in range(14):                                        # little arcs, more of them near the top
        ta = 1.1 * r.uniform() ** 0.6
        d = r.uniform(0.03, 0.06)
        arc = I.zap(d, r.uniform(150, 300), 0.4, 800, 7000, 3.0, sizzle=0.8) * S.decay(ns(d), d, attack=0.002)
        S.place(out, arc * r.uniform(0.15, 0.35) * (0.4 + 0.6 * ta / 1.1), ta)
    return cut(rv(S.lp(out, 9000), 'room', 0.1), 1.3, 0.12)


@sfx('lance_fire', 'weapon', 'Tesla Lance shot: thunderous zap-boom with a crackly sizzle tail')
def lance_fire():
    out = S.zeros(1.2)
    S.place(out, I.nburst(0.025, lo=1500, t60=0.02, attack=0.0003) * 0.5, 0)
    n = ns(0.45)
    t = times(n)
    S.place(out, I.zap(0.45, 60 + 500 * np.exp(-t / 0.05), 0.35, 200, 8000, 3.0, sizzle=0.6)
            * S.decay(n, 0.5, attack=0.004), 0.002)
    m = ns(0.18)
    tm = times(m)
    src = S.square(120 + 1500 * np.exp(-tm / 0.03), m, pw=0.3) * S.decay(m, 0.18, attack=0.0008)
    S.place(out, S.svf(src, 600 + 5000 * np.exp(-tm / 0.04), q=3.0, mode='lp') * 0.5, 0)
    S.place(out, S.drive(I.thump(105, 36, 0.7, 0.035, 0.5), 1.8) * 0.9, 0.004)
    k = ns(0.8)
    tk = times(k)
    th = S.lp(S.brown(k) * 4, 240) * (1 + 0.5 * S.smooth_noise(k, 8)) * np.clip(tk / 0.03, 0, 1) * np.exp(-tk / 0.25)
    S.place(out, S.fade(th, 0.0, 0.15) * 0.65, 0.01)
    S.place(out, I.crackle(0.7, rate=240, lo=2500, hi=9000, env=lambda tt: math.exp(-tt / 0.25)) * 0.8, 0.02)
    j = ns(0.7)
    gate = (S.smooth_noise(j, 90) > 0.4) * 1.0
    sz = S.filt(S.white(j) * gate, lambda f: S.H_bp(f, 5000, 0.7)) * np.exp(-times(j) / 0.2)
    S.place(out, S.fade(sz, 0.0, 0.1) * 0.3, 0.04)
    return rv(S.lp(out, 10000), 'room', 0.15)


@sfx('wrench_swing', 'weapon', 'Heavy wrench swing: low, airy whoosh', gain=-4.0)
def wrench_swing():
    D = 0.3
    n = ns(D)
    u = times(n) / D
    pk = 0.55
    hump = np.where(u < pk, np.sin(0.5 * np.pi * u / pk) ** 2,
                    np.cos(0.5 * np.pi * np.clip((u - pk) / (1 - pk), 0, 1)) ** 2)
    air = S.sweep(S.pink(n) * 4, 'bp', lambda tt: 380 + 700 * np.sin(np.pi * np.clip(tt / D, 0, 1)) ** 1.5, q=0.9)
    low = S.lp(S.brown(n) * 4, 220)
    return (air * 0.8 + low * 0.5 * hump) * hump


@sfx('wrench_hit', 'weapon', 'Shock wrench hit: heavy metal clang with an electric zap on top')
def wrench_hit():
    out = S.zeros(0.8)
    S.place(out, I.metal(310, 0.6, 0.4, ratios=(1.0, 2.43, 3.9, 5.6, 7.4), amps=(1, .8, .55, .35, .2),
                         bright=0.8, click_amt=0.5) * 0.7, 0)
    S.place(out, S.drive(I.thump(150, 60, 0.2, 0.012, 0.12), 1.5) * 0.8, 0)
    S.place(out, I.nburst(0.025, lo=800, hi=7000, t60=0.018) * 0.6, 0)
    z = ns(0.25)
    S.place(out, I.zap(0.25, 130, 0.4, 700, 8000, 3.0, sizzle=0.7) * S.decay(z, 0.25, attack=0.002) * 0.9, 0.005)
    S.place(out, I.crackle(0.3, rate=260, lo=2500, hi=9000, env=lambda tt: math.exp(-tt / 0.1)) * 0.7, 0.01)
    m = ns(0.08)
    S.place(out, S.harm(1400 * np.exp(-times(m) / 0.04), m, bright=3) * S.decay(m, 0.08) * 0.3, 0.004)
    return rv(out, 'room', 0.12)


@sfx('bomb_throw', 'weapon', 'Bomb toss: short whoosh with a sputtering, fizzing fuse', gain=-3.0)
def bomb_throw():
    out = S.zeros(0.6)
    S.place(out, I.whoosh(0.3, 450, 1600, q=1.0, peak=0.35) * 0.7, 0)
    n = ns(0.45)
    hiss = S.sweep(S.white(n), 'lp', lambda tt: 9000 - 5000 * np.clip(tt / 0.45, 0, 1))
    hiss = S.filt(hiss, lambda f: S.H_bp(f, 5000, 0.6))
    sput = np.clip(0.55 + 0.45 * S.smooth_noise(n, 35), 0, None)
    S.place(out, hiss * sput * env_t(n, [(0, 0), (0.01, 1), (0.3, 0.75), (0.45, 0)]) * 0.35, 0)
    S.place(out, I.crackle(0.45, rate=160, lo=2000, hi=8000, env=lambda tt: 1 - tt / 0.45) * 0.5, 0)
    return rv(out, 'room', 0.08)


def segment(x, dur, fade, skip=0.15):
    """Window `dur` s of a steady texture x (skipping its first `skip` s, where filters and reverb
    are still settling) with equal-power sine/cosine edges of `fade` s, then pad 50 ms of silence
    so finalize() leaves the edges alone. The half-power points are dur - fade apart, so copies
    re-triggered about that often cross-fade at constant power into one steady sound."""
    n = ns(dur)
    a = ns(skip)
    t = times(n)
    w = np.sin(0.5 * np.pi * np.clip(t / fade, 0, 1)) * np.cos(0.5 * np.pi * np.clip((t - (dur - fade)) / fade, 0, 1))
    return S.pad_to(np.asarray(x[a:a + n], float) * w, n + ns(0.05))


def steady(x, win=0.1):
    """Even out slow loudness drift in a texture (divide by its RMS smoothed over a `win` s Hann
    window). Anything slower than ~1/win inside a re-triggered segment would repeat with every
    copy and be heard as pumping; faster flicker and tremolo survive."""
    w = np.hanning(ns(win))
    p = np.convolve(x * x, w / w.sum(), mode='same')
    return x * np.sqrt(np.median(p) / (p + 1e-12))


def fast_flutter(n, lo=10.0, hi=30.0):
    """Unit-std random flutter with content only between lo and hi Hz (no slow wander)."""
    y = S.filt(S.gauss(n), lambda f: S.H_bp(f, math.sqrt(lo * hi), math.sqrt(lo * hi) / (hi - lo))
               * S.H_hp(f, lo, 4) * S.H_lp(f, hi, 4))
    return y / (np.std(y) + 1e-12)


def tonal_noise(n, partials, sigma=1.6):
    """Held 'tone' whose partials (freq, amp) are narrow Gaussian bands of noise sigma Hz wide.
    It sounds like a shimmering hum, but copies more than ~1/(2 sigma) s apart are uncorrelated
    on average, so overlapping re-triggers add in power instead of beating or cancelling."""
    f = np.fft.rfftfreq(n, 1.0 / S.SR)
    H2 = np.zeros(len(f))
    for fk, a in partials:
        if fk < 0.45 * S.SR:
            H2 += a * a * np.exp(-((f - fk) / sigma) ** 2)
    y = np.fft.irfft(np.fft.rfft(S.gauss(n)) * np.sqrt(H2), n)
    return y / (np.std(y) + 1e-12)


@sfx('gun_longshot', 'weapon',
     'Longshot rifle: sharp crack and punchy boom, a long brassy barrel ring-out and a distant echo')
def gun_longshot():
    shot = S.zeros(0.45)
    S.place(shot, I.nburst(0.012, lo=1800, t60=0.007, attack=0.0002) * 1.1, 0)        # supersonic crack
    S.place(shot, I.click(0.004, 5000, 0.7) * 1.2, 0)
    S.place(shot, S.drive(I.thump(150, 44, 0.45, 0.018, 0.28), 1.8) * 0.95, 0.001)   # boom
    n = ns(0.3)
    t = times(n)
    blast = S.sweep(S.drive(S.pink(n) * 4, 2.0), 'lp', lambda tt: 450 + 6500 * np.exp(-np.maximum(tt, 0) / 0.025))
    S.place(shot, S.fade(blast * np.clip(t / 0.0015, 0, 1) * np.exp(-t / 0.05), 0.0, 0.05) * 0.85, 0)
    out = S.zeros(1.1)
    S.place(out, shot, 0)
    ring = I.metal(940, 1.0, 0.8, ratios=(1.0, 2.01, 3.02, 4.07, 5.16), amps=(1, .55, .4, .26, .14),
                   bright=0.85, click_amt=0.0)
    S.place(out, ring * 0.2, 0.003)
    # distant echo: the shot thrown back off far hills, darker and diffuse
    echo = S.echo(S.lp(shot, 2200), 0.29, fb=0.3, wet=1.0, damp=1500, dry=0.0)
    S.place(out, rv(echo, 'outdoor', 0.8) * 0.22, 0)
    return cut(rv(out, 'room', 0.08), 0.9, 0.25)


@sfx('scope_zoom', 'weapon', 'Scope zoom: small mechanical lens-twist click with a soft whirr', gain=-5.0)
def scope_zoom():
    out = S.zeros(0.32)
    D = 0.17
    n = ns(D)
    env = env_t(n, [(0, 0), (0.025, 1), (0.13, 0.85), (D, 0)])
    # soft whirr: a tiny lens motor gliding up, roughened by its gear teeth
    wh = S.filt(I.servo(D, 820, 1250, wobble=0.008, bright=2.2, rate=9.0),
                lambda f: S.H_bp(f, 1500, 0.7) * S.H_lp(f, 5000, 2))
    wh *= 0.6 + 0.4 * np.sin(TAU * np.cumsum(np.linspace(95.0, 140.0, n)) / S.SR) ** 2
    S.place(out, wh * env * 0.11, 0.012)
    # the knurled ring turning over fine detents
    det = np.zeros(n)
    for k in range(int(D * 62)):
        S.place(det, I.click(0.002, 4300, 0.9), k / 62.0)
    S.place(out, det * env * 0.28, 0.012)
    S.place(out, S.filt(S.pink(n) * 2, lambda f: S.H_bp(f, 2800, 1.0)) * env * 0.12, 0.012)
    # grip click, then the lens clicks home with a tiny glassy glint
    S.place(out, I.metal(3300, 0.05, 0.018, bright=0.6, click_amt=0.4) * 0.32, 0.0)
    S.place(out, I.metal(2500, 0.07, 0.03, bright=0.6, click_amt=0.6) * 0.65, D + 0.012)
    S.place(out, I.wood(1100, 0.05, 0.02, bright=0.8, click_amt=0.25) * 0.35, D + 0.012)
    S.place(out, I.bell(hz('E7'), 0.12, 'crystal', t60=0.09, vel=0.5, mallet=0) * 0.05, D + 0.016)
    return cut(rv(out, 'room', 0.06), 0.26, 0.05)


@sfx('gun_gatling', 'weapon',
     'Gatling shot: one short, punchy rotary-gun tak with a tiny tail, for rapid re-triggering')
def gun_gatling():
    out = S.zeros(0.14)
    S.place(out, S.drive(I.thump(185, 72, 0.09, 0.008, 0.055), 1.7), 0)
    S.place(out, I.nburst(0.04, fc=1450, q=0.7, t60=0.022, attack=0.0004) * 1.3, 0)
    S.place(out, I.nburst(0.015, lo=3000, t60=0.007, attack=0.0002) * 0.45, 0)
    S.place(out, I.click(0.003, 4200, 0.8) * 0.6, 0)
    S.place(out, S.modal(ns(0.07), [(3150, 1.0, 0.045), (4900, 0.5, 0.03)]) * 0.1, 0.002)
    return cut(rv(out, 'room', 0.05), 0.12, 0.04)


@sfx('gatling_spin', 'weapon', 'Gatling spin-up: rising motor whine with the barrels rattling faster and faster')
def gatling_spin():
    D = 0.9
    n = ns(D)
    t = times(n)
    sp = 1.0 - (1.0 - np.clip(t / 0.78, 0, 1)) ** 2.2           # spin speed 0 -> 1, easing into full speed
    env = env_t(n, [(0, 0), (0.05, 0.4), (0.78, 1.0), (D - 0.06, 1.0), (D, 0)])
    out = S.zeros(D + 0.1)
    S.place(out, I.metal(600, 0.15, 0.06, bright=0.6, click_amt=0.4) * 0.25, 0)    # the clutch engages
    S.place(out, I.thump(160, 80, 0.1, 0.01, 0.06) * 0.3, 0)
    # motor whine rising with the speed
    fmot = 150.0 + 330.0 * sp
    whine = S.harm(fmot, n, bright=1.4 + 2.2 * sp, kind='square', even=0.35) + 0.35 * S.sine(2 * fmot, n) * sp
    S.place(out, S.lp(whine, 4500) * env * 0.2, 0)
    # air churned by the barrels, pulsing at the barrel-pass rate
    ph = np.cumsum(6.0 + 34.0 * sp) / S.SR
    air = S.sweep(S.pink(n) * 4, 'bp', 500 + 1500 * sp, q=0.9)
    S.place(out, air * env * (0.7 + 0.3 * np.cos(TAU * ph)) * 0.22, 0)
    # rattle: a clack each time a barrel passes the bolt
    tones = (1750.0, 2150.0, 1900.0, 2350.0, 1820.0, 2050.0)
    for k, i in enumerate(np.nonzero(np.diff(np.floor(ph)) > 0)[0] + 1):
        s = float(sp[i])
        S.place(out, I.metal(tones[k % 6] * (1 + 0.08 * s), 0.05, 0.03 - 0.012 * s, bright=0.6, click_amt=0.4)
                * (0.16 + 0.16 * s), int(i))
        if s < 0.5:
            S.place(out, I.wood(330, 0.06, 0.03, bright=0.8, click_amt=0.2) * 0.14 * (1 - 2 * s), int(i))
    return cut(rv(out, 'room', 0.08), D, 0.06)


@sfx('flamer_burst', 'weapon',
     'Flamer: roaring gas-flame fwoosh segment with equal-power edges; re-triggered every ~0.3 s it blends into '
     'one roar', gain=-3.0)
def flamer_burst():
    m = ns(0.75)
    roar = S.filt(S.pink(m) * 4, lambda f: S.H_lp(f, 2600, 2) * S.H_bell(f, 500, 5.0, 1.6) * S.H_hp(f, 90, 2))
    rumble = S.filt(S.brown(m) * 4, lambda f: S.H_lp(f, 170, 2) * S.H_hp(f, 35, 2))
    jet = S.filt(S.white(m), lambda f: S.H_bp(f, 3800, 0.8) * S.H_lp(f, 9000, 2))
    cr = I.crackle(0.75, rate=170, lo=1800, hi=7000, size=(0.0003, 0.0015))
    x = steady(rv(roar + 0.6 * rumble + 0.08 * jet + 0.4 * cr, 'room', 0.12)[:m])
    x *= 1 + 0.2 * np.tanh(fast_flutter(m, 10.0, 30.0))         # quick flame flicker, no slow wander
    return segment(x, 0.435, 0.12)


@sfx('crossbow_fire', 'weapon', 'Clockwork crossbow shot: taut string twang, wooden thunk and a little clockwork tick')
def crossbow_fire():
    out = S.zeros(0.55)
    # the string lets go: a quick airy thwip as the bolt leaves
    S.place(out, I.whoosh(0.08, 2200, 5500, q=1.1, peak=0.25, color='white') * 0.22, 0)
    # twang: a taut string with a slack pitch drop and a nasal ring
    n = ns(0.42)
    t = times(n)
    f = 150 * (1 + 0.4 * np.exp(-t / 0.01)) * (1 + 0.015 * np.exp(-t / 0.12) * np.sin(TAU * 12 * t))
    tw = S.harm(f, n, bright=4 + 12 * np.exp(-t / 0.02)) * S.decay(n, 0.38, attack=0.0006)
    tw = S.filt(tw, lambda fr: S.H_bell(fr, 950, 7.0, 1.2) * S.H_lp(fr, 6500, 2) * S.H_hp(fr, 100, 2))
    S.place(out, tw * 0.45, 0)
    S.place(out, S.ks_pluck(162, 0.42, t60=0.38, stretch=0.3, bright=7000, pick=0.08) * 0.5, 0)
    # wooden thunk of the limbs slapping their stops
    S.place(out, I.wood(235, 0.2, 0.07, bright=0.8, click_amt=0.15) * 0.6, 0.006)
    S.place(out, I.thump(170, 90, 0.12, 0.012, 0.07) * 0.6, 0.006)
    # clockwork tick-tick as the trigger sear resets
    S.place(out, I.metal(3300, 0.05, 0.02, bright=0.6, click_amt=0.4) * 0.22, 0.12)
    S.place(out, I.metal(2850, 0.05, 0.02, bright=0.6, click_amt=0.4) * 0.17, 0.165)
    return cut(rv(out, 'room', 0.1), 0.45, 0.12)


@sfx('crossbow_reload', 'weapon', 'Crossbow reload: ratcheting clockwork crank clicks ending in a latch clack')
def crossbow_reload():
    out = S.zeros(0.85)
    r = S.rng()
    # winding: the crank turning against the string's rising tension
    n = ns(0.48)
    t = times(n)
    wind = S.filt(S.pink(n) * 3, lambda f: S.H_bp(f, 1100, 1.0)) * (0.55 + 0.45 * np.sin(TAU * 8.0 * t) ** 2)
    S.place(out, wind * env_t(n, [(0, 0), (0.04, 1), (0.42, 0.8), (0.48, 0)]) * 0.07, 0.02)
    cr = creak(0.45, 62, 105, rough=0.08)
    S.place(out, cr * env_t(len(cr), [(0, 0), (0.06, 1), (0.38, 0.8), (0.45, 0)]) * 0.18, 0.03)
    # ratchet: the pawl clicking over the gear teeth, tightening as it winds
    for k in range(8):
        tc = 0.03 + 0.057 * k + r.uniform(-0.004, 0.004)
        S.place(out, I.metal((2250 + 55 * k) * r.uniform(0.97, 1.03), 0.06, 0.028, bright=0.6, click_amt=0.5)
                * (0.3 + 0.03 * k), tc)
        S.place(out, I.wood(500 + 14 * k, 0.05, 0.022, bright=0.8, click_amt=0.2) * 0.22, tc)
    # latch clack as the string locks
    tl = 0.55
    S.place(out, I.metal(1050, 0.15, 0.07, bright=0.65, click_amt=0.6) * 0.6, tl)
    S.place(out, I.wood(320, 0.12, 0.06, bright=0.8, click_amt=0.4) * 0.55, tl)
    S.place(out, I.thump(260, 120, 0.09, 0.01, 0.06) * 0.6, tl)
    S.place(out, I.nburst(0.04, fc=1500, q=0.9, t60=0.03) * 0.35, tl)
    return cut(rv(out, 'room', 0.08), 0.72, 0.12)


@sfx('hammer_slam', 'weapon', 'Steam hammer slam: huge piston thud, a heavy metallic clang and a hissing steam tail')
def hammer_slam():
    out = S.zeros(1.2)
    # piston thud
    S.place(out, S.drive(I.thump(92, 32, 0.8, 0.035, 0.5), 2.0), 0)
    S.place(out, I.nburst(0.03, lo=600, hi=7000, t60=0.02, attack=0.0004) * 0.7, 0)
    S.place(out, I.nburst(0.16, fc=230, q=3.5, t60=0.12, attack=0.002) * 0.9, 0.002)      # hollow cylinder
    n = ns(0.3)
    t = times(n)
    body = S.sweep(S.drive(S.pink(n) * 4, 2.0), 'lp', lambda tt: 300 + 3200 * np.exp(-np.maximum(tt, 0) / 0.04))
    S.place(out, S.fade(body * np.clip(t / 0.002, 0, 1) * np.exp(-t / 0.07), 0.0, 0.05) * 0.75, 0)
    # clang of the steel head
    S.place(out, I.metal(235, 0.9, 0.6, ratios=(1.0, 2.43, 3.9, 5.6, 7.4), amps=(1, .8, .55, .35, .2),
                         bright=0.8, click_amt=0.5) * 0.5, 0.002)
    S.place(out, I.metal(1180, 0.5, 0.3, bright=0.7, click_amt=0.2) * 0.12, 0.004)
    # steam venting from the piston
    m = ns(0.8)
    hs = S.sweep(I.hiss(0.8, 2200, 10000, 0.25, 22), 'lp', lambda tt: 10000 - 5500 * np.clip(tt / 0.8, 0, 1))
    S.place(out, hs * env_t(m, [(0, 0), (0.025, 1), (0.25, 0.7), (0.8, 0)], curve=1.5) * 0.55, 0.07)
    return cut(rv(out, 'room', 0.13), 0.95, 0.25)


# ---------------------------------------------------------------------------
# magic weapons
# ---------------------------------------------------------------------------

@sfx('wand_ember', 'spell', 'Ember wand: quick fiery whoosh-pop with a spray of sparks')
def wand_ember():
    out = S.zeros(0.45)
    n = ns(0.2)
    fire = S.sweep(S.pink(n) * 4, 'lp', lambda tt: 700 + 3800 * np.clip(tt / 0.07, 0, 1) ** 1.5)
    S.place(out, fire * env_t(n, [(0, 0), (0.07, 1), (0.2, 0)], curve=1.5) * 0.7, 0)
    S.place(out, I.whoosh(0.12, 500, 2600, q=1.1, peak=0.75) * 0.45, 0)
    tp = 0.075                                                   # the ember pops off the wand tip
    m = ns(0.09)
    tm = times(m)
    f = 320 * np.exp(np.log(1100 / 320) * np.clip(tm / 0.025, 0, 1))
    pop = (S.sine(f, m) + 0.3 * S.harm(f, m, bright=1.5, kind='square')) * S.decay(m, 0.07, attack=0.0015)
    S.place(out, pop * 0.55, tp)
    S.place(out, I.thump(260, 110, 0.08, 0.01, 0.05) * 0.4, tp)
    S.place(out, I.click(0.003, 3500, 0.8) * 0.5, tp)
    S.place(out, I.crackle(0.3, rate=150, lo=2000, hi=8000, env=lambda tt: math.exp(-tt / 0.1)) * 0.9, tp)
    S.place(out, I.sparkle(0.2, 40, 3000, 8000, root=69, env=lambda tt: math.exp(-tt / 0.07)) * 0.18, tp + 0.01)
    return cut(rv(out, 'room', 0.12), 0.32, 0.1)


@sfx('wand_frost', 'spell', 'Frost wand: icy crystalline chime (stacked fifths) with a crisp frosty crackle')
def wand_frost():
    out = S.zeros(0.6)
    S.place(out, I.nburst(0.04, lo=4500, hi=12000, t60=0.03, attack=0.0005) * 0.35, 0)
    S.place(out, I.whoosh(0.18, 6000, 2800, q=0.9, peak=0.12, color='white') * 0.2, 0)
    S.place(out, I.thump(420, 220, 0.05, 0.006, 0.03) * 0.25, 0)
    for k, (nm, dt) in enumerate((('E6', 0.0), ('B6', 0.022), ('F#7', 0.045))):
        S.place(out, I.bell(hz(nm), 0.45, 'crystal', t60=0.32 - 0.04 * k, vel=0.85, mallet=0.12) * (0.42 - 0.08 * k),
                dt)
    r = S.rng()
    modes = [(r.uniform(3000, 8000), r.uniform(0.3, 1.0), r.uniform(0.04, 0.15)) for _ in range(8)]
    S.place(out, S.modal(ns(0.2), modes) * 0.1, 0)
    S.place(out, I.crackle(0.35, rate=550, lo=3500, hi=10000, size=(0.0002, 0.0008),
                           env=lambda tt: math.exp(-tt / 0.1)) * 0.55, 0.02)
    S.place(out, I.sparkle(0.3, 45, 4000, 10000, root=76, env=lambda tt: math.exp(-tt / 0.1)) * 0.15, 0.03)
    return cut(rv(S.lp(out, 11000), 'magic', 0.14), 0.42, 0.14)


@sfx('tome_cast', 'spell', 'Tome cast: riffling pages flutter into a soft swirl of rising magical tones')
def tome_cast():
    out = S.zeros(0.9)
    r = S.rng()
    # page flutter: a quick riffle of paper flaps
    for k in range(10):
        m = ns(0.045)
        tm = times(m)
        fc = r.uniform(2000, 3800)
        flap = S.filt(S.white(m), lambda f: S.H_bp(f, fc, 0.8) * S.H_hp(f, 700, 2)) \
            + 0.6 * S.filt(S.pink(m) * 3, lambda f: S.H_bp(f, 700, 1.0))
        env = np.clip(tm / 0.003, 0, 1) * np.exp(-tm / 0.012)
        S.place(out, flap * env * (0.55 - 0.035 * k) * r.uniform(0.7, 1.0), 0.021 * k + r.uniform(0, 0.004))
    # swirl: a glassy voice gliding up an octave with a circling vibrato, over a rising celesta run
    ts = 0.12
    n = ns(0.55)
    t = times(n)
    f = hz('D5') * 2 ** (np.clip(t / 0.4, 0, 1) ** 0.8) * (1 + 0.012 * np.sin(TAU * 7 * t))
    sw = (S.sine(f, n) + 0.35 * S.sine(2 * f, n) + 0.25 * S.tri(1.5 * f, n)) \
        * env_t(n, [(0, 0), (0.12, 1), (0.35, 0.8), (0.55, 0)], curve=1.0)
    S.place(out, S.chorus(sw, 3, base_ms=12, depth_ms=3, rate=1.6, mix=0.6) * 0.16, ts)
    for k, nm in enumerate(('D5', 'F#5', 'A5', 'D6', 'E6', 'A6')):
        S.place(out, I.bell(hz(nm), 0.5, 'celesta', t60=0.4, vel=0.6 + 0.05 * k, mallet=0.08) * 0.22, ts + 0.045 * k)
    S.place(out, I.sparkle(0.45, 45, 2500, 8000, root=74, rise=1.0,
                           env=lambda tt: math.sin(math.pi * min(tt / 0.45, 1.0))) * 0.22, ts)
    S.place(out, I.whoosh(0.35, 700, 3500, q=0.9, peak=0.6) * 0.15, ts - 0.05)
    return cut(rv(out, 'magic', 0.25), 0.66, 0.22)


@sfx('orb_cast', 'spell', 'Orb cast: deep wobbling magical warble that launches away')
def orb_cast():
    out = S.zeros(0.9)
    D = 0.62
    n = ns(D)
    t = times(n)
    wob = np.sin(TAU * np.cumsum(12.0 - 4.0 * t / D) / S.SR)    # the wobble slows as the orb flies off...
    f = 105.0 * (1 + 0.1 * wob) * 2 ** (-0.3 * t / D)           # ...and its pitch sags, Doppler-style
    src = S.harm(f, n, bright=6.0) + 0.5 * S.sine(f, n) + 0.2 * S.sine(4.02 * f, n)
    fc = 250 + (300 + 1500 * np.exp(-t / 0.2)) * (0.55 + 0.45 * wob)
    y = S.svf(src, fc, q=3.0, mode='lp') * env_t(n, [(0, 0), (0.015, 1), (0.12, 0.85), (D, 0)], curve=1.5)
    S.place(out, S.chorus(y, 3, base_ms=12, depth_ms=3, rate=1.4, mix=0.5) * 0.7, 0)
    S.place(out, I.thump(150, 55, 0.3, 0.025, 0.2) * 0.6, 0)
    S.place(out, I.whoosh(0.5, 1600, 350, q=1.0, peak=0.12) * 0.3, 0.02)
    S.place(out, I.sparkle(0.35, 35, 2500, 7000, root=62, rise=-0.8, env=lambda tt: math.exp(-tt / 0.15)) * 0.15, 0.02)
    return cut(rv(out, 'magic', 0.22), 0.7, 0.2)


@sfx('orb_implode', 'spell', 'Orb implosion: inward-sucking whoomp collapsing into a dark bass boom')
def orb_implode():
    out = S.zeros(1.5)
    T = 0.42                                                     # the moment it collapses
    # inward suck: a reversed reverb swell and a tone spiralling down into the centre
    hit = S.zeros(0.12)
    S.place(hit, I.nburst(0.1, lo=250, hi=7000, t60=0.08), 0)
    S.place(hit, I.bell(hz('A5'), 0.1, 'crystal', t60=0.08, mallet=0) * 0.5, 0)
    suck = S.convolve(hit, ir('magic'))[:ns(T)][::-1]
    S.place(out, suck / (np.max(np.abs(suck)) + 1e-9) * 0.6, 0)
    n = ns(T)
    t = times(n)
    u = t / T
    f = 1100 * 2 ** (-3.2 * u ** 0.8)
    tone = (S.sine(f, n) + 0.4 * S.tri(1.5 * f, n)) * u ** 2 * (1 + 0.3 * np.sin(TAU * np.cumsum(6 + 14 * u) / S.SR))
    S.place(out, S.chorus(tone, 3, rate=2.0, depth_ms=3, mix=0.5) * 0.25, 0)
    # collapse: a dark whoomp, the bass boom and a low cursed chord
    S.place(out, I.nburst(0.25, hi=900, t60=0.2, attack=0.004, color='pink') * 0.6, T)
    S.place(out, S.drive(I.thump(95, 28, 0.9, 0.05, 0.65), 1.8), T)
    k = ns(0.9)
    S.place(out, S.lp(S.brown(k) * 4, 120) * S.decay(k, 0.75, attack=0.02) * 0.45, T)
    m = ns(0.8)
    ch = sum(S.harm(hz(nm), m, bright=2.5) for nm in ('A1', 'E2', 'Bb2'))
    ch *= env_t(m, [(0, 0), (0.03, 1), (0.8, 0)], curve=3)
    S.place(out, S.chorus(S.lp(ch, 900), 3, rate=1.2, depth_ms=3, mix=0.6) * 0.12, T)
    return cut(rv(out, 'big', 0.18), 1.05, 0.35)


@sfx('beam_hum', 'spell',
     'Arcane beam: bright shimmering hum segment with equal-power edges; re-triggered every ~0.3 s it blends into a '
     'steady hum', gain=-3.0)
def beam_hum():
    m = ns(0.75)
    t = times(m)
    # D sus2 chord as 'tonal noise' (see tonal_noise): steady and bright, yet copies 0.3 s apart are
    # uncorrelated, so their cross-fades sum at constant power instead of beating. Spreading the
    # energy over many partials keeps the leftover correlation inside a short cross-fade small.
    parts = [(hz('D2'), 0.3)]
    for nm, a in (('D3', 0.45), ('A3', 0.6), ('D4', 0.55), ('E4', 0.35), ('A4', 0.5), ('D5', 0.35), ('E5', 0.25),
                  ('A5', 0.2)):
        parts += [(k * hz(nm), a / k * math.exp(-(k - 1) / 5.0)) for k in range(1, 25)]
    hum = tonal_noise(m, parts, sigma=3.0)
    shim = tonal_noise(m, [(hz('A5'), 1.0), (hz('E6'), 0.6), (hz('A6'), 0.45), (hz('C#7'), 0.2)], sigma=3.0) \
        * (0.6 + 0.4 * np.sin(TAU * 7.0 * t + 1.0))
    fizz = S.filt(S.white(m), lambda f: S.H_bp(f, 6500, 0.8)) * (0.5 + 0.5 * np.tanh(fast_flutter(m, 15.0, 45.0)))
    x = hum + 0.3 * shim + 0.12 * fizz
    x = S.filt(x, lambda f: S.H_bell(f, 2200, 4.0, 1.6) * S.H_lp(f, 9000, 2) * S.H_hp(f, 50, 2))
    x = steady(rv(S.chorus(x, 3, base_ms=11, depth_ms=2.5, rate=0.9, mix=0.5), 'magic', 0.12)[:m])
    x *= 1 + 0.1 * np.sin(TAU * 13.0 * t)                       # the beam's pulse
    return segment(x, 0.435, 0.12)


@sfx('blade_swing', 'weapon', 'Rune blade swing: airy magical whoosh with a shimmering tail', gain=-3.0)
def blade_swing():
    out = S.zeros(0.6)
    D = 0.26
    n = ns(D)
    u = times(n) / D
    pk = 0.45
    hump = np.where(u < pk, np.sin(0.5 * np.pi * u / pk) ** 2,
                    np.cos(0.5 * np.pi * np.clip((u - pk) / (1 - pk), 0, 1)) ** 2)
    arc = np.sin(np.pi * np.clip(u, 0, 1))
    air = S.sweep(S.pink(n) * 4, 'bp', 650 + 1700 * arc ** 1.5, q=1.0)
    S.place(out, air * hump * 0.9, 0)
    # a faint glassy 'sing' riding the arc of the swing
    f = 1150 * (1 + 0.25 * arc)
    sing = (S.sine(f, n) + 0.45 * S.sine(2.01 * f, n) + 0.2 * S.sine(3.03 * f, n)) * hump ** 1.5
    S.place(out, S.chorus(sing, 3, base_ms=10, depth_ms=1.5, rate=3.0, mix=0.5) * 0.07, 0)
    # shimmering tail
    S.place(out, I.sparkle(0.32, 70, 3000, 9500, root=74, rise=0.6, env=lambda tt: math.exp(-tt / 0.11)) * 0.26, 0.11)
    S.place(out, I.bell(hz('A6'), 0.4, 'crystal', t60=0.3, vel=0.5, mallet=0) * 0.08, 0.14)
    return cut(rv(out, 'magic', 0.16), 0.38, 0.12)


@sfx('blade_wave', 'weapon', 'Rune blade wave: crescent energy slash, a sharp whoosh into a bright ringing arcane tone')
def blade_wave():
    out = S.zeros(0.95)
    S.place(out, I.whoosh(0.3, 500, 5000, q=1.2, peak=0.35, curve=0.8) * 0.7, 0)
    S.place(out, I.thump(240, 90, 0.18, 0.015, 0.12) * 0.45, 0.04)
    # the crescent: a glassy tone whipping up a fourth into a ringing A, with a slow shimmer
    t0 = 0.05
    n = ns(0.6)
    t = times(n)
    f = hz('A5') * 2 ** (-(5 / 12) * np.exp(-t / 0.025)) * (1 + 0.004 * np.sin(TAU * 6.0 * t))
    ring = (S.sine(f, n) + 0.5 * S.sine(2 * f, n) + 0.25 * S.sine(3 * f, n) + 0.12 * S.sine(4.2 * f, n)) \
        * S.decay(n, 0.55, attack=0.004)
    S.place(out, S.chorus(ring, 3, base_ms=12, depth_ms=2.5, rate=1.8, mix=0.55) * 0.32, t0)
    S.place(out, I.bell(hz('E6'), 0.6, 'chime', t60=0.45, vel=0.75, detune=0.002) * 0.25, t0 + 0.03)
    S.place(out, I.bell(hz('A6'), 0.6, 'chime', t60=0.4, vel=0.7, detune=0.002) * 0.2, t0 + 0.035)
    m = ns(0.4)
    S.place(out, S.fm(hz('A5'), m, ratio=3.5, index=2.5 * np.exp(-times(m) / 0.06)) * S.decay(m, 0.35, attack=0.002)
            * 0.08, t0)
    S.place(out, I.sparkle(0.4, 80, 3000, 10000, root=69, rise=0.6, env=lambda tt: math.exp(-tt / 0.14)) * 0.3,
            t0 + 0.02)
    return cut(rv(out, 'magic', 0.22), 0.65, 0.2)


# ===========================================================================
# tools
# ===========================================================================

@sfx('tool_grab_loop', 'tool_loop', 'Gravity-gauntlet hum: warm low drone, soft shimmer and gentle warble', loop=True)
def tool_grab_loop():
    n = ns(4.0)
    t = times(n)
    vib = 1 + 0.002 * np.sin(TAU * S.loopf(0.5, n) * t)
    y = S.harm(S.loopf(110.0, n) * vib, n, bright=2.2) + 0.7 * S.sine(S.loopf(110.5, n) * vib, n)
    y += 0.25 * S.harm(S.loopf(165.0, n), n, bright=1.5)
    sh = S.sine(S.loopf(880, n), n) * (0.5 + 0.5 * np.sin(TAU * S.loopf(0.75, n) * t)) \
        + S.sine(S.loopf(1320.5, n), n) * (0.5 + 0.5 * np.sin(TAU * S.loopf(0.5, n) * t + 2))
    y += 0.06 * sh
    band = S.filt(S.pink(n), lambda f: S.H_bp(f, 600, 1.5), circular=True)
    y += 0.5 * band * (1 + 0.3 * np.sin(TAU * S.loopf(6.0, n) * t))
    y *= 1 + 0.12 * np.sin(TAU * S.loopf(6.0, n) * t)
    y = S.filt(y, lambda f: S.H_lp(f, 3000, 2), circular=True)
    return S.chorus(y, 3, base_ms=10, depth_ms=2, rate=0.5, mix=0.4, circular=True)


@sfx('tool_grab_start', 'tool', 'Rising vwoom into the grab hum, with a sparkle')
def tool_grab_start():
    out = S.zeros(0.8)
    n = ns(0.45)
    t = times(n)
    f = 55 * 2 ** np.clip(t / 0.3, 0, 1)
    env = np.clip(t / 0.25, 0, 1) ** 1.5 * np.where(t < 0.32, 1.0, np.exp(-(t - 0.32) / 0.05))
    S.place(out, (S.harm(f, n, bright=2.5) + 0.8 * S.sine(f, n)) * env * 0.7, 0)
    S.place(out, I.whoosh(0.4, 300, 1800, q=1.2, peak=0.75) * 0.5, 0)
    S.place(out, I.sparkle(0.25, 60, 3000, 9000, root=69) * 0.25, 0.02)
    S.place(out, I.bell(hz('A5'), 0.5, 'crystal', t60=0.4, vel=0.6) * 0.25, 0.3)
    return rv(out, 'room', 0.15)


@sfx('tool_freeze', 'tool', 'Ice lock: crackling frost, crystalline shing and a solid thunk')
def tool_freeze():
    out = S.zeros(1.3)
    S.place(out, I.crackle(0.5, rate=500, lo=3500, hi=9000, env=lambda tt: math.exp(-tt / 0.2),
                           size=(0.0002, 0.001)) * 0.55, 0)
    r = S.rng()
    modes = list(zip(np.sort(r.uniform(2000, 7000, 10)), r.uniform(0.3, 1, 10), r.uniform(0.3, 0.8, 10)))
    S.place(out, S.modal(ns(1.0), modes) * 0.22, 0.03)
    S.place(out, I.whoosh(0.5, 6000, 2500, q=0.8, peak=0.15, color='white') * 0.4, 0)
    S.place(out, I.thump(260, 120, 0.15, 0.015, 0.08) * 0.5, 0.0)
    S.place(out, I.bell(hz('E7'), 0.8, 'crystal', t60=0.6, vel=0.7) * 0.2, 0.05)
    return rv(S.lp(out, 10000), 'magic', 0.22)


@sfx('tool_weld', 'tool', 'Rune weld: sizzling arc that locks with a clunk and a soft confirm ping')
def tool_weld():
    out = S.zeros(1.0)
    n = ns(0.4)
    gate = (S.smooth_noise(n, 120) > 0.3) * (0.6 + 0.4 * S.white(n))
    sz = S.filt(S.white(n) * gate, lambda f: S.H_bp(f, 4500, 0.7))
    sz *= env_t(n, [(0, 0), (0.02, 1), (0.32, 0.8), (0.4, 0)])
    S.place(out, sz * 0.6, 0)
    m = ns(0.38)
    S.place(out, I.zap(0.38, 120, 0.25, 300, 5000, 2.0, sizzle=0.3)
            * env_t(m, [(0, 0), (0.02, 1), (0.3, 0.7), (0.38, 0)]) * 0.35, 0)
    S.place(out, I.metal(310, 0.4, 0.22, bright=0.55, click_amt=0.4) * 0.55, 0.36)
    S.place(out, I.thump(180, 80, 0.15, 0.015, 0.1) * 0.6, 0.36)
    S.place(out, I.bell(hz('G6'), 0.5, 'crystal', t60=0.4, vel=0.6) * 0.25, 0.38)
    return rv(out, 'room', 0.15)


@sfx('tool_remove', 'tool', 'Dematerialise: shimmer sucked away with a downward zip and a puff')
def tool_remove():
    out = S.zeros(0.8)
    S.place(out, I.whoosh(0.3, 5000, 900, q=1.2, peak=0.9) * 0.6, 0)
    S.place(out, I.sparkle(0.3, 70, 2500, 9000, root=74, rise=-1.5, env=lambda tt: min(1.0, tt / 0.25)) * 0.35, 0)
    m = ns(0.22)
    tm = times(m)
    f = 1400 * np.exp(np.log(180 / 1400) * np.clip(tm / 0.2, 0, 1))
    S.place(out, S.harm(f, m, bright=2.0) * S.adsr(m, 0.01, 0.05, 0.8, 0.05, gate=0.17) * 0.3, 0.12)
    S.place(out, I.nburst(0.12, hi=1200, t60=0.1, color='pink') * 0.5, 0.3)
    return rv(out, 'magic', 0.18)


@sfx('tool_spawn', 'tool', 'Cartoon bubble pop with a sparkly tail as an object appears')
def tool_spawn():
    out = S.zeros(0.5)
    n = ns(0.12)
    t = times(n)
    f = 260 * np.exp(np.log(950 / 260) * np.clip(t / 0.035, 0, 1))
    pop = (S.sine(f, n) + 0.25 * S.harm(f, n, bright=1.5, kind='square')) * S.decay(n, 0.1, attack=0.002)
    S.place(out, pop, 0)
    S.place(out, I.click(0.004, 2500, 0.8) * 0.6, 0)
    S.place(out, I.sparkle(0.3, 30, 3500, 10000, root=79, grain=(0.04, 0.12)) * 0.25, 0.03)
    S.place(out, I.bell(hz('G6'), 0.35, 'celesta', t60=0.3, vel=0.6) * 0.2, 0.03)
    return rv(out, 'room', 0.12)


@sfx('tool_configure', 'tool', 'Friendly electronic double beep (E6, A6)', gain=2.0)
def tool_configure():
    out = S.zeros(0.3)
    for f, t0, d in ((hz('E6'), 0.0, 0.055), (hz('A6'), 0.08, 0.075)):
        n = ns(d + 0.03)
        S.place(out, (S.sine(f, n) + 0.18 * S.sine(3 * f, n)) * S.adsr(n, 0.003, 0.02, 0.85, 0.02, gate=d), t0)
    S.place(out, I.click(0.003, 3000, 0.8) * 0.3, 0)
    return rv(out, 'room', 0.08)


# ===========================================================================
# contraptions
# ===========================================================================

@sfx('thruster_loop', 'loop', 'Brass steam thruster: smooth roar, low rumble and soft hiss', loop=True)
def thruster_loop():
    n = ns(4.0)
    t = times(n)
    roar = S.filt(S.pink(n), lambda f: S.H_lp(f, 2200, 2) * S.H_bell(f, 600, 5, 1.5) * S.H_hp(f, 80, 2), circular=True)
    rum = S.filt(S.brown(n), lambda f: S.H_lp(f, 120, 2), circular=True)
    hs = S.filt(S.white(n), lambda f: S.H_hp(f, 4500, 2) * S.H_lp(f, 11000, 2), circular=True)
    flutter = 1 + 0.15 * S.smooth_noise(n, 9) + 0.08 * np.sin(TAU * S.loopf(23, n) * t)
    return (roar + 0.8 * rum + 0.12 * hs) * flutter


@sfx('engine_loop', 'loop', 'Clockwork steam engine: rhythmic chuffs, ticking gears and a low hum', loop=True)
def engine_loop():
    L = 2.0
    n = ns(L)
    out = np.zeros(n)
    r = S.rng()
    for k in range(8):
        t0 = k * L / 8
        a = 1.0 if k % 2 == 0 else 0.8
        ch = I.nburst(0.16, fc=r.uniform(900, 1100), q=0.8, t60=0.12, attack=0.004, color='pink')
        S.place(out, ch * a, t0, circular=True)
        S.place(out, I.thump(85, 55, 0.12, 0.02, 0.09) * 0.5 * a, t0, circular=True)
    for k in range(32):
        S.place(out, I.metal(1800 if k % 4 else 1500, 0.05, 0.025, bright=0.6, click_amt=0.3)
                * (0.12 if k % 4 else 0.2), k * L / 32 + 0.012, circular=True)
    out += S.harm(S.loopf(55, n), n, bright=2.0) * 0.2 + S.sine(S.loopf(110, n), n) * 0.08
    return S.filt(out, lambda f: S.H_lp(f, 7000, 2), circular=True)


@sfx('rotor_loop', 'loop', 'Wooden rotor whup-whup (12 Hz blade pass) with a soft motor whine', loop=True)
def rotor_loop():
    L = 2.0
    n = ns(L)
    t = times(n)
    out = np.zeros(n)
    for k in range(24):
        m = ns(0.07)
        w = np.sin(np.pi * times(m) / 0.07) ** 2
        nz = S.filt(S.white(m) * w, lambda f: S.H_lp(f, 800, 2) * S.H_hp(f, 60, 2) * S.H_bell(f, 300, 4, 1.5))
        S.place(out, nz * (1.2 if k % 3 == 0 else 1.0) * 1.4, k * L / 24, circular=True)
        S.place(out, I.thump(70, 50, 0.07, 0.02, 0.06) * 0.35, k * L / 24, circular=True)
    air = S.filt(S.pink(n), lambda f: S.H_lp(f, 1500, 2), circular=True) * 0.18
    whine = S.harm(S.loopf(330, n) * (1 + 0.004 * np.sin(TAU * S.loopf(3, n) * t)), n, bright=1.8,
                   kind='square', even=0.3) * 0.05
    return out + air + whine


@sfx('hover_loop', 'loop', 'Levitation stone: warm magical hum with slow shimmer', loop=True)
def hover_loop():
    n = ns(4.0)
    t = times(n)
    y = np.zeros(n)
    for f, a in ((110, 1.0), (165, 0.5), (220, 0.45), (277.25, 0.25), (330, 0.2)):
        wob = 1 + 0.002 * np.sin(TAU * S.loopf(0.25, n) * t + f)
        y += a * (S.sine(S.loopf(f, n) * wob, n) + 0.7 * S.sine(S.loopf(f + 0.25 * (1 + (f > 200)), n) * wob, n))
    y *= 1 + 0.15 * np.sin(TAU * S.loopf(0.5, n) * t)
    air = S.filt(S.pink(n), lambda f: S.H_bp(f, 1200, 1.0), circular=True) \
        * (1 + 0.5 * np.sin(TAU * S.loopf(0.25, n) * t + 1))
    tw = sum(S.sine(S.loopf(f, n), n) * (0.5 + 0.5 * np.sin(TAU * S.loopf(rr, n) * t + p)) ** 4
             for f, rr, p in ((1760, 0.75, 0), (2217.5, 1.0, 2), (2640, 0.5, 4)))
    out = y * 0.25 + air * 0.25 + tw * 0.04
    return S.chorus(out, 3, base_ms=12, depth_ms=2, rate=0.4, mix=0.35, circular=True)


@sfx('impact_wood', 'impact', 'Chunky wooden knock with a small bounce')
def impact_wood():
    out = S.zeros(0.5)
    S.place(out, I.wood(185, 0.4, 0.14, bright=0.9, click_amt=0.5), 0)
    S.place(out, I.thump(150, 90, 0.1, 0.02, 0.06) * 0.6, 0)
    S.place(out, I.wood(205, 0.25, 0.08, bright=0.8) * 0.3, 0.065)
    S.place(out, I.crackle(0.05, rate=300, lo=1500, hi=5000) * 0.3, 0.002)
    return rv(out, 'room', 0.1)


@sfx('impact_metal', 'impact', 'Resonant metal clang with a short ring')
def impact_metal():
    out = S.zeros(1.4)
    S.place(out, I.metal(410, 1.3, 1.0, bright=0.75, click_amt=0.4), 0)
    S.place(out, I.thump(140, 80, 0.12, 0.015, 0.08) * 0.6, 0)
    return rv(S.lp(out, 9000), 'room', 0.12)


@sfx('impact_stone', 'impact', 'Heavy stone thud with gritty crunch and pebbles')
def impact_stone():
    out = S.zeros(0.6)
    S.place(out, I.thump(130, 60, 0.25, 0.02, 0.12), 0)
    S.place(out, I.nburst(0.15, hi=2500, t60=0.09, attack=0.001, color='pink') * 0.7, 0)
    S.place(out, I.crackle(0.18, rate=250, lo=1200, hi=6000, env=lambda tt: math.exp(-tt / 0.06)) * 0.8, 0)
    r = S.rng()
    for _ in range(3):
        S.place(out, S.modal(ns(0.05), [(r.uniform(2500, 4000), 1, 0.03)]) * 0.12, r.uniform(0.08, 0.3))
    return rv(out, 'room', 0.1)


@sfx('spring_boing', 'impact', 'Cartoon spring boing with a wobbling pitch')
def spring_boing():
    n = ns(1.1)
    t = times(n)
    f = 200 * (1 - 0.08 * np.clip(t / 0.8, 0, 1)) * (1 + 0.22 * np.exp(-t / 0.28) * np.sin(TAU * 9.5 * t))
    src = S.harm(f, n, bright=6)
    fc = 700 + 1400 * np.exp(-t / 0.15) * (0.5 + 0.5 * np.cos(TAU * 9.5 * t))
    y = (S.svf(src, fc, q=4.0, mode='bp') * 0.8 + 0.4 * S.sine(f, n)) * S.decay(n, 1.0, attack=0.002)
    S.place(y, I.metal(900, 0.15, 0.08, bright=0.6, click_amt=0.5) * 0.4, 0)
    return rv(y, 'room', 0.1)


@sfx('turret_arcane', 'weapon', 'Arcane turret bolt: glassy FM pew with a sparkle burst')
def turret_arcane():
    out = S.zeros(0.9)
    n = ns(0.35)
    t = times(n)
    y = S.fm(700 + 1100 * np.exp(-t / 0.06), n, ratio=1.41, index=0.4 + 3.0 * np.exp(-t / 0.05)) \
        * S.decay(n, 0.3, attack=0.001)
    S.place(out, S.chorus(y, 2, rate=3, depth_ms=1.5, mix=0.5) * 0.6, 0)
    S.place(out, I.nburst(0.06, lo=3000, hi=10000, t60=0.04) * 0.35, 0)
    S.place(out, I.thump(220, 90, 0.12, 0.012, 0.08) * 0.5, 0)
    S.place(out, I.sparkle(0.25, 60, 3000, 10000, root=74, env=lambda tt: math.exp(-tt / 0.1)) * 0.3, 0.01)
    return rv(out, 'hall', 0.14)


@sfx('turret_rivet', 'weapon', 'Heavy rivet turret shot with a ratcheting barrel clack')
def turret_rivet():
    out = S.zeros(0.45)
    S.place(out, S.drive(I.thump(120, 50, 0.2, 0.015, 0.12), 1.5), 0)
    S.place(out, I.nburst(0.06, fc=1000, q=0.6, t60=0.04, attack=0.0005) * 1.6, 0)
    S.place(out, S.modal(ns(0.2), [(2200, 1, 0.1), (3600, 0.6, 0.07), (5300, 0.3, 0.05)]) * 0.22, 0.003)
    for k in range(3):
        S.place(out, I.metal(1400 + 150 * k, 0.06, 0.03, bright=0.6, click_amt=0.5) * 0.18, 0.05 + 0.022 * k)
    return rv(out, 'room', 0.12)


# ===========================================================================
# enemies
# ===========================================================================

@sfx('wisp_loop', 'enemy_loop', 'Ember wisp idle: flickering flame flutter, soft crackle, faint mischievous tone',
     loop=True)
def wisp_loop():
    L = 3.0
    n = ns(L)
    t = times(n)
    fl = S.filt(S.pink(n), lambda f: S.H_bp(f, 750, 0.7) * S.H_lp(f, 5000, 2), circular=True)
    out = fl * (1 + 0.45 * S.smooth_noise(n, 8))
    cr = np.zeros(n)
    r = S.rng()
    for _ in range(r.poisson(9 * L)):
        m = ns(r.uniform(0.0005, 0.003))
        b = S.white(m) * np.exp(-np.arange(m) / (m / 3)) * math.exp(-r.uniform(0, 2.5))
        S.place(cr, b, r.uniform(0, L), circular=True)
    out += S.filt(cr, lambda f: S.H_hp(f, 1500, 2) * S.H_lp(f, 7000, 2), circular=True) * 1.5
    vib = 1 + 0.01 * np.sin(TAU * S.loopf(5, n) * t)
    tone = (S.sine(S.loopf(523.25, n) * vib, n) + 0.5 * S.sine(S.loopf(784, n) * vib, n)) \
        * (0.5 + 0.5 * np.sin(TAU * S.loopf(0.6667, n) * t)) ** 2
    return out + tone * 0.03


@sfx('wisp_attack', 'enemy', 'Wisp lunge: impish hee-hee giggle into a fiery fwoosh')
def wisp_attack():
    out = S.zeros(0.95)
    for k, (t0, f0) in enumerate(((0.0, 700), (0.075, 660), (0.15, 620))):
        n = ns(0.06)
        t = times(n)
        f = f0 * (1 + 0.15 * np.sin(np.pi * t / 0.06))
        c = S.harm(f, n, bright=6) * np.sin(np.pi * t / 0.06) ** 1.5
        c = I.formant(c + 0.2 * S.white(n), [(0, 'i'), (0.06, 'e')], 1.5)
        S.place(out, c * (1 - 0.15 * k), t0)
    S.place(out, I.whoosh(0.55, 500, 2500, q=0.9, peak=0.3) * 0.7, 0.18)
    S.place(out, I.crackle(0.5, 120, 1500, 6000, env=lambda tt: math.exp(-tt / 0.2)) * 0.8, 0.18)
    S.place(out, I.thump(160, 70, 0.15, 0.02, 0.1) * 0.4, 0.2)
    return rv(out, 'room', 0.15)


@sfx('golem_step', 'enemy', 'Heavy stone footfall: deep thud, rock crunch, gravel and a faint rune hum')
def golem_step():
    out = S.zeros(1.0)
    S.place(out, S.drive(I.thump(70, 36, 0.8, 0.04, 0.45), 1.6), 0)
    S.place(out, I.nburst(0.35, hi=1300, t60=0.22, attack=0.002, color='pink') * 0.9, 0)
    S.place(out, I.crackle(0.4, rate=160, lo=900, hi=4500, env=lambda tt: math.exp(-tt / 0.12)) * 0.9, 0.005)
    n = ns(0.6)
    S.place(out, (S.sine(hz('A2'), n) + 0.6 * S.sine(hz('E3'), n)) * S.decay(n, 0.5, attack=0.01) * 0.15, 0)
    return rv(out, 'room', 0.12)


@sfx('golem_slam', 'enemy', 'Golem ground slam: huge boom, rock smash, debris and a dark rune chord')
def golem_slam():
    out = S.zeros(2.4)
    S.place(out, I.nburst(0.02, lo=500, t60=0.015) * 0.8, 0)
    S.place(out, S.drive(I.thump(60, 28, 1.6, 0.07, 1.1), 2.0), 0)
    n = ns(1.2)
    t = times(n)
    sm = S.sweep(S.drive(S.pink(n) * 4, 2.0), 'lp', lambda tt: 400 + 5000 * np.exp(-np.maximum(tt, 0) / 0.15))
    S.place(out, sm * np.exp(-t / 0.3) * 0.8, 0)
    S.place(out, I.crackle(1.2, rate=120, lo=800, hi=5000, env=lambda tt: math.exp(-tt / 0.4)), 0.03)
    m = ns(1.6)
    ch = sum(S.harm(hz(nm), m, bright=3.0) for nm in ('A2', 'E3', 'Bb3'))
    ch *= env_t(m, [(0, 0), (0.08, 1), (1.6, 0)], curve=3)
    S.place(out, S.chorus(S.lp(ch, 1800), 3, rate=1.5, depth_ms=3, mix=0.6) * 0.18, 0.02)
    k = ns(2.0)
    S.place(out, S.lp(S.brown(k) * 4, 120) * S.decay(k, 1.6, attack=0.05) * 0.5, 0)
    return rv(out, 'big', 0.25)


@sfx('wraith_shriek', 'enemy', 'Ghostly wailing shriek: three formant voices with eerie vibrato')
def wraith_shriek():
    n = ns(1.3)
    t = times(n)
    contour = np.interp(t, [0, 0.35, 0.7, 1.3], [480, 1050, 900, 620])
    out = np.zeros(n)
    for det, vr, ph in ((0.0, 6.5, 0.0), (0.018, 7.3, 1.3), (-0.015, 5.9, 2.1)):
        out += S.harm(contour * (1 + det) * (1 + 0.03 * np.sin(TAU * vr * t + ph)), n, bright=8)
    out += S.white(n) * 0.3
    out = I.formant(out, [(0, 'u'), (0.3, 'i'), (0.8, 'e'), (1.3, 'a')], scale=1.3)
    out = S.filt(out * env_t(n, [(0, 0), (0.12, 1), (0.8, 0.8), (1.3, 0)], curve=1.5),
                 lambda f: S.H_hp(f, 250, 2) * S.H_lp(f, 6000, 2))
    return rv(S.chorus(out, 3, base_ms=15, depth_ms=5, rate=0.9, mix=0.5), 'magic', 0.35)


@sfx('cultist_cast', 'enemy', 'Dark choral chant swelling into a crackling cursed release')
def cultist_cast():
    out = S.zeros(1.9)
    n = ns(0.9)
    t = times(n)
    ch = np.zeros(n)
    for nm, det in (('D3', 0.0), ('A2', 0.004), ('F3', -0.003), ('D2', 0.002)):
        ch += S.harm(hz(nm) * (1 + det) * (1 + 0.006 * np.sin(TAU * 5.0 * t + det * 1000)), n, bright=10)
    ch = I.formant(ch, [(0, 'o'), (0.5, 'u'), (0.9, 'o')], scale=0.9)
    S.place(out, ch * env_t(n, [(0, 0), (0.5, 1), (0.8, 0.9), (0.9, 0)], curve=1) * 0.6, 0)
    S.place(out, I.whoosh(0.85, 200, 1600, q=1.0, peak=0.9, curve=1.5) * 0.5, 0)
    S.place(out, I.crackle(0.6, rate=140, lo=1200, hi=6000, env=lambda tt: math.exp(-tt / 0.2)) * 0.8, 0.8)
    S.place(out, I.thump(110, 40, 0.5, 0.03, 0.35) * 0.7, 0.8)
    m = ns(0.8)
    S.place(out, S.fm(hz('F#5'), m, ratio=1.414, index=2.5) * S.decay(m, 0.7, attack=0.002) * 0.15, 0.8)
    return rv(out, 'magic', 0.3)


@sfx('drone_loop', 'enemy_loop', 'Scout drone hover: four detuned rotor buzzes, small motor whine, gentle bob',
     loop=True)
def drone_loop():
    n = ns(2.0)
    t = times(n)
    y = np.zeros(n)
    for k, f in enumerate((180.0, 181.5, 183.0, 184.5)):
        y += S.harm(S.loopf(f, n), n, bright=4.0, ph0=k * 0.27)
    y = S.filt(y, lambda f: S.H_lp(f, 1600, 2) * S.H_bell(f, 900, 4, 1.2), circular=True)
    whine = S.sine(S.loopf(1200, n) * (1 + 0.003 * np.sin(TAU * S.loopf(4, n) * t)), n) * 0.05
    air = S.filt(S.pink(n), lambda f: S.H_bp(f, 1000, 0.7), circular=True) * 0.3
    return (y * 0.25 + whine + air) * (1 + 0.12 * np.sin(TAU * S.loopf(4, n) * t))


@sfx('drone_shoot', 'enemy', 'Small tinny blaster pew from a scout drone')
def drone_shoot():
    out = S.zeros(0.45)
    n = ns(0.16)
    t = times(n)
    y = S.harm(700 + 2100 * np.exp(-t / 0.035), n, bright=4, kind='square', even=0.2) * S.decay(n, 0.15, attack=0.0008)
    S.place(out, y * 0.7, 0)
    S.place(out, I.click(0.003, 6000, 0.8) * 0.5, 0)
    S.place(out, I.nburst(0.04, lo=2500, hi=9000, t60=0.03) * 0.25, 0)
    return S.echo(out, 0.06, 0.25, 0.18, damp=4000)


@sfx('sentry_shoot', 'enemy', 'Sentry turret shot: hard punch, metallic ring and an electric snap')
def sentry_shoot():
    out = S.zeros(0.5)
    S.place(out, S.drive(I.thump(130, 50, 0.2, 0.012, 0.12), 1.8), 0)
    S.place(out, S.drive(I.nburst(0.04, lo=1200, hi=7000, t60=0.025, attack=0.0003), 2.0) * 0.8, 0)
    S.place(out, S.modal(ns(0.25), [(620, 1, 0.14), (1430, 0.7, 0.1), (2700, 0.45, 0.07)]) * 0.3, 0.002)
    n = ns(0.07)
    t = times(n)
    S.place(out, S.harm(900 * np.exp(-t / 0.05), n, bright=3) * S.decay(n, 0.07) * 0.2, 0.01)
    return rv(out, 'room', 0.12)


@sfx('crawler_skitter', 'enemy', 'Spider-bot legs: rapid metallic taps over a servo whir')
def crawler_skitter():
    dur = 0.8
    out = S.zeros(dur + 0.1)
    r = S.rng()
    tt = 0.0
    while tt < dur - 0.05:
        f0 = r.uniform(1700, 3200)
        S.place(out, S.modal(ns(0.05), [(f0, 1.0, 0.025), (f0 * 1.6, 0.5, 0.015)]) * r.uniform(0.4, 1.0), tt)
        S.place(out, I.click(0.002, 5000, 0.8) * 0.3, tt)
        tt += r.uniform(0.025, 0.06)
    n = ns(dur)
    shape = np.sin(np.pi * times(n) / dur)
    S.place(out, I.servo(dur, 700, 900, wobble=0.04, bright=2.0) * shape ** 0.5 * 0.12, 0)
    S.place(out, I.hiss(dur, 3500, 9000, 0.4, 25) * shape * 0.05, 0)
    return rv(out, 'room', 0.1)


@sfx('crawler_bite', 'enemy', 'Mandible snap: servo zip and two sharp metal clacks')
def crawler_bite():
    out = S.zeros(0.5)
    n = ns(0.08)
    S.place(out, I.servo(0.08, 500, 1500, wobble=0.0, bright=2.0) * np.sin(np.pi * times(n) / 0.08) * 0.25, 0)
    for k, t0 in enumerate((0.07, 0.115)):
        S.place(out, I.metal(1800 + 300 * k, 0.12, 0.05, bright=0.7, click_amt=0.8) * (0.6 + 0.4 * k), t0)
    S.place(out, I.nburst(0.05, fc=2000, q=0.8, t60=0.04) * 0.4, 0.115)
    return rv(out, 'room', 0.1)


@sfx('ironclad_step', 'enemy', 'Giant mech stomp: sub boom, heavy steel clank, servo and hydraulic hiss')
def ironclad_step():
    out = S.zeros(1.8)
    S.place(out, S.drive(I.thump(52, 26, 1.2, 0.05, 0.8), 2.0), 0)
    S.place(out, I.nburst(0.05, hi=2000, t60=0.04, color='pink') * 0.6, 0)
    S.place(out, I.metal(95, 1.2, 0.7, ratios=(1.0, 2.43, 4.3, 7.9, 12.9), amps=(1, .8, .6, .4, .25),
                         bright=0.8, click_amt=0.4) * 0.6, 0)
    n = ns(0.5)
    S.place(out, I.hiss(0.5, 2500, 10000, 0.2, 20) * env_t(n, [(0, 0), (0.03, 1), (0.5, 0)], curve=2) * 0.35, 0.15)
    m = ns(0.35)
    S.place(out, I.servo(0.35, 320, 210, wobble=0.01, bright=2.5) * env_t(m, [(0, 0), (0.05, 1), (0.35, 0)]) * 0.08,
            0.05)
    return rv(out, 'big', 0.2)


@sfx('ironclad_rocket', 'enemy', 'Rocket launch: ignition pop and a roaring, receding whoosh')
def ironclad_rocket():
    out = S.zeros(1.8)
    S.place(out, I.thump(110, 50, 0.25, 0.02, 0.15), 0)
    S.place(out, I.nburst(0.04, lo=500, hi=6000, t60=0.03) * 0.8, 0)
    n = ns(1.5)
    roar = S.sweep(S.pink(n) * 4, 'bp', lambda tt: 1800 * np.exp(-np.maximum(tt, 0) / 0.8) + 400, q=0.7)
    S.place(out, roar * env_t(n, [(0, 0), (0.04, 1), (0.4, 0.8), (1.5, 0)], curve=1.5), 0.01)
    m = ns(1.2)
    S.place(out, I.hiss(1.2, 3000, 10000, 0.3, 30) * env_t(m, [(0, 0), (0.05, 1), (1.2, 0)], curve=2) * 0.2, 0.02)
    S.place(out, I.crackle(1.0, rate=80, lo=1000, hi=5000, env=lambda tt: math.exp(-tt / 0.4)) * 0.5, 0.02)
    return rv(out, 'big', 0.18)


@sfx('hit_magic', 'enemy', 'Magic creature hit: sparkly tssh with crystalline pings')
def hit_magic():
    out = S.zeros(0.6)
    S.place(out, I.nburst(0.06, lo=2000, hi=11000, t60=0.05) * 0.6, 0)
    S.place(out, I.thump(220, 90, 0.1, 0.012, 0.07) * 0.6, 0)
    r = S.rng()
    tbl = I.scale_freqs(74, I.PENT, 1500, 6000)
    for k in range(4):
        S.place(out, I.bell(tbl[r.integers(len(tbl))], 0.4, 'crystal', t60=0.25, vel=0.7, mallet=0) * 0.2, 0.003 * k)
    S.place(out, I.sparkle(0.3, 50, 3000, 10000, root=74, env=lambda tt: math.exp(-tt / 0.1)) * 0.25, 0.01)
    return rv(out, 'hall', 0.12)


@sfx('hit_metal', 'enemy', 'Metal enemy hit: punchy clank and tink')
def hit_metal():
    out = S.zeros(0.5)
    S.place(out, I.metal(880, 0.45, 0.3, ratios=(1.0, 1.58, 2.42, 3.37, 4.6), amps=(1, 0.8, 0.6, 0.4, 0.25),
                         bright=0.85, click_amt=0.6), 0)
    S.place(out, I.thump(170, 90, 0.1, 0.01, 0.06) * 0.7, 0)
    S.place(out, I.nburst(0.02, lo=3000, hi=9000, t60=0.012) * 0.4, 0)
    return rv(out, 'room', 0.1)


@sfx('death_magic', 'enemy', 'Magic death: sparkly poof, rising glitter and a fading ghost tone')
def death_magic():
    out = S.zeros(1.8)
    S.place(out, I.nburst(0.35, hi=1600, t60=0.3, attack=0.004, color='pink') * 0.8, 0)
    S.place(out, I.thump(190, 70, 0.25, 0.02, 0.15) * 0.5, 0)
    S.place(out, I.sparkle(1.2, 70, 2500, 9000, root=74, rise=1.2, env=lambda tt: math.exp(-tt / 0.5)) * 0.4, 0.02)
    n = ns(1.0)
    t = times(n)
    f = 880 * 2 ** (-np.clip(t / 0.9, 0, 1))
    gh = (S.sine(f, n) + 0.3 * S.sine(1.5 * f, n)) * env_t(n, [(0, 0), (0.05, 1), (1.0, 0)], curve=1.5)
    S.place(out, S.chorus(gh, 3, rate=1.2, depth_ms=4, mix=0.6) * 0.2, 0.03)
    S.place(out, I.whoosh(0.5, 3000, 600, q=0.8, peak=0.15) * 0.3, 0)
    return rv(out, 'magic', 0.3)


@sfx('death_tech', 'enemy', 'Tech death: metal crunch, electric sputter, a pop and tinkling bolts')
def death_tech():
    out = S.zeros(1.8)
    r = S.rng()
    for _ in range(9):
        S.place(out, I.metal(r.uniform(400, 2500), 0.2, 0.12, bright=0.6, click_amt=0.5) * r.uniform(0.2, 0.5),
                r.uniform(0, 0.22))
    S.place(out, S.drive(I.nburst(0.25, lo=300, hi=5000, t60=0.15, color='pink'), 2.5) * 0.4, 0)
    for k, t0 in enumerate((0.12, 0.24, 0.31)):
        S.place(out, I.zap(0.06, 110 + 40 * k, 0.4, 500, 7000, 3.0) * S.decay(ns(0.06), 0.06) * 0.35, t0)
    S.place(out, I.thump(140, 45, 0.5, 0.025, 0.3), 0.38)
    S.place(out, I.nburst(0.3, hi=3000, t60=0.25, color='pink', attack=0.001) * 0.8, 0.38)
    for _ in range(6):
        S.place(out, I.metal(r.uniform(2500, 5000), 0.15, 0.08, bright=0.6, click_amt=0.2) * 0.12, r.uniform(0.6, 1.3))
    return rv(out, 'room', 0.15)


@sfx('elite_spawn', 'enemy', 'Champion enemy appears: ominous low brass stab (D minor with a tritone) over a rumble')
def elite_spawn():
    out = S.zeros(1.6)
    stab = np.zeros(ns(1.0))
    for nm, v in (('D2', 0.8), ('A2', 0.6), ('D3', 0.9), ('F3', 0.8), ('G#3', 0.7), ('D4', 0.5)):
        S.place(stab, I.brass(hz(nm), 0.3, vel=1.0, voices=3, detune=9.0, bright=11.0, attack=0.02, release=0.45,
                              scoop=0.06) * v, 0)
    S.place(out, S.filt(stab, lambda f: S.H_lp(f, 5000, 2) * S.H_bell(f, 1200, 5.0, 1.5)), 0)
    S.place(out, I.timpani(hz('D2'), 1.0, t60=0.8) * 0.3, 0)
    S.place(out, S.drive(I.thump(75, 30, 0.8, 0.05, 0.6), 1.6) * 0.4, 0)
    n = ns(1.0)
    rum = S.lp(S.brown(n) * 4, 120) * (1 + 0.5 * S.smooth_noise(n, 5)) \
        * env_t(n, [(0, 0), (0.06, 1), (0.4, 0.6), (1.0, 0)], curve=1.5)
    S.place(out, rum * 0.25, 0)
    return cut(rv(out, 'hall', 0.18), 1.35, 0.35)


# ===========================================================================
# ambience
# ===========================================================================

@sfx('amb_wind_loop', 'amb', 'Soft outdoor wind with slow gusts and a faint whistle', loop=True)
def amb_wind_loop():
    n = ns(16.0)
    gust = 0.55 + 0.45 * np.tanh(S.smooth_noise(n, 0.15))
    fcurve = 500 + 700 * (0.5 + 0.5 * np.tanh(S.smooth_noise(n, 0.12)))
    body = S.tvfilt(S.pink(n), lambda tt, f: S.H_bp(f, S.curve_at(fcurve, tt), 0.7) * S.H_lp(f, 3000, 2),
                    circular=True, frame=2048)
    whistle = S.tvfilt(S.white(n), lambda tt, f: S.H_bp(f, S.curve_at(fcurve * 2.2, tt), 12.0),
                       circular=True, frame=4096)
    rumble = S.filt(S.brown(n), lambda f: S.H_lp(f, 150, 2), circular=True)
    return body * gust + whistle * gust ** 2 * 0.08 + rumble * 0.3


def bird(kind, r):
    if kind == 'tweet':
        k = int(r.integers(2, 5))
        base = r.uniform(2800, 4200)
        out = S.zeros(0.16 * k + 0.1)
        tt = 0.0
        for _ in range(k):
            d = r.uniform(0.04, 0.07)
            n = ns(d)
            t = times(n)
            S.place(out, S.sine(base * (1 + 0.35 * t / d), n) * np.sin(np.pi * t / d) ** 2, tt)
            tt += r.uniform(0.09, 0.14)
        return out
    if kind == 'warble':
        d = r.uniform(0.4, 0.8)
        n = ns(d)
        t = times(n)
        rate = r.uniform(18, 30)
        f = r.uniform(2500, 3800) + r.uniform(300, 700) * np.sin(TAU * rate * t) + 400 * (t / d) * r.choice([-1, 1])
        env = np.sin(np.pi * t / d) ** 0.7 * (0.6 + 0.4 * np.sin(TAU * rate / 2 * t) ** 2)
        return S.sine(f, n) * env
    if kind == 'song':
        notes = r.uniform(2000, 3600, int(r.integers(3, 7)))
        durs = r.uniform(0.08, 0.18, len(notes))
        gaps = r.uniform(0.02, 0.06, len(notes))
        total = float(np.sum(durs + gaps)) + 0.05
        n = ns(total)
        t = times(n)
        starts = np.concatenate([[0], np.cumsum(durs + gaps)[:-1]])
        f = np.interp(t, np.repeat(starts, 2) + np.tile([0.0, 0.015], len(notes)), np.repeat(notes, 2))
        amp = np.zeros(n)
        for s0, d in zip(starts, durs):
            m = (t >= s0) & (t < s0 + d)
            amp[m] = np.sin(np.pi * (t[m] - s0) / d) ** 0.8
        return (S.sine(f, n) + 0.12 * S.sine(2 * f, n)) * amp
    if kind == 'chirrup':
        k = int(r.integers(4, 9))
        base = r.uniform(3500, 5000)
        out = S.zeros(0.065 * k + 0.05)
        for i in range(k):
            n = ns(0.025)
            t = times(n)
            S.place(out, S.sine(base * (1.2 - 0.4 * t / 0.025), n) * np.sin(np.pi * t / 0.025), i * 0.065)
        return out
    # coo: soft low two/three-note hoot
    out = S.zeros(1.4)
    tt = 0.0
    for f0 in (r.uniform(520, 580), r.uniform(460, 500), r.uniform(480, 520))[:int(r.integers(2, 4))]:
        d = r.uniform(0.25, 0.4)
        n = ns(d)
        t = times(n)
        f = f0 * (1 + 0.01 * np.sin(TAU * 6 * t))
        S.place(out, (S.sine(f, n) + 0.1 * S.sine(2 * f, n)) * np.sin(np.pi * t / d) ** 1.5 * 0.6, tt)
        tt += d + r.uniform(0.05, 0.15)
    return out


@sfx('amb_birds_loop', 'amb', 'Daytime meadow: gentle leaf-rustle bed with assorted songbird calls', loop=True)
def amb_birds_loop():
    L = 24.0
    n = ns(L)
    out = S.filt(S.pink(n), lambda f: S.H_bp(f, 2500, 0.5) * S.H_lp(f, 7000, 2), circular=True) \
        * (0.6 + 0.4 * np.tanh(S.smooth_noise(n, 0.2))) * 0.12
    r = S.rng()
    tt = r.uniform(0, 1)
    while tt < L:
        kind = r.choice(['tweet', 'warble', 'song', 'chirrup', 'coo'], p=[0.3, 0.2, 0.25, 0.15, 0.1])
        dist = r.uniform(0, 1)
        call = bird(kind, r)
        call = S.lp(call, 9000 - 5000 * dist) * (1 - 0.7 * dist)
        S.place(out, call, tt, circular=True)
        tt += r.uniform(0.7, 2.2)
    return rv(out, 'outdoor', 0.25, circular=True)


def cricket_chirp(fc, pulses, prate):
    out = S.zeros(pulses / prate + 0.03)
    for p in range(pulses):
        n = ns(0.012)
        t = times(n)
        S.place(out, (S.sine(fc, n) + 0.1 * S.sine(2 * fc, n)) * np.sin(np.pi * t / 0.012) ** 2, p / prate)
    return out


def frog(r):
    out = S.zeros(0.4)
    f0 = r.uniform(170, 240)
    for k in range(2):
        n = ns(0.09)
        t = times(n)
        src = S.harm(f0 * (1 - 0.05 * t / 0.09), n, bright=8) * (0.5 + 0.5 * np.sin(TAU * 45 * t)) \
            * np.sin(np.pi * t / 0.09) ** 0.8
        y = S.filt(src, lambda f: S.H_bp(f, 800, 2.0) + 0.5 * S.H_bp(f, 1600, 3.0))
        S.place(out, y, k * 0.14)
    return out


def owl(r):
    out = S.zeros(1.6)
    tt = 0.0
    for d in (0.35, 0.18, 0.4):
        n = ns(d)
        t = times(n)
        f = r.uniform(360, 390) * (1 - 0.04 * t / d)
        S.place(out, (S.sine(f, n) + 0.08 * S.sine(2 * f, n)) * np.sin(np.pi * t / d) ** 1.2, tt)
        tt += d + 0.12
    return S.lp(out, 1200)


@sfx('amb_night_loop', 'amb', 'Night: cricket chorus, the odd frog and a distant owl over a soft breeze', loop=True)
def amb_night_loop():
    L = 20.0
    n = ns(L)
    out = S.filt(S.brown(n), lambda f: S.H_lp(f, 400, 2), circular=True) \
        * (0.7 + 0.3 * np.tanh(S.smooth_noise(n, 0.1))) * 0.2
    r = S.rng()
    out *= 1.4
    for c in range(4):
        fc = r.uniform(4200, 5200)
        period = r.uniform(0.55, 0.9)
        chirp = cricket_chirp(fc, int(r.integers(2, 5)), r.uniform(28, 40))
        dist = r.uniform(0.4, 1.0)
        chirp = S.lp(chirp, 7500 - 3000 * dist) * (1 - 0.6 * dist) * 0.3
        tt = r.uniform(0, period)
        while tt < L:
            S.place(out, chirp * r.uniform(0.85, 1.0), tt, circular=True)
            tt += period * r.uniform(0.95, 1.05)
    for t0 in r.uniform(0, L, 4):
        S.place(out, frog(r) * r.uniform(0.2, 0.35), t0, circular=True)
    for t0 in (r.uniform(2, 6), r.uniform(12, 16)):
        S.place(out, owl(r) * 0.25, t0, circular=True)
    return rv(out, 'outdoor', 0.3, circular=True)


@sfx('amb_magic_loop', 'amb', 'Magical ambience: evolving D-major drone, airy shimmer and stray twinkles', loop=True)
def amb_magic_loop():
    L = 16.0
    n = ns(L)
    t = times(n)
    out = np.zeros(n)
    for nm, a, rate, ph in (('D3', 1.0, 1, 0), ('A3', 0.7, 2, 1), ('D4', 0.5, 3, 2), ('E4', 0.35, 1, 3),
                            ('F#4', 0.3, 2, 4), ('A4', 0.25, 3, 5)):
        f = hz(nm)
        sw = 0.6 + 0.4 * np.sin(TAU * rate / L * t + ph)
        out += a * sw * (S.sine(S.loopf(f, n), n) + 0.5 * S.sine(S.loopf(f * 1.003, n), n)
                         + 0.15 * S.sine(S.loopf(2 * f, n), n))
    out *= 0.18
    out += S.filt(S.pink(n), lambda f: S.H_bp(f, 3500, 0.6) * S.H_lp(f, 9000, 2), circular=True) \
        * (0.5 + 0.5 * np.sin(TAU * 2 / L * t + 1)) * 0.15
    r = S.rng()
    for _ in range(9):
        S.place(out, I.sparkle(1.2, 25, 2500, 8000, root=62) * 0.18, r.uniform(0, L), circular=True)
    tbl = I.scale_freqs(62, I.PENT, 900, 4000)
    for _ in range(12):
        S.place(out, I.bell(tbl[r.integers(len(tbl))], 2.0, 'celesta', t60=1.8, vel=0.5) * 0.1, r.uniform(0, L),
                circular=True)
    out = S.chorus(out, 3, rate=0.3, mix=0.3, circular=True)
    return rv(out, 'magic', 0.35, circular=True)


@sfx('amb_factory_loop', 'amb', 'Workshop floor: machine hum, rhythmic press, gear ticking and steam bursts',
     loop=True)
def amb_factory_loop():
    L = 16.0
    n = ns(L)
    t = times(n)
    out = (S.harm(S.loopf(60, n), n, bright=2.5) * 0.12 + S.sine(S.loopf(120, n), n) * 0.05) \
        * (1 + 0.05 * np.sin(TAU * t / 4))
    out += S.filt(S.brown(n), lambda f: S.H_lp(f, 200, 2), circular=True) * 0.25
    for k in range(8):
        t0 = 2.0 * k + 0.3
        S.place(out, I.thump(90, 45, 0.4, 0.03, 0.25) * 0.6, t0, circular=True)
        S.place(out, I.metal(260, 0.7, 0.45, bright=0.6, click_amt=0.3) * 0.25, t0, circular=True)
        S.place(out, I.hiss(0.7, 2500, 9000, 0.2, 15) * env_t(ns(0.7), [(0, 0), (0.05, 1), (0.7, 0)], curve=2) * 0.12,
                t0 + 0.25, circular=True)
    for k in range(int(L * 6)):
        S.place(out, I.metal(1900 if k % 3 else 1500, 0.04, 0.02, bright=0.6, click_amt=0.2) * 0.05, k / 6.0,
                circular=True)
    r = S.rng()
    for t0 in (5.1, 12.7):
        for j in range(3):
            S.place(out, I.metal(r.uniform(700, 900), 0.5, 0.35, bright=0.6, click_amt=0.4) * 0.12, t0 + 0.32 * j,
                    circular=True)
    out = S.filt(out, lambda f: S.H_lp(f, 8000, 2), circular=True)
    return rv(out, 'factory', 0.3, circular=True)


# ===========================================================================
# finishing
# ===========================================================================

def finalize(x, loop):
    x = np.asarray(x, float)
    if loop:
        x = S.filt(x, lambda f: S.H_hp(f, 25.0, 2), circular=True)
        return x - x.mean()
    x = S.hp(x, 25.0)
    x = S.trim_tail(x, -60.0, keep=0.02)
    return S.fade(x, 0.0015, min(0.03, len(x) / S.SR / 4))


def master(x, group, gain_db, loop):
    peak = float(np.max(np.abs(x)))
    L = S.loudness_int(x, circular=True) if loop else S.loudness_max(x, 0.2)
    g = TARGETS[group] + gain_db - L
    g = min(g, CEILING - S.a2db(peak) + MAX_LIMIT)
    y = x * S.db2a(g)
    ceil = CEILING
    for _ in range(4):  # re-limit until the true (inter-sample) peak is under the ceiling too
        y = S.limit(y, ceil, circular=loop)
        tp = float(S.a2db(S.true_peak(y)))
        if tp <= CEILING + 0.02:
            break
        ceil -= tp - CEILING + 0.02
    return y, g


def render(name):
    e = REG[name]
    S.seed(zlib.crc32(name.encode()))
    x = e['fn']()
    x = finalize(x, e['loop'])
    return master(x, e['group'], e['gain'], e['loop'])


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    want = [a for a in argv if not a.startswith('--')]
    names = [k for k, e in REG.items() if not want or k in want or e['group'] in want]
    t_all = time.time()
    for name in names:
        t0 = time.time()
        y, g = render(name)
        S.write_wav(os.path.join(OUT, name + '.wav'), y, loop=REG[name]['loop'])
        print('%-22s %5.2fs gain %+6.1f dB  (%.1fs)' % (name, len(y) / S.SR, g, time.time() - t0))
    print('rendered %d sounds in %.1fs' % (len(names), time.time() - t_all))
    if '--nopreview' not in argv:
        import qa
        qa.run_sfx(names if want else None)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
