"""RuneWire procedural audio toolkit: a small numpy-only DSP library.

Used by make_sfx.py and make_music.py. Run those under Blender's bundled
Python, which has numpy (the system python3 does not):

    env -u LD_LIBRARY_PATH blender --background --factory-startup --python art/audio/make_sfx.py

Conventions
-----------
* Signals are float64 numpy arrays at SR. Mono is shape (n,), stereo is (2, n).
* Times are in seconds, frequencies in Hz.
* Functions that take ``circular=True`` treat the signal as one period of a
  loop: filters, delays and reverbs wrap their tails around the end, so the
  result loops seamlessly.
* Randomness comes from a module RNG; call ``seed(n)`` before building each
  sound so every asset is reproducible.
"""
import math
import struct

import numpy as np

SR = 44100
TAU = 2.0 * math.pi

_rng = np.random.default_rng(0)


# ---------------------------------------------------------------------------
# basics
# ---------------------------------------------------------------------------

def seed(s):
    global _rng
    _rng = np.random.default_rng(s)


def rng():
    return _rng


def ns(sec):
    """Seconds -> whole samples."""
    return max(0, int(round(float(sec) * SR)))


def times(n):
    return np.arange(n) / SR


def db2a(d):
    return 10.0 ** (np.asarray(d, float) / 20.0)


def a2db(a):
    return 20.0 * np.log10(np.maximum(np.abs(a), 1e-12))


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, float) - 69.0) / 12.0)


_NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi(name):
    """'C4' -> 60, 'F#3' -> 54, 'Bb2' -> 46. Numbers pass through."""
    if not isinstance(name, str):
        return float(name)
    s = name.strip()
    n = _NOTE[s[0].upper()]
    i = 1
    while i < len(s) and s[i] in '#b':
        n += 1 if s[i] == '#' else -1
        i += 1
    return 12 * (int(s[i:]) + 1) + n


def hz(name):
    return float(mtof(midi(name)))


def good_size(n):
    """Smallest 2^a 3^b 5^c >= n (fast FFT length)."""
    n = int(max(n, 1))
    best = 1 << (n - 1).bit_length()
    p5 = 1
    while p5 < best:
        p35 = p5
        while p35 < best:
            p = p35
            while p < n:
                p *= 2
            best = min(best, p)
            p35 *= 3
        p5 *= 5
    return best


def arr(v, n):
    a = np.asarray(v, dtype=float)
    if a.ndim == 0:
        return np.full(n, float(a))
    if a.shape[-1] != n:
        raise ValueError('length %d != %d' % (a.shape[-1], n))
    return a


def loopf(f, n):
    """Nearest frequency that fits a whole number of cycles in n samples."""
    k = max(1, int(round(f * n / SR)))
    return k * SR / n


def zeros(sec):
    return np.zeros(ns(sec))


# ---------------------------------------------------------------------------
# envelopes
# ---------------------------------------------------------------------------

def env_pts(pts, n, curve=None):
    """Piecewise envelope through (time, value) points; holds the end values.

    curve=None is linear. A number k bends every segment exponentially:
    k > 0 changes fast at the start of the segment (natural decays and
    attacks), k < 0 changes slowly first.
    """
    t = times(n)
    ts = np.array([p[0] for p in pts], float)
    vs = np.array([p[1] for p in pts], float)
    out = np.interp(t, ts, vs)
    if curve is None or abs(curve) < 1e-6:
        return out
    for i in range(len(ts) - 1):
        t0, t1 = ts[i], ts[i + 1]
        if t1 <= t0:
            continue
        a, b = np.searchsorted(t, [t0, t1])
        if b <= a:
            continue
        u = (t[a:b] - t0) / (t1 - t0)
        s = (1.0 - np.exp(-curve * u)) / (1.0 - math.exp(-curve))
        out[a:b] = vs[i] + (vs[i + 1] - vs[i]) * s
    return out


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, gate=None):
    """ADSR. gate = time (s) the release starts; default n/SR - r."""
    t = times(n)
    if gate is None:
        gate = n / SR - r
    gate = max(float(gate), 0.0)

    def pre(tt):
        e = np.empty_like(tt)
        m = tt < a
        e[m] = np.sin(0.5 * np.pi * tt[m] / a) if a > 0 else 1.0
        e[~m] = s + (1.0 - s) * np.exp(-(tt[~m] - a) / max(d / 4.0, 1e-5))
        return e

    env = pre(t)
    lg = pre(np.array([gate]))[0]
    m = t >= gate
    u = (t[m] - gate) / max(r, 1e-5)
    env[m] = np.where(u < 1.0, lg * np.exp(-4.6 * u) * (1.0 - u), 0.0)
    return env


