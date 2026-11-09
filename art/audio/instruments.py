"""RuneWire instruments and sound-design building blocks, built on synth.py.

Shared by make_sfx.py and make_music.py. Every function returns a mono float
array starting at t = 0 unless noted.
"""
import math

import numpy as np

import synth as S
from synth import ns, times, TAU, SR

PENT = [0, 2, 4, 7, 9]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]
LYDIAN = [0, 2, 4, 6, 7, 9, 11]


def scale_freqs(root, degrees, lo, hi):
    """All frequencies of a scale (root midi, degree list) between lo and hi Hz."""
    out = []
    for o in range(-3, 10):
        for d in degrees:
            f = float(S.mtof(root + 12 * o + d))
            if lo <= f <= hi:
                out.append(f)
    return np.array(sorted(out))


def snap(f, table):
    return table[np.argmin(np.abs(np.log(table) - math.log(f)))]


# ---------------------------------------------------------------------------
# generic sound-design layers
# ---------------------------------------------------------------------------

def thump(f0=160.0, f1=50.0, dur=0.4, tau=0.035, t60=0.35, attack=0.0008):
    """Sine with an exponential pitch drop: kicks, impacts, punches."""
    n = ns(dur)
    t = times(n)
    f = f1 + (f0 - f1) * np.exp(-t / tau)
    return S.sine(f, n) * S.decay(n, t60, attack=attack)


def nburst(dur, lo=None, hi=None, t60=None, attack=0.001, color='white', fc=None, q=1.0,
           order=2):
    """Filtered noise burst with an exponential decay."""
    n = ns(dur)
    x = S.white(n) if color == 'white' else S.pink(n) * 3.0 if color == 'pink' else S.brown(n) * 3.0

    def H(f):
        g = np.ones_like(f)
        if lo:
            g = g * S.H_hp(f, lo, order)
        if hi:
            g = g * S.H_lp(f, hi, order)
        if fc:
            g = g * S.H_bp(f, fc, q)
        return g
    return S.filt(x, H) * S.decay(n, t60 or dur, attack=attack)


def click(dur=0.004, fc=3000.0, q=0.8, t=0.0012):
    n = ns(dur)
    x = S.white(n) * np.exp(-times(n) / t)
    return S.bp(x, fc, q)


def crackle(dur, rate=40.0, lo=1500.0, hi=7000.0, env=None, size=(0.0004, 0.003), spread=12.0):
    """Random sparse pops (fire crackle, sizzle, grit). env: callable t->0..1 density."""
    n = ns(dur)
    out = np.zeros(n)
    r = S.rng()
    k = r.poisson(rate * dur)
    for _ in range(k):
        tt = r.uniform(0, dur)
        if env is not None and r.uniform() > env(tt):
            continue
        m = max(4, ns(r.uniform(*size)))
        a = math.exp(-r.uniform(0, math.log(spread)))  # log-uniform loudness
        b = S.white(m) * np.exp(-np.arange(m) / (m / 3.0)) * a
        S.place(out, b, tt)
    return S.filt(out, lambda f: S.H_hp(f, lo, 2) * S.H_lp(f, hi, 2))


def whoosh(dur, f0, f1, q=1.2, peak=0.5, color='pink', amp=None, curve=1.0):
    """Band-pass swept noise. amp: optional per-sample envelope; default a hump
    peaking at `peak` (fraction of dur)."""
    n = ns(dur)
    x = S.pink(n) * 4.0 if color == 'pink' else S.white(n)
    fc = lambda t: f0 * (f1 / f0) ** (np.clip(t / dur, 0, 1) ** curve)
    y = S.sweep(x, 'bp', fc, q=q)
    if amp is None:
        u = times(n) / dur
        amp = np.where(u < peak, np.sin(0.5 * np.pi * u / peak) ** 2,
                       np.cos(0.5 * np.pi * np.clip((u - peak) / (1 - peak), 0, 1)) ** 2)
    return y * amp


def sparkle(dur, density=30.0, lo=2500.0, hi=9000.0, scale=PENT, root=72, grain=(0.04, 0.2),
            rise=0.0, env=None, jitter=0.6, partial2=0.22, detune=0.004):
    """Cloud of tiny bell grains (magic glitter). Pitches snap to a scale so the
    glitter stays musical. rise = octaves the pitch range drifts over the sound."""
    n = ns(dur)
    out = np.zeros(n)
    r = S.rng()
    table = scale_freqs(root, scale, lo * 0.25, hi * 4.0) if scale else None
    k = r.poisson(density * dur)
    for _ in range(k):
        tt = r.uniform(0, dur)
        w = env(tt) if env is not None else 1.0
        if w <= 0 or r.uniform() > w:
            continue
        sh = 2.0 ** (rise * tt / dur)
        f = math.exp(r.uniform(math.log(lo), math.log(hi))) * sh
        if table is not None:
            f = snap(f, table)
        if f > 0.42 * SR:
            continue
        gd = r.uniform(*grain)
        m = ns(gd)
        tg = times(m)
        e = np.exp(-6.9 * tg / gd)
        a = 1.0 - jitter * r.uniform()
        g = np.sin(TAU * f * tg) + 0.5 * np.sin(TAU * f * (1 + detune) * tg)
        if 2 * f < 0.42 * SR:
            g += partial2 * np.sin(TAU * 2.0 * f * tg) * np.exp(-12.0 * tg / gd)
        g *= e * a
        k1 = min(m, ns(0.001))
        g[:k1] *= np.linspace(0, 1, k1)
        S.place(out, g, tt)
    return out


def metal(f0, dur=1.0, t60=0.8, ratios=(1.0, 2.32, 4.25, 6.63, 9.38, 12.1),
          amps=(1.0, 0.7, 0.5, 0.32, 0.2, 0.12), bright=1.0, jitter=0.015, click_amt=0.25,
          damp=0.55):
    """Struck metal (plate/bar-like inharmonic modes)."""
    n = ns(dur)
    r = S.rng()
    modes = []
    for i, (ra, a) in enumerate(zip(ratios, amps)):
        f = f0 * ra * (1.0 + jitter * r.standard_normal())
        modes.append((f, a * bright ** i, t60 / (1.0 + damp * i)))
        modes.append((f * 1.0031, 0.35 * a * bright ** i, t60 / (1.0 + damp * i)))
    y = S.modal(n, modes)
    if click_amt:
        S.place(y, click(0.005, min(3.5 * f0, 9000.0), 0.7) * click_amt * 4.0, 0)
    return y


def wood(f0=200.0, dur=0.4, t60=0.12, bright=1.0, click_amt=0.4):
    n = ns(dur)
    ratios = (1.0, 2.31, 3.9, 5.7, 8.1)
    amps = (1.0, 0.55, 0.3, 0.16, 0.08)
    tms = (1.0, 0.6, 0.42, 0.3, 0.2)
    modes = [(f0 * r_, a * bright ** i, t60 * tm) for i, (r_, a, tm) in enumerate(zip(ratios, amps, tms))]
    y = S.modal(n, modes)
    if click_amt:
        S.place(y, click(0.006, min(6.0 * f0, 6000.0), 0.6) * click_amt * 4.0, 0)
    return y


def zap(dur, f_base=90.0, jitter=0.35, lo=300.0, hi=7000.0, amount=3.0, sizzle=0.5):
    """Electric arc: jittery buzz + random crackle, saturated."""
    n = ns(dur)
    fj = f_base * np.exp(jitter * S.smooth_noise(n, 25.0))
    buzz = S.saw(fj, n)
    am = 0.55 + 0.45 * np.tanh(1.5 * S.smooth_noise(n, 90.0))
    gate = (S.smooth_noise(n, 300.0) > 0.9).astype(float)
    y = buzz * am + sizzle * S.white(n) * gate
    y = S.drive(y, amount)
    return S.filt(y, lambda f: S.H_hp(f, lo, 2) * S.H_lp(f, hi, 2))


def servo(dur, f0, f1, wobble=0.015, bright=3.0, rate=7.0):
    """Motor whine gliding from f0 to f1."""
    n = ns(dur)
    t = times(n)
    f = f0 * (f1 / f0) ** (t / max(dur, 1e-6)) * (1.0 + wobble * np.sin(TAU * rate * t))
    return S.harm(f, n, bright=bright, kind='square', even=0.35)


def hiss(dur, lo=2500.0, hi=11000.0, flutter=0.15, rate=18.0):
    n = ns(dur)
    y = S.filt(S.white(n), lambda f: S.H_hp(f, lo, 2) * S.H_lp(f, hi, 2))
    return y * (1.0 + flutter * S.smooth_noise(n, rate))