def decay(n, t60, attack=0.0, hold=0.0):
    """Exponential decay reaching -60 dB after t60 s, optional sine attack."""
    t = times(n)
    e = np.exp(-6.9078 * np.maximum(t - attack - hold, 0.0) / t60)
    if attack > 0:
        e = e * np.where(t < attack, np.sin(0.5 * np.pi * np.clip(t / attack, 0, 1)), 1.0)
    return e


def fade(x, fin=0.002, fout=0.01):
    """Raised-cosine fade in/out (in place on a copy)."""
    x = np.array(x, float, copy=True)
    n = x.shape[-1]
    a = min(ns(fin), n // 2)
    b = min(ns(fout), n // 2)
    if a > 0:
        x[..., :a] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if b > 0:
        x[..., n - b:] *= 0.5 + 0.5 * np.cos(np.pi * (np.arange(b) + 1) / b)
    return x


def smooth_noise(n, rate, circular=True):
    """Smooth random curve (unit std) with content below ~rate Hz. Periodic over n."""
    X = np.fft.rfft(_rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    X *= np.exp(-(f / max(rate, 1e-3)) ** 2)
    X[0] = 0.0
    y = np.fft.irfft(X, n)
    return y / (np.std(y) + 1e-12)


# ---------------------------------------------------------------------------
# oscillators (all band-limited)
# ---------------------------------------------------------------------------

def phase(freq, n, ph0=0.0):
    """Running phase in cycles; sample 0 has phase ph0."""
    f = arr(freq, n)
    ph = np.empty(n)
    ph[0] = 0.0
    if n > 1:
        np.cumsum(f[:-1], out=ph[1:])
        ph[1:] /= SR
    return ph + ph0


def sine(freq, n, ph0=0.0):
    return np.sin(TAU * phase(freq, n, ph0))


def _blep(ph, dt):
    out = np.zeros_like(ph)
    m = ph < dt
    if m.any():
        t = ph[m] / dt[m]
        out[m] = t + t - t * t - 1.0
    m = ph > 1.0 - dt
    if m.any():
        t = (ph[m] - 1.0) / dt[m]
        out[m] = t * t + t + t + 1.0
    return out


def saw(freq, n, ph0=0.0):
    """PolyBLEP sawtooth in [-1, 1]."""
    f = arr(freq, n)
    dt = np.clip(np.abs(f) / SR, 1e-9, 0.49)
    ph = phase(f, n, ph0) % 1.0
    return 2.0 * ph - 1.0 - _blep(ph, dt)


def square(freq, n, pw=0.5, ph0=0.0):
    """PolyBLEP pulse wave; pw may be an array (PWM)."""
    f = arr(freq, n)
    dt = np.clip(np.abs(f) / SR, 1e-9, 0.49)
    ph = phase(f, n, ph0) % 1.0
    p = arr(pw, n)
    y = np.where(ph < p, 1.0, -1.0)
    y += _blep(ph, dt)
    y -= _blep((ph - p) % 1.0, dt)
    return y


def additive(freq, n, partials, ph0=0.0, fmax=None):
    """Sum of sine partials [(ratio, amp[, phase_cycles]), ...]; amp may be an array.
    Partials fade out smoothly as they approach fmax (default 0.45*SR)."""
    fmax = 0.45 * SR if fmax is None else fmax
    f = np.abs(arr(freq, n))
    ph = phase(freq, n, ph0)
    fmin_, fpk = f.min(), f.max()
    out = np.zeros(n)
    for p in partials:
        r, a = p[0], p[1]
        off = p[2] if len(p) > 2 else 0.0
        if r * fmin_ >= fmax:
            continue
        x = np.sin(TAU * (r * ph + off))
        if r * fpk > 0.8 * fmax:
            x *= np.clip((fmax - r * f) / (0.2 * fmax), 0.0, 1.0)
        out += np.asarray(a) * x
    return out


def tri(freq, n, ph0=0.0):
    parts = [(k, (8.0 / np.pi ** 2) * (-1.0) ** ((k - 1) // 2) / (k * k)) for k in range(1, 40, 2)]
    return additive(freq, n, parts, ph0)


def harm(freq, n, bright=8.0, kind='saw', max_h=64, fmax=None, ph0=0.0, even=1.0, tilt=1.0):
    """Band-limited harmonic tone with time-varying brightness.

    Harmonic k has amplitude base_k * exp(-(k-1)/bright), with base_k = 1/k^tilt
    (saw) or odd-only (square; even harmonics scaled by `even`). `bright` may be
    an array, which gives brass/string style "brightness follows loudness".
    Uses the Chebyshev recurrence so it costs ~3 multiply-adds per harmonic.
    """
    fmax = 0.45 * SR if fmax is None else fmax
    f = np.abs(arr(freq, n))
    B = np.maximum(arr(bright, n), 1e-3)
    th = TAU * phase(freq, n, ph0)
    c2 = 2.0 * np.cos(th)
    s_prev = np.zeros(n)
    s_cur = np.sin(th)
    out = np.zeros(n)
    K = int(min(max_h, fmax / max(f.min(), 1.0), 7.0 * B.max() + 2))  # exp(-7) ~ -60 dB
    fpk = f.max()
    for k in range(1, K + 1):
        if k > 1:
            s_next = c2 * s_cur - s_prev
            s_prev, s_cur = s_cur, s_next
        if kind == 'square' and k % 2 == 0:
            base = even / k ** tilt
            if base == 0.0:
                continue
        else:
            base = 1.0 / k ** tilt
        g = base * np.exp(-(k - 1) / B)
        if k * fpk > 0.8 * fmax:
            g = g * np.clip((fmax - k * f) / (0.2 * fmax), 0.0, 1.0)
        out += g * s_cur
    return out


def fm(freq, n, ratio=1.0, index=1.0, ph0=0.0, mod_freq=None, fb_shape=None):
    """Two-operator FM (phase modulation). index may be an array."""
    f = arr(freq, n)
    phc = phase(f, n, ph0)
    fmod = f * ratio if mod_freq is None else arr(mod_freq, n)
    phm = phase(fmod, n)
    return np.sin(TAU * phc + arr(index, n) * np.sin(TAU * phm))


# ---------------------------------------------------------------------------
# noise
# ---------------------------------------------------------------------------

def white(n):
    return _rng.uniform(-1.0, 1.0, n)


def gauss(n):
    return _rng.standard_normal(n)


def colored(n, slope_db=-3.0, lo=20.0, hi=None):
    """Noise with a spectral slope in dB/octave (-3 pink, -6 brown). Periodic over n,
    normalised to RMS 0.25."""
    X = np.fft.rfft(_rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = (np.maximum(f, lo) / 1000.0) ** (slope_db / 6.0206)
    if hi:
        g *= H_lp(f, hi, 2)
    g[0] = 0.0
    y = np.fft.irfft(X * g, n)
    return 0.25 * y / (np.sqrt(np.mean(y * y)) + 1e-12)


def pink(n, **kw):
    return colored(n, -3.0, **kw)


def brown(n, **kw):
    return colored(n, -6.0, **kw)


# ---------------------------------------------------------------------------
# static zero-phase FFT filters
# ---------------------------------------------------------------------------

def H_lp(f, fc, order=2):
    return 1.0 / np.sqrt(1.0 + (np.asarray(f) / fc) ** (2 * order))


def H_hp(f, fc, order=2):
    f = np.maximum(np.asarray(f, float), 1e-6)
    return 1.0 / np.sqrt(1.0 + (fc / f) ** (2 * order))


def H_bp(f, fc, q=1.0):
    """2nd-order band-pass magnitude, unity at fc."""
    x = np.maximum(np.asarray(f, float), 1e-6) / fc
    return 1.0 / np.sqrt(1.0 + (q * (x - 1.0 / x)) ** 2)


def H_res(f, fc, q=0.707):
    """Resonant 2-pole low-pass magnitude (peak ~q at fc)."""
    x = np.asarray(f, float) / fc
    return 1.0 / np.sqrt((1.0 - x * x) ** 2 + (x / q) ** 2)


def H_bell(f, fc, gain_db, width=1.0):
    """Peaking EQ: gaussian bump in log-frequency, width = FWHM in octaves."""
    lf = np.log2(np.maximum(np.asarray(f, float), 1.0) / fc)
    return 1.0 + (db2a(gain_db) - 1.0) * np.exp(-0.5 * (lf / (width / 2.355)) ** 2)


def H_shelf(f, fc, gain_db, high=True, width=2.0):
    """Smooth shelf centred on fc (width in octaves)."""
    lf = np.log2(np.maximum(np.asarray(f, float), 1.0) / fc)
    s = 1.0 / (1.0 + np.exp(-lf * 4.4 / width))
    if not high:
        s = 1.0 - s
    return db2a(gain_db * s)


def filt(x, H, circular=False, tail=0.0):
    """Zero-phase FFT filter. H is a callable f->gain (or an array for rfftfreq(nfft)).
    Non-circular signals are zero-padded; `tail` extends the output (s)."""
    x = np.asarray(x, float)
    n = x.shape[-1]
    if circular:
        nfft = n
    else:
        nfft = good_size(n + ns(tail) + min(n, ns(0.3)) + 64)
    X = np.fft.rfft(x, nfft, axis=-1)
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    G = H(f) if callable(H) else H
    y = np.fft.irfft(X * G, nfft, axis=-1)
    return y[..., :n + (0 if circular else ns(tail))]


def lp(x, fc, order=2, **kw):
    return filt(x, lambda f: H_lp(f, fc, order), **kw)


def hp(x, fc, order=2, **kw):
    return filt(x, lambda f: H_hp(f, fc, order), **kw)


def bp(x, fc, q=1.0, **kw):
    return filt(x, lambda f: H_bp(f, fc, q), **kw)


def curve_at(c, t):
    """Evaluate a control curve at times t: callable(t), per-sample array, or scalar."""
    if callable(c):
        return c(t)
    c = np.asarray(c, float)
    if c.ndim == 0:
        return np.full_like(t, float(c))
    return np.interp(t * SR, np.arange(len(c)), c)


def tvfilt(x, Hfn, frame=1024, hop=None, circular=False):
    """Time-varying zero-phase filter via STFT overlap-add.

    Hfn(t, f) -> gain, with t shaped (frames, 1) in seconds (frame centres) and
    f shaped (1, bins) in Hz. With circular=True t is wrapped into [0, n/SR).
    """
    x = np.asarray(x, float)
    n = len(x)
    hop = hop or frame // 4
    w = np.sin(np.pi * (np.arange(frame) + 0.5) / frame)
    if circular:
        nfr = int(math.ceil(n / hop))
        starts = np.arange(nfr) * hop - frame // 2
        idx = (starts[:, None] + np.arange(frame)[None, :]) % n
        frames = x[idx] * w
        tc = ((starts + frame // 2) % n) / SR
        total = n
        off = 0
    else:
        pad = frame
        nfr = int(math.ceil((n + 2 * pad - frame) / hop)) + 1
        total = (nfr - 1) * hop + frame
        xp = np.zeros(total)
        xp[pad:pad + n] = x
        starts = np.arange(nfr) * hop
        idx = starts[:, None] + np.arange(frame)[None, :]
        frames = xp[idx] * w
        tc = (starts + frame // 2 - pad) / SR
        off = pad
    S = np.fft.rfft(frames, axis=1)
    f = np.fft.rfftfreq(frame, 1.0 / SR)
    G = Hfn(tc[:, None], f[None, :])
    Y = np.fft.irfft(S * G, frame, axis=1) * w
    flat = idx.ravel()
    out = np.bincount(flat, weights=Y.ravel(), minlength=total)
    norm = np.bincount(flat, weights=np.tile(w * w, nfr), minlength=total)
    out = out / np.maximum(norm, 1e-9)
    return out[off:off + n]


def sweep(x, kind, fc, q=0.707, order=2, frame=1024, circular=False):
    """Filter sweep. fc: callable(t), per-sample array or scalar.
    kind: 'lp' | 'hp' | 'bp' | 'res' (resonant low-pass)."""
    def Hfn(t, f):
        c = np.maximum(curve_at(fc, t), 10.0)
        if kind == 'lp':
            return H_lp(f, c, order)
        if kind == 'hp':
            return H_hp(f, c, order)
        if kind == 'bp':
            return H_bp(f, c, q)
        if kind == 'res':
            return H_res(f, c, q)
        raise ValueError(kind)
    return tvfilt(x, Hfn, frame=frame, circular=circular)


def svf(x, fc, q=0.707, mode='lp'):
    """Time-varying TPT state-variable filter (sample loop; use on short sounds).
    mode: lp | bp (unity peak) | hp | notch."""
    x = np.asarray(x, float)
    n = len(x)
    fcv = np.clip(arr(fc, n), 5.0, 0.45 * SR)
    g = np.tan(np.pi * fcv / SR)
    k = 1.0 / arr(q, n)
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    xs, A1, A2, A3 = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist()
    lpo = [0.0] * n
    bpo = [0.0] * n
    ic1 = ic2 = 0.0
    for i in range(n):
        v3 = xs[i] - ic2
        v1 = A1[i] * ic1 + A2[i] * v3
        v2 = ic2 + A2[i] * ic1 + A3[i] * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        lpo[i] = v2
        bpo[i] = v1
    lpa = np.array(lpo)
    bpa = np.array(bpo)
    if mode == 'lp':
        return lpa
    if mode == 'bp':
        return k * bpa
    if mode == 'hp':
        return x - k * bpa - lpa
    if mode == 'notch':
        return x - k * bpa
    raise ValueError(mode)


# ---------------------------------------------------------------------------
# resonators
# ---------------------------------------------------------------------------

def modal(n, modes, attack=0.0005):
    """Struck resonator: sum of decaying sines. modes = [(freq, amp, t60), ...]."""
    t = times(n)
    out = np.zeros(n)
    for m in modes:
        fr, a, t60 = m[0], m[1], m[2]
        if fr >= 0.45 * SR or fr <= 0:
            continue
        out += a * np.exp(-6.9078 * t / t60) * np.sin(TAU * fr * t)
    if attack > 0:
        k = min(n, ns(attack))
        out[:k] *= np.sin(0.5 * np.pi * np.arange(k) / max(k, 1))
    return out


def ks_pluck(freq, dur, t60=1.5, stretch=0.5, bright=6000.0, pick=0.18, os=2, rng_=None):
    """Karplus-Strong plucked string, block-vectorised, tuned exactly by resampling.

    t60: decay of the fundamental; stretch in (0, 0.5]: 0.5 = darker, smaller =
    brighter; bright: low-pass on the excitation; pick: pluck position (0..0.5).
    """
    r = rng_ if rng_ is not None else _rng
    sr2 = SR * os
    S = float(np.clip(stretch, 0.05, 0.5))
    L = max(2, int(math.floor(sr2 / freq - S)))
    f_eff = sr2 / (L + S)
    n_out = ns(dur)
    need = int(math.ceil(n_out * os * freq / f_eff)) + 8
    nb = need // L + 3
    e = r.uniform(-1.0, 1.0, L)
    # low-pass the excitation (one period, circular)
    E = np.fft.rfft(e)
    fe = np.fft.rfftfreq(L, 1.0 / sr2)
    e = np.fft.irfft(E * H_lp(fe, bright, 1), L)
    p = max(1, int(round(pick * L)))
    e = e - 0.92 * np.roll(e, p)
    e -= e.mean()
    e /= np.max(np.abs(e)) + 1e-12
    y = np.zeros(nb * L)
    y[:L] = e
    rho = 10.0 ** (-3.0 / (t60 * f_eff))
    a, b = rho * (1.0 - S), rho * S
    for blk in range(1, nb):
        s0 = (blk - 1) * L
        prv = y[s0:s0 + L]
        sh = np.empty(L)
        sh[0] = y[s0 - 1] if s0 >= 1 else 0.0
        sh[1:] = prv[:-1]
        y[s0 + L:s0 + 2 * L] = a * prv + b * sh
    pos = np.arange(n_out) * (os * freq / f_eff)
    return frac_read(y, pos)


# ---------------------------------------------------------------------------
# nonlinear
# ---------------------------------------------------------------------------

def resample_fft(x, n_out):
    """Band-limited resample of a (zero-padded) signal to n_out samples."""
    x = np.asarray(x, float)
    n = len(x)
    X = np.fft.rfft(x)
    nb = n_out // 2 + 1
    Y = np.zeros(nb, complex)
    m = min(nb, len(X))
    Y[:m] = X[:m]
    if n_out < n:  # taper top 8% to avoid Gibbs ringing
        k = max(1, int(0.08 * m))
        Y[m - k:m] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, k + 1) / k)
    return np.fft.irfft(Y, n_out) * (n_out / n)


def drive(x, amount=2.0, os=4, asym=0.0):
    """Oversampled tanh saturation (asym > 0 adds even harmonics)."""
    x = np.asarray(x, float)
    n = len(x)
    pad = 512
    xp = np.concatenate([np.zeros(pad), x, np.zeros(pad)])
    up = resample_fft(xp, len(xp) * os)
    y = (np.tanh(amount * up + asym) - math.tanh(asym)) / math.tanh(amount)
    return resample_fft(y, len(xp))[pad:pad + n]


def crush(x, steps=16):
    return np.round(x * steps) / steps


# ---------------------------------------------------------------------------
# delays, modulation, space
# ---------------------------------------------------------------------------

def frac_read(x, pos, circular=False):
    """Cubic-Hermite read of x at fractional sample positions."""
    x = np.asarray(x, float)
    n = len(x)
    i = np.floor(pos).astype(np.int64)
    fr = pos - i
    if circular:
        g = lambda j: x[j % n]
    else:
        xp = np.concatenate([np.zeros(2), x, np.zeros(3)])
        g = lambda j: xp[np.clip(j + 2, 0, n + 4)]
    y0, y1, y2, y3 = g(i - 1), g(i), g(i + 1), g(i + 2)
    c1 = 0.5 * (y2 - y0)
    c2 = y0 - 2.5 * y1 + 2.0 * y2 - 0.5 * y3
    c3 = 0.5 * (y3 - y0) + 1.5 * (y1 - y2)
    return ((c3 * fr + c2) * fr + c1) * fr + y1


def chorus(x, voices=3, base_ms=14.0, depth_ms=2.5, rate=0.6, mix=0.5,
           circular=False, stereo=False, spread=0.8):
    """Multi-voice modulated-delay chorus. stereo=True returns (2, n)."""
    x = np.asarray(x, float)
    n = len(x)
    t = times(n)
    idx = np.arange(n, dtype=float)
    L = np.zeros(n)
    Rr = np.zeros(n)
    for v in range(voices):
        r = rate * (1.0 + 0.23 * v)
        if circular:
            r = loopf(r, n)
        d = (base_ms + 0.6 * v + depth_ms * np.sin(TAU * (r * t + v / voices))) * SR / 1000.0
        y = frac_read(x, idx - d, circular)
        p = spread * (-1.0 if v % 2 == 0 else 1.0) * (0.5 + 0.5 * v / max(voices - 1, 1))
        a = (p + 1.0) * np.pi / 4.0
        L += y * math.cos(a)
        Rr += y * math.sin(a)
    L *= math.sqrt(2.0) / voices
    Rr *= math.sqrt(2.0) / voices
    if stereo:
        return np.vstack([x * (1 - mix) + L * mix, x * (1 - mix) + Rr * mix])
    return x * (1 - mix) + 0.5 * (L + Rr) * mix


def echo(x, delay, fb=0.35, wet=0.35, damp=5000.0, circular=False, tail=None, dry=1.0):
    """Feedback delay computed exactly in the frequency domain (fractional delays OK)."""
    x = np.asarray(x, float)
    n = x.shape[-1]
    if circular:
        nfft, add = n, 0
    else:
        if tail is None:
            k = math.log(1e-3) / math.log(min(max(fb, 1e-3), 0.95))
            tail = delay * (k + 1)
        add = ns(tail)
        nfft = good_size(n + add)
    X = np.fft.rfft(x, nfft, axis=-1)
    f = np.fft.rfftfreq(nfft, 1.0 / SR)
    E = np.exp(-1j * TAU * f * delay)
    Lf = H_lp(f, damp, 1)
    H = dry + wet * Lf * E / (1.0 - fb * Lf * E)
    return np.fft.irfft(X * H, nfft, axis=-1)[..., :n + add]


def make_ir(t60=1.5, hf=0.45, lf=1.1, predelay=0.012, stereo=False, early=6,
            fadein=0.006, bright=10000.0, length=None, seed_=777):
    """Synthetic reverb impulse response: decaying noise with frequency-dependent
    decay (hf/lf scale T60 at 8 kHz / 150 Hz) plus a few early reflections.
    Energy-normalised so 'wet' gains mean the same for every IR."""
    r = np.random.default_rng(seed_)
    L = ns(length if length else t60 * 1.1 + predelay)
    pd = ns(predelay)
    m = L - pd
    nch = 2 if stereo else 1
    out = np.zeros((nch, L))
    t = times(m)

    def Hfn(tt, f):
        lfo = np.log2(np.maximum(f, 20.0) / 1000.0)
        T = np.where(lfo < 0,
                     t60 * (1.0 + (lf - 1.0) * np.clip(-lfo / 2.7, 0, 1)),
                     t60 * (1.0 + (hf - 1.0) * np.clip(lfo / 3.0, 0, 1)))
        return np.exp(-6.9078 * np.maximum(tt, 0.0) / T) * H_lp(f, bright, 1)

    for c in range(nch):
        nz = r.standard_normal(m)
        tail = tvfilt(nz, Hfn, frame=1024)
        tail *= 1.0 - np.exp(-t / fadein)
        rms0 = np.sqrt(np.mean(tail[:ns(0.05)] ** 2)) + 1e-9
        for _ in range(early):
            te = r.uniform(0.003, 0.05)
            k = ns(te)
            if k < m:
                tail[k] += rms0 * r.uniform(2.0, 5.0) * math.exp(-te / 0.06) * r.choice([-1.0, 1.0])
        out[c, pd:] = tail
    out /= math.sqrt(np.sum(out ** 2) / nch) + 1e-12
    return out if stereo else out[0]


def convolve(x, h, circular=False):
    """FFT convolution. x (n,) or (2,n); h (m,) or (2,m). Circular wraps the tail."""
    x = np.asarray(x, float)
    h = np.asarray(h, float)
    n = x.shape[-1]
    m = h.shape[-1]
    if circular:
        if m > n:
            k = int(math.ceil(m / n))
            hp_ = np.zeros(h.shape[:-1] + (k * n,))
            hp_[..., :m] = h
            h = hp_.reshape(h.shape[:-1] + (k, n)).sum(axis=-2)
        return np.fft.irfft(np.fft.rfft(x, n, axis=-1) * np.fft.rfft(h, n, axis=-1), n, axis=-1)
    nfft = good_size(n + m - 1)
    y = np.fft.irfft(np.fft.rfft(x, nfft, axis=-1) * np.fft.rfft(h, nfft, axis=-1), nfft, axis=-1)
    return y[..., :n + m - 1]


def reverb(x, ir, wet=0.25, dry=1.0, circular=False):
    """Convolution reverb. Mono x with stereo ir returns stereo."""
    x = np.asarray(x, float)
    y = convolve(x, ir, circular)
    out = wet * y
    if circular:
        return out + dry * x
    pad = np.zeros(out.shape[:-1] + (out.shape[-1],))
    pad[..., :x.shape[-1]] = x
    return out + dry * pad


# ---------------------------------------------------------------------------
# mixing helpers
# ---------------------------------------------------------------------------

def place(buf, x, t, gain=1.0, circular=False):
    """Add x into buf starting at time t (s) or sample index (int). Extends nothing:
    non-circular overflow is dropped; circular wraps around."""
    x = np.asarray(x, float) * gain
    N = buf.shape[-1]
    s = t if isinstance(t, (int, np.integer)) else ns(t) if t >= 0 else -ns(-t)
    m = x.shape[-1]
    if circular:
        s %= N
        off = 0
        while off < m:
            seg = min(m - off, N - s)
            buf[..., s:s + seg] += x[..., off:off + seg]
            off += seg
            s = 0
        return buf
    a = max(0, s)
    b = min(N, s + m)
    if b > a:
        buf[..., a:b] += x[..., a - s:b - s]
    return buf


def mixlen(*xs):
    """Sum signals of different lengths (all start at 0)."""
    n = max(x.shape[-1] for x in xs)
    out = np.zeros(n)
    for x in xs:
        out[:x.shape[-1]] += x
    return out


def pad_to(x, n):
    x = np.asarray(x, float)
    if x.shape[-1] >= n:
        return x[..., :n]
    out = np.zeros(x.shape[:-1] + (n,))
    out[..., :x.shape[-1]] = x
    return out


def pan(x, p=0.0):
    """Constant-power pan, p in [-1, 1] -> (2, n)."""
    a = (float(np.clip(p, -1, 1)) + 1.0) * np.pi / 4.0
    return np.vstack([x * math.cos(a), x * math.sin(a)])


def norm_peak(x, peak=1.0):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def trim_tail(x, thresh_db=-62.0, keep=0.03):
    """Drop trailing near-silence (relative to the peak), keeping a short pad."""
    a = np.abs(x)
    th = a.max() * db2a(thresh_db)
    idx = np.nonzero(a > th)[0]
    if len(idx) == 0:
        return x
    end = min(len(x), idx[-1] + ns(keep))
    return x[:end]


# ---------------------------------------------------------------------------
# loudness and limiting
# ---------------------------------------------------------------------------

_K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285],
       [1.0, -1.69065929318241, 0.73248077421585])
_K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def _bq_mag(ba, f, fs=48000.0):
    b, a = ba
    z = np.exp(-1j * TAU * np.asarray(f) / fs)
    return np.abs((b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z))


def kweight(x, circular=False):
    """ITU-R BS.1770 K-weighting (magnitude only, zero phase)."""
    return filt(x, lambda f: _bq_mag(_K1, f) * _bq_mag(_K2, f), circular=circular)


def _ms_windows(y, win, hop):
    """Mean square (summed over channels) over sliding windows."""
    y2 = y * y
    if y2.ndim == 2:
        y2 = y2.sum(axis=0)
    n = len(y2)
    if n < win:
        y2 = np.concatenate([y2, np.zeros(win - n)])
        n = win
    c = np.concatenate([[0.0], np.cumsum(y2)])
    starts = np.arange(0, n - win + 1, hop)
    return (c[starts + win] - c[starts]) / win


def loudness_max(x, win=0.4):
    """Max momentary loudness (default 400 ms windows, LUFS-like)."""
    y = kweight(x)
    ms = _ms_windows(y, ns(win), ns(0.02))
    return -0.691 + 10.0 * math.log10(max(ms.max(), 1e-20))


def loudness_int(x, circular=True):
    """Gated integrated loudness (BS.1770-style)."""
    y = kweight(x, circular=circular)
    ms = _ms_windows(y, ns(0.4), ns(0.1))
    lk = -0.691 + 10.0 * np.log10(np.maximum(ms, 1e-20))
    g = ms[lk > -70.0]
    if len(g) == 0:
        return -70.0
    rel = -0.691 + 10.0 * math.log10(g.mean()) - 10.0
    g2 = ms[lk > rel]
    return -0.691 + 10.0 * math.log10(max(g2.mean(), 1e-20))


def true_peak(x, os=4):
    x = np.asarray(x, float)
    if x.ndim == 2:
        return max(true_peak(c, os) for c in x)
    n = len(x)
    up = resample_fft(np.concatenate([x, np.zeros(64)]), (n + 64) * os)
    return float(np.max(np.abs(up)))


def _sliding_min(v, w, circular):
    """min over the forward window v[i : i+w]."""
    if w <= 1:
        return v.copy()
    if circular:
        vp = np.concatenate([v, v[:w - 1]])
    else:
        vp = np.concatenate([v, np.ones(w - 1)])
    from numpy.lib.stride_tricks import sliding_window_view
    out = np.empty(len(v))
    step = 1 << 18
    for a in range(0, len(v), step):
        b = min(len(v), a + step)
        out[a:b] = sliding_window_view(vp[a:b + w - 1], w).min(axis=1)
    return out


def _tp_env(x, circular, os=4):
    """Per-sample true-peak envelope: |x| including the 4x-oversampled points
    that follow each sample (catches inter-sample overs)."""
    xs = x if x.ndim == 2 else x[None, :]
    n = xs.shape[1]
    env = np.zeros(n)
    for ch in xs:
        if circular:
            up = resample_fft(ch, n * os)
        else:
            up = resample_fft(np.concatenate([ch, np.zeros(64)]), (n + 64) * os)[:n * os]
        env = np.maximum(env, np.abs(up).reshape(n, os).max(axis=1))
        env = np.maximum(env, np.abs(ch))
    return env


def limit(x, ceiling_db=-1.0, attack=0.0015, release=0.08, circular=False):
    """Look-ahead brick-wall limiter (mono or stereo, linked)."""
    x = np.asarray(x, float)
    c = float(db2a(ceiling_db))
    a = _tp_env(x, circular)
    req = np.minimum(1.0, c / np.maximum(a, 1e-12))
    if req.min() >= 1.0:
        return x.copy()
    la = max(2, ns(attack))
    g = _sliding_min(req, la, circular)
    # release (control rate, sample loop over blocks)
    blk = 16
    nb = int(math.ceil(len(g) / blk))
    gp = np.concatenate([g, np.ones(nb * blk - len(g))]).reshape(nb, blk).min(axis=1)
    coef = math.exp(-blk / (release * SR))
    gl = gp.tolist()
    passes = 2 if circular else 1
    state = 1.0
    if circular:
        state = min(gl)
    res = [0.0] * nb
    for _ in range(passes):
        for i in range(nb):
            v = gl[i]
            rec = 1.0 - (1.0 - state) * coef   # recover towards unity gain
            state = v if v < rec else rec       # but never above what this block needs
            res[i] = state
    gr = np.repeat(np.array(res), blk)[:len(g)]
    g = np.minimum(g, gr)
    # attack smoothing: moving average over la samples, aligned with the look-ahead
    if circular:
        gpad = np.concatenate([g[-(la - 1):], g])
    else:
        gpad = np.concatenate([np.ones(la - 1), g])
    cs = np.concatenate([[0.0], np.cumsum(gpad)])
    gs = (cs[la:] - cs[:-la]) / la
    gs = np.minimum(gs[:len(g)], 1.0)
    y = x * gs
    return np.clip(y, -c, c)


# ---------------------------------------------------------------------------
# WAV I/O (with 'smpl' loop chunk understood by Godot's importer)
# ---------------------------------------------------------------------------

def to_int16(x, dither=True, rng_seed=12345):
    x = np.asarray(x, float)
    r = np.random.default_rng(rng_seed)
    y = x * 32767.0
    if dither:
        y = y + (r.uniform(-0.5, 0.5, y.shape) + r.uniform(-0.5, 0.5, y.shape))
    return np.clip(np.round(y), -32768, 32767).astype('<i2')


def write_wav(path, x, loop=False, sr=SR):
    """16-bit PCM WAV. x: (n,) mono or (2, n) stereo. loop=True adds a 'smpl'
    chunk with one forward loop over the whole file (start 0, end = frame count,
    Godot's exclusive-end convention), so Godot's default 'Detect From WAV' loop
    mode imports it as a looping stream."""
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = x[None, :]
    ch, n = x.shape
    pcm = to_int16(x).T.reshape(-1).tobytes()
    fmt = struct.pack('<HHIIHH', 1, ch, sr, sr * ch * 2, ch * 2, 16)
    chunks = [b'fmt ' + struct.pack('<I', len(fmt)) + fmt,
              b'data' + struct.pack('<I', len(pcm)) + pcm + (b'\x00' if len(pcm) % 2 else b'')]
    if loop:
        smpl = struct.pack('<9I', 0, 0, int(round(1e9 / sr)), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack('<6I', 0, 0, 0, n, 0, 0)
        chunks.append(b'smpl' + struct.pack('<I', len(smpl)) + smpl)
    body = b'WAVE' + b''.join(chunks)
    with open(path, 'wb') as fh:
        fh.write(b'RIFF' + struct.pack('<I', len(body)) + body)


def read_wav(path):
    """Returns (float array (ch, n), sr, loop) where loop is (start, end) or None."""
    with open(path, 'rb') as fh:
        data = fh.read()
    assert data[:4] == b'RIFF' and data[8:12] == b'WAVE', path
    pos = 12
    fmt = None
    pcm = None
    loop = None
    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        size = struct.unpack('<I', data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + size]
        if cid == b'fmt ':
            fmt = struct.unpack('<HHIIHH', body[:16])
        elif cid == b'data':
            pcm = body
        elif cid == b'smpl':
            vals = struct.unpack('<%dI' % (len(body) // 4), body)
            if vals[7] > 0:
                loop = (vals[11], vals[12])
        pos += 8 + size + (size & 1)
    ch, sr = fmt[1], fmt[2]
    a = np.frombuffer(pcm, '<i2').astype(float) / 32768.0
    return a.reshape(-1, ch).T, sr, loop