VOWELS = {
    'a': [(730, 1.0, 90), (1090, 0.5, 110), (2440, 0.22, 160), (3400, 0.08, 250)],
    'e': [(530, 1.0, 80), (1840, 0.45, 120), (2480, 0.28, 160), (3500, 0.08, 250)],
    'i': [(300, 1.0, 60), (2290, 0.35, 120), (3010, 0.25, 170), (3700, 0.08, 250)],
    'o': [(570, 1.0, 80), (840, 0.55, 100), (2410, 0.12, 160), (3400, 0.05, 250)],
    'u': [(320, 1.0, 60), (870, 0.35, 90), (2240, 0.07, 160), (3300, 0.03, 250)],
}


def _formant_gain(f, fs, gs, bws):
    g = np.zeros(np.broadcast(f, fs[0]).shape)
    for fk, gk, bk in zip(fs, gs, bws):
        g = g + gk * S.H_bp(f, fk, fk / bk)
    return g


def formant(x, path, scale=1.0, circular=False):
    """Vowel filter. path = [(t, 'a'), (t2, 'o'), ...] interpolated over time."""
    ts = np.array([p[0] for p in path])
    V = [VOWELS[p[1]] for p in path]
    F = np.array([[v[k][0] for k in range(4)] for v in V]) * scale
    G = np.array([[v[k][1] for k in range(4)] for v in V])
    B = np.array([[v[k][2] for k in range(4)] for v in V]) * math.sqrt(scale)

    def Hfn(t, f):
        tt = t[:, 0]
        fs = [np.exp(np.interp(tt, ts, np.log(F[:, k])))[:, None] for k in range(4)]
        gs = [np.interp(tt, ts, G[:, k])[:, None] for k in range(4)]
        bs = [np.interp(tt, ts, B[:, k])[:, None] for k in range(4)]
        return _formant_gain(f, fs, gs, bs)
    return S.tvfilt(x, Hfn, frame=1024, circular=circular)


# ---------------------------------------------------------------------------
# tuned percussion
# ---------------------------------------------------------------------------

BELLS = {
    # (ratio, amp, t60 scale)
    'glock': [(1.0, 1.0, 1.0), (2.756, 0.25, 0.35), (5.404, 0.1, 0.15), (8.933, 0.04, 0.08)],
    'celesta': [(1.0, 1.0, 1.0), (2.0, 0.2, 0.4), (3.0, 0.05, 0.25), (4.0, 0.07, 0.15), (6.27, 0.04, 0.06)],
    'coin': [(1.0, 1.0, 1.0), (2.0, 0.45, 0.55), (3.0, 0.2, 0.35), (4.16, 0.16, 0.25),
             (5.43, 0.08, 0.15), (6.79, 0.05, 0.1)],
    'chime': [(1.0, 1.0, 1.0), (2.76, 0.4, 0.5), (5.40, 0.22, 0.3), (8.93, 0.1, 0.2)],
    'vibes': [(1.0, 1.0, 1.0), (4.0, 0.22, 0.3), (10.0, 0.05, 0.1)],
    'musicbox': [(1.0, 1.0, 1.0), (2.0, 0.08, 0.3), (5.93, 0.15, 0.12), (13.7, 0.05, 0.04)],
    'crystal': [(1.0, 1.0, 1.0), (2.32, 0.45, 0.6), (4.25, 0.3, 0.4), (6.63, 0.18, 0.25), (9.38, 0.08, 0.15)],
    'marimba': [(1.0, 1.0, 1.0), (3.93, 0.18, 0.18), (9.2, 0.04, 0.06)],
}


def bell(freq, dur, kind='glock', t60=1.2, vel=1.0, mallet=0.25, detune=0.0, trem=0.0):
    """Modal bell family (glock, celesta, coin, chime, vibes, musicbox, crystal, marimba)."""
    n = ns(dur)
    modes = []
    for r_, a, tm in BELLS[kind]:
        f = freq * r_
        if f > 0.43 * SR:
            continue
        a2 = a * (vel ** 0.5 if r_ > 1.5 else 1.0)
        modes.append((f, a2, t60 * tm))
        if detune:
            modes.append((f * (1.0 + detune), a2 * 0.6, t60 * tm))
    y = S.modal(n, modes)
    if trem:
        y *= 1.0 - trem * (0.5 - 0.5 * np.cos(TAU * 5.5 * times(n)))
    if mallet:
        S.place(y, click(0.004, min(freq * 3.0, 10000.0), 0.8) * mallet * 3.0 * vel, 0)
    return S.fade(y, 0.0, 0.01) * vel


PLUCKS = {
    'harp': dict(t60=2.4, stretch=0.32, bright=5200.0, pick=0.24, sub=0.0,
                 body=[(230.0, 2.0, 1.2), (1800.0, 1.5, 1.5)]),
    'pizz': dict(t60=0.55, stretch=0.5, bright=2800.0, pick=0.2, sub=0.0,
                 body=[(290.0, 3.0, 1.3), (520.0, 2.0, 1.5), (3200.0, -4.0, 2.0)]),
    'guitar': dict(t60=1.6, stretch=0.4, bright=3800.0, pick=0.14, sub=0.0,
                   body=[(110.0, 3.0, 1.0), (230.0, 2.0, 1.0)]),
    'bass': dict(t60=1.4, stretch=0.5, bright=1300.0, pick=0.24, sub=0.45,
                 body=[(95.0, 2.0, 1.0), (2000.0, -6.0, 2.0)]),
}


def pluck(freq, dur, kind='harp', vel=1.0, rel=0.08):
    p = PLUCKS[kind]
    y = S.ks_pluck(freq, dur, t60=p['t60'], stretch=p['stretch'],
                   bright=p['bright'] * (0.45 + 0.55 * vel), pick=p['pick'])
    if p['sub']:
        n = len(y)
        y = y + p['sub'] * S.sine(freq, n) * S.decay(n, p['t60'] * 0.8, attack=0.003)
    body = p['body']
    y = S.filt(y, lambda f: np.prod([S.H_bell(f, fc, g, w) for fc, g, w in body], axis=0) * S.H_hp(f, 40.0, 2))
    return S.fade(y, 0.0004, rel) * vel


# ---------------------------------------------------------------------------
# sustained instruments
# ---------------------------------------------------------------------------

def brass(freq, dur, vel=1.0, voices=2, detune=7.0, vib=0.0045, bright=6.0, attack=0.045,
          release=0.14, scoop=0.012):
    """Additive brass: brightness follows loudness, a little pitch scoop and vibrato."""
    n = ns(dur + release)
    t = times(n)
    amp = S.adsr(n, a=attack, d=0.3, s=0.82, r=release, gate=dur)
    bump = np.exp(-np.maximum(t - attack * 0.6, 0) / 0.09)
    B = 1.0 + (bright * vel - 1.0) * amp * (0.8 + 0.6 * bump)
    vib_env = np.clip((t - 0.22) / 0.25, 0, 1)
    out = np.zeros(n)
    r = S.rng()
    for v in range(voices):
        c = (v - (voices - 1) / 2.0) * detune
        f = freq * 2 ** (c / 1200.0) * (1.0 - scoop * np.exp(-t / 0.035)) \
            * (1.0 + vib * vib_env * np.sin(TAU * (5.3 + 0.2 * v) * t + v))
        out += S.harm(f, n, bright=B, kind='saw', max_h=48, ph0=r.uniform())
    return out * amp / voices


def strings(freq, dur, vel=1.0, voices=3, detune=8.0, attack=0.008, release=0.09, bright=7.0,
            sus=0.45, decay_t=0.12):
    """Ensemble strings, staccato by default (longer notes: raise sus/attack)."""
    n = ns(dur + release)
    t = times(n)
    amp = S.adsr(n, a=attack, d=decay_t, s=sus, r=release, gate=dur)
    B = 1.5 + bright * vel * amp
    out = np.zeros(n)
    r = S.rng()
    for v in range(voices):
        c = (v - (voices - 1) / 2.0) * detune
        f = freq * 2 ** (c / 1200.0) * (1.0 + 0.003 * np.sin(TAU * (5.0 + 0.4 * v) * t + 2 * v))
        out += S.harm(f, n, bright=B, kind='saw', max_h=48, ph0=r.uniform())
    bow = S.filt(S.white(n), lambda f: S.H_bp(f, 3200.0, 0.8)) * np.exp(-t / 0.02) * 0.25 * vel
    return (out / voices + bow) * amp


def synth_bass(freq, dur, vel=1.0, bright=6.0, sub=0.6, release=0.06, drive_amt=1.6):
    n = ns(dur + release)
    t = times(n)
    amp = S.adsr(n, a=0.004, d=0.18, s=0.65, r=release, gate=dur)
    B = 1.3 + bright * vel * np.exp(-t / 0.08)
    y = S.harm(freq, n, bright=B, kind='saw', max_h=40) + sub * S.sine(freq, n)
    return S.drive(y * amp, drive_amt) * 0.8


def pad(freq, dur, kind='warm', attack=0.6, release=1.2, voices=3, detune=10.0, bright=4.0,
        drift=0.0015):
    """Pad voice. kinds: warm (soft saw ensemble), glass (sine + soft square),
    choir (bright saws for formant filtering)."""
    n = ns(dur + release)
    t = times(n)
    env = S.adsr(n, a=attack, d=0.6, s=0.85, r=release, gate=dur)
    out = np.zeros(n)
    r = S.rng()
    for v in range(voices):
        c = (v - (voices - 1) / 2.0) * detune / max(1.0, (voices - 1) / 2.0)
        f = freq * 2 ** (c / 1200.0) * (1.0 + drift * np.sin(TAU * (0.21 + 0.07 * v) * t + 1.7 * v))
        if kind == 'warm':
            out += S.harm(f, n, bright=bright, kind='saw', ph0=r.uniform())
        elif kind == 'glass':
            out += 0.75 * S.sine(f, n, r.uniform()) + 0.35 * S.harm(f, n, bright=bright, kind='square',
                                                                      ph0=r.uniform())
        elif kind == 'choir':
            out += S.harm(f, n, bright=bright * 3.0, kind='saw', ph0=r.uniform())
        else:
            raise ValueError(kind)
    return out * env / voices


FLUTE = [1.0, 0.36, 0.16, 0.08, 0.04, 0.02]
CLARINET = [1.0, 0.03, 0.55, 0.04, 0.32, 0.03, 0.18, 0.02, 0.09]
OCARINA = [1.0, 0.12, 0.05, 0.02]


def mono_line(notes, timbre=FLUTE, glide=0.035, vib_rate=5.2, vib_depth=0.006, vib_delay=0.2,
              attack=0.045, release=0.12, breath=0.05, chiff=0.18, tail=0.3, trem=0.35,
              bright_vel=0.6, brass=0.0, detune=0.0):
    """Render a legato monophonic phrase (flute, clarinet, ocarina, horn...).

    notes: [(t0, dur, freq, vel), ...] in seconds, sorted. Consecutive notes
    that touch are slurred (pitch glides, no re-attack). brass > 0 switches the
    tone to a band-limited saw whose brightness follows the loudness (horn).
    detune shifts the whole line in cents (for ensemble doubling).
    Returns (signal, t_first).
    """
    t_first = notes[0][0]
    t_last = max(nt[0] + nt[1] for nt in notes) + release + tail
    n = ns(t_last - t_first)
    t = times(n)
    logf = np.full(n, math.log(notes[0][2]))
    amp = np.zeros(n)
    vib = np.zeros(n)
    vel_curve = np.zeros(n)
    ch = np.zeros(n)
    bump = np.zeros(n)
    r = S.rng()
    for i, (t0, d, f, v) in enumerate(notes):
        a = ns(t0 - t_first)
        nxt = notes[i + 1] if i + 1 < len(notes) else None
        prv = notes[i - 1] if i > 0 else None
        slur_in = prv is not None and t0 - (prv[0] + prv[1]) < 0.015
        slur_out = nxt is not None and nxt[0] - (t0 + d) < 0.015
        hold_end = ns(nxt[0] - t_first) if nxt else n
        logf[a:hold_end] = math.log(f)
        end_t = (t0 + d - t_first) + (0.03 if slur_out else 0.0)
        tt = t - (t0 - t_first)
        att = attack * (0.5 if slur_in else 1.0)
        s0 = 0.75 if slur_in else 0.0
        e = np.where(tt < att, s0 + (1 - s0) * np.sin(0.5 * np.pi * np.clip(tt / att, 0, 1)), 1.0)
        e *= np.exp(-np.maximum(tt - att, 0) * 0.15)  # gentle sag on long notes
        rel = np.clip((t - end_t) / release, 0, 1)
        e *= np.where(t < end_t, 1.0, np.exp(-4.6 * rel) * (1 - rel))
        e[tt < 0] = 0.0
        amp = np.maximum(amp, e * v)
        ve = np.clip((tt - vib_delay) / 0.3, 0, 1) * (t < end_t + 0.05)
        vib = np.maximum(vib, ve)
        m = (tt >= 0) & (t < end_t + release)
        vel_curve[m] = v
        if not slur_in:
            bump = np.maximum(bump, np.where(tt >= 0, np.exp(-np.maximum(tt, 0) / 0.12), 0.0))
        if chiff and not slur_in:
            cb = S.filt(S.white(ns(0.05)), lambda fr: S.H_bp(fr, min(f * 2.0, 9000.0), 1.2)) \
                * np.exp(-times(ns(0.05)) / 0.012)
            S.place(ch, cb * v * chiff, a)
    # centred glide smoothing of the pitch curve
    g = max(1, ns(glide))
    k = np.ones(g) / g
    lf = np.convolve(np.concatenate([np.full(g, logf[0]), logf, np.full(g, logf[-1])]), k, 'same')[g:g + n]
    wob = 1.0 + 0.12 * S.smooth_noise(n, 0.7)
    vphase = TAU * np.cumsum(vib_rate * wob) / SR + r.uniform(0, TAU)
    vsig = np.sin(vphase)
    freq = np.exp(lf) * (1.0 + vib_depth * vib * vsig) * 2 ** (detune / 1200.0)
    if brass > 0:
        B = 1.0 + brass * amp * (0.7 + 0.3 * vel_curve) * (1.0 + 0.45 * bump)
        tone = S.harm(freq, n, bright=B, kind='saw', max_h=48, ph0=r.uniform())
    else:
        parts = []
        for k_, a_ in enumerate(timbre):
            parts.append((k_ + 1, a_ * (bright_vel * vel_curve + (1 - bright_vel)) ** (0.6 * k_)))
        tone = S.additive(freq, n, parts)
    tone *= 1.0 + trem * 0.1 * vib * vsig  # flute vibrato is partly amplitude
    br = S.filt(S.white(n), lambda fr: S.H_bp(fr, 2800.0, 0.6)) * breath
    y = tone * amp + br * amp + ch
    return y, t_first


# ---------------------------------------------------------------------------
# drums and percussion
# ---------------------------------------------------------------------------

def kick(vel=1.0, f0=150.0, f1=48.0, tau=0.03, t60=0.45, click_amt=0.25, amount=1.4):
    y = thump(f0, f1, t60 * 1.1, tau, t60, attack=0.0006)
    c = nburst(0.006, lo=1500.0, t60=0.004, attack=0.0002) * click_amt
    S.place(y, c, 0)
    return S.drive(y * vel, amount) / math.tanh(amount)


def snare(vel=1.0, tone=185.0, t60=0.22, snappy=0.8, bright=1.0):
    n = ns(0.4)
    t = times(n)
    body = (S.sine(tone * (1 + 0.25 * np.exp(-t / 0.012)), n) + 0.45 * S.sine(tone * 1.78, n)) \
        * S.decay(n, 0.13, attack=0.0005)
    nz = S.filt(S.white(n), lambda f: S.H_hp(f, 1100.0, 2) * S.H_lp(f, 8500.0 * bright, 2)
                * S.H_bell(f, 4500.0, 3.0, 1.5)) * S.decay(n, t60, attack=0.0008)
    return (0.55 * body + snappy * 1.6 * nz) * vel


_HATF = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)


def hat(vel=1.0, open_=False, t60=None):
    n = ns(0.6 if open_ else 0.12)
    m = sum(S.square(f * 1.47, n, ph0=i * 0.13) for i, f in enumerate(_HATF))
    x = 0.35 * m + S.white(n)
    y = S.filt(x, lambda f: S.H_hp(f, 7000.0, 3) * S.H_lp(f, 15000.0, 2))
    return y * S.decay(n, t60 or (0.45 if open_ else 0.055), attack=0.0004) * vel * 0.6


def shaker(vel=1.0, length=0.07, fc=7000.0):
    n = ns(length * 2.5)
    t = times(n)
    tp = length * 0.35                       # swell up to the peak, then a fast fall
    env = (t / tp) ** 2 * np.exp(2.0 * (1.0 - t / tp))
    y = S.filt(S.white(n), lambda f: S.H_bp(f, fc, 0.8) * S.H_hp(f, 2500.0, 2))
    return S.fade(y * env, 0.0, 0.01) * vel * 0.8


def tamb(vel=1.0):
    n = ns(0.4)
    r = S.rng()
    modes = [(r.uniform(4500, 11000), r.uniform(0.3, 1.0), r.uniform(0.08, 0.22)) for _ in range(10)]
    j = S.modal(n, modes) * 0.25
    nz = S.filt(S.white(n), lambda f: S.H_hp(f, 5000.0, 2)) * S.decay(n, 0.14, attack=0.001)
    return (j + 0.6 * nz) * vel


def woodblock(freq=900.0, vel=1.0):
    n = ns(0.18)
    y = S.modal(n, [(freq, 1.0, 0.07), (freq * 2.53, 0.35, 0.035), (freq * 3.93, 0.12, 0.02)])
    S.place(y, click(0.003, freq * 3, 0.7) * 1.5, 0)
    return y * vel


def tom(freq=110.0, vel=1.0, t60=0.5, skin=0.3):
    n = ns(t60 * 1.15)
    t = times(n)
    f = freq * (1.0 + 0.35 * np.exp(-t / 0.025))
    y = S.sine(f, n) * S.decay(n, t60, attack=0.0006)
    y += 0.3 * S.sine(f * 1.59, n) * S.decay(n, t60 * 0.4)
    y += 0.15 * S.sine(f * 2.14, n) * S.decay(n, t60 * 0.25)
    S.place(y, nburst(0.04, hi=3000.0, t60=0.03) * skin * 2.0, 0)
    return y * vel


def taiko(freq=60.0, vel=1.0, t60=0.9):
    y = tom(freq, 1.0, t60, skin=0.45)
    y = S.drive(y, 1.5) / math.tanh(1.5)
    return y * vel


def timpani(freq, vel=1.0, t60=1.8):
    n = ns(t60 * 1.1)
    modes = [(freq * r_, a, t60 * tm) for r_, a, tm in
             ((1.0, 1.0, 1.0), (1.504, 0.45, 0.7), (1.742, 0.3, 0.6), (2.0, 0.22, 0.5),
              (2.245, 0.14, 0.4), (2.494, 0.08, 0.3))]
    y = S.modal(n, modes)
    S.place(y, 0.4 * thump(freq * 1.2, freq * 0.5, t60 * 0.6, 0.02, t60 * 0.4), 0)
    S.place(y, nburst(0.03, hi=2000.0, t60=0.025) * 0.5, 0)
    return y * vel


def crash(vel=1.0, t60=2.2):
    n = ns(t60)
    m = sum(S.square(f * 2.9, n, ph0=i * 0.21) for i, f in enumerate(_HATF))
    x = 0.25 * m + S.white(n)
    x = S.filt(x, lambda f: S.H_hp(f, 3000.0, 2) * S.H_bell(f, 5500.0, 3.0, 1.5))
    x = S.sweep(x, 'lp', lambda tt: 4500.0 + 10000.0 * np.exp(-np.maximum(tt, 0) / 0.5))
    env = S.decay(n, t60, attack=0.002) * (1.0 + 0.8 * np.exp(-times(n) / 0.04))
    return x * env * vel * 0.5


def triangle_inst(vel=1.0, freq=1250.0, t60=2.5):
    n = ns(t60)
    rs = (1.0, 2.03, 3.06, 4.11, 5.18, 6.42, 7.61, 9.12)
    modes = [(freq * r_, 1.0 / (1 + 0.5 * i), t60 / (1 + 0.35 * i)) for i, r_ in enumerate(rs)]
    y = S.modal(n, modes)
    S.place(y, click(0.003, 6000.0, 0.8), 0)
    return y * vel * 0.35


def clap(vel=1.0):
    n = ns(0.3)
    out = np.zeros(n)
    for k, dt in enumerate((0.0, 0.011, 0.022)):
        S.place(out, nburst(0.03 if k < 2 else 0.2, fc=1300.0, q=1.1, t60=0.012 if k < 2 else 0.16), dt)
    return out * vel
