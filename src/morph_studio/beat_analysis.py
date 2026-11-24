"""One beat/tempo/section analyzer for any kind of music (F15).

There is no style switch: the same pipeline must handle click tracks and electronic
music (sharp, regular onsets) as well as classical recordings (soft string onsets,
pp-to-ff dynamics, rubato, little or no percussion). It follows Frédéric Patin's
statistical sub-band energy method (independent implementation):

1. **Sub-band onset strength** — the spectrum is split into log-spaced sub-bands of
   increasing width; each band's energy is compared with its own ~1.3 s running
   history and log-compressed, so quiet passages count as much as loud ones and a
   single loud band cannot dominate.
2. **Local tempo curve** — autocorrelation in sliding windows, weighted by a
   log-Gaussian perceptual prior around 110 BPM to settle half/double-tempo choices.
3. **Dynamic-programming beat tracking** (after Ellis 2007) — each beat picks the
   predecessor that best balances onset strength against deviation from the *local*
   beat period, so the grid follows accelerando/ritardando and is exact for steady
   tempos. The reported BPM is refined from the median inter-beat interval.
4. **Sections** — novelty of short-term loudness and brightness between adjacent
   windows marks phrase/section changes (natural sync points when beats are weak).

Results are heuristics with confidence values; storyboard BPM/offset overrides win.
"""
from __future__ import annotations

import math

SR = 11025
FFT_N = 512
HOP = 256
FPS = SR / HOP  # ~43.07 analysis frames per second
N_BANDS = 16
HISTORY_S = 1.3


def band_edges(n_bands: int = N_BANDS, fmin: float = 60.0, fmax: float = SR / 2) -> list[tuple[int, int]]:
    """Log-spaced sub-band bin ranges of increasing width (16 bands)."""
    bin_hz = SR / FFT_N
    edges = [fmin * (fmax / fmin) ** (k / n_bands) for k in range(n_bands + 1)]
    out, prev = [], 1
    for k in range(n_bands):
        hi = max(prev + 1, int(edges[k + 1] / bin_hz))
        out.append((prev, min(hi, FFT_N // 2)))
        prev = hi
    return out


def subband_frames(samples: list[float]) -> tuple[list[list[float]], list[float], list[float]]:
    """Per-frame sub-band energies, loudness (dB) and spectral brightness (Hz).

    Frame f covers samples starting at ``f * HOP``; its time is ``f / FPS``.
    """
    from .audio_bands import fft_magnitudes
    window = [0.5 - 0.5 * math.cos(2 * math.pi * i / (FFT_N - 1)) for i in range(FFT_N)]
    bands = band_edges()
    bin_hz = SR / FFT_N
    energies, loudness, brightness = [], [], []
    padded = samples + [0.0] * FFT_N
    for start in range(0, len(samples), HOP):
        mags = fft_magnitudes([padded[start + i] * window[i] for i in range(FFT_N)])
        power = [m * m for m in mags]
        energies.append([sum(power[lo:hi]) for lo, hi in bands])
        total = sum(power) + 1e-12
        loudness.append(10 * math.log10(total))
        brightness.append(sum(i * bin_hz * p for i, p in enumerate(power)) / total)
    return energies, loudness, brightness


def onset_strength(energies: list[list[float]], prime_from: int = 0) -> list[float]:
    """Sum over sub-bands of the positive log-ratio of instant energy to its history.

    Each band's history is primed with its mean level over the first ~1.3 s of real
    audio (from ``prime_from``), so the warm-up does not inflate every frame.
    """
    if not energies:
        return []
    hist_n = max(4, int(HISTORY_S * FPS))
    n_bands = len(energies[0])
    sample = energies[prime_from:prime_from + hist_n] or energies[:hist_n]
    prime = [sum(f[b] for f in sample) / len(sample) for b in range(n_bands)]
    running = [p * hist_n for p in prime]
    buffers = [[prime[b]] * hist_n for b in range(n_bands)]
    floor = max(1e-10, max(max(f) for f in energies) * 1e-6)  # ignore near-silence
    pos, raw = 0, []
    for f, frame in enumerate(energies):
        value = 0.0
        for b, e in enumerate(frame):
            history = running[b] / hist_n
            value += max(0.0, math.log((e + floor) / (history + floor)))
            running[b] += e - buffers[b][pos]
            buffers[b][pos] = e
        pos = (pos + 1) % hist_n
        raw.append(value)
    peak = max(raw)
    return [r / peak for r in raw] if peak > 0 else raw


def _smooth(env: list[float]) -> list[float]:
    k = (0.25, 0.5, 1.0, 0.5, 0.25)
    return [sum(k[j + 2] * env[i + j] for j in range(-2, 3) if 0 <= i + j < len(env)) for i in range(len(env))]


def _tempo_prior(bpm: float, centre: float = 110.0, octave_sigma: float = 1.0) -> float:
    return math.exp(-0.5 * (math.log2(bpm / centre) / octave_sigma) ** 2)


def tempo_curve(env: list[float], window_s: float = 8.0, hop_s: float = 2.0,
                min_bpm: float = 50.0, max_bpm: float = 220.0, rubato: float = 1.25) -> list[dict]:
    """Local tempo over time with one consistent tempo octave.

    The octave is chosen once for the whole piece (autocorrelation summed over all
    windows × perceptual prior); each window's tempo may then vary only within a factor
    ``rubato`` of it, so half/double-tempo flips cannot break beat tracking.
    """
    env = _smooth(env)
    win = min(len(env), int(window_s * FPS))
    hop = max(1, int(hop_s * FPS))
    lo_lag, hi_lag = int(FPS * 60 / max_bpm), int(math.ceil(FPS * 60 / min_bpm))
    windows: list[tuple[int, dict]] = []
    starts = range(0, max(1, len(env) - win + 1), hop) if win else []
    for start in starts:
        seg = env[start:start + win]
        mean = sum(seg) / len(seg)
        c = [x - mean for x in seg]
        energy = sum(x * x for x in c)
        if energy <= 1e-9:
            continue
        acs = {lag: sum(c[i] * c[i + lag] for i in range(len(c) - lag)) / energy
               for lag in range(max(1, lo_lag - 1), min(hi_lag + 1, len(c) - 1) + 1)}
        windows.append((start, acs))
    if not windows:
        return []
    total: dict[int, float] = {}
    for _, acs in windows:
        for lag, ac in acs.items():
            total[lag] = total.get(lag, 0.0) + ac
    global_lag = max((l for l in total if lo_lag <= l <= hi_lag),
                     key=lambda l: total[l] * _tempo_prior(60 * FPS / l))
    # Periodic material scores (almost) as high at 2x / 3x the beat period, and accented
    # bars push those multiples above the beat. Prefer a sub-multiple that is nearly as strong.
    for div in (2, 3):
        near = [l for l in range(round(global_lag / div) - 1, round(global_lag / div) + 2)
                if l in total and l >= lo_lag]
        if near:
            sub = max(near, key=lambda l: total[l])
            if total[sub] >= 0.75 * total[global_lag]:
                global_lag = sub
                break
    lo_l, hi_l = global_lag / rubato, global_lag * rubato

    def closeness(lag: int) -> float:  # prefer local tempi near the global one
        return math.exp(-0.5 * (math.log2(lag / global_lag) / 0.12) ** 2)

    curve = []
    for start, acs in windows:
        peaks = [l for l in acs if lo_l <= l <= hi_l and l - 1 in acs and l + 1 in acs
                 and acs[l] >= acs[l - 1] and acs[l] >= acs[l + 1]]
        if not peaks:
            continue
        lag = max(peaks, key=lambda l: acs[l] * closeness(l))
        ac = acs[lag]
        refined = float(lag)
        if lag - 1 in acs and lag + 1 in acs:
            a, b, d = acs[lag - 1], acs[lag], acs[lag + 1]
            denom = a - 2 * b + d
            if denom:
                refined += max(-0.5, min(0.5, 0.5 * (a - d) / denom))
        curve.append({"t": round((start + win / 2) / FPS, 2), "bpm": round(60 * FPS / refined, 2),
                      "confidence": round(max(0.0, min(1.0, ac)), 3)})
    bpms = [p["bpm"] for p in curve]
    for i, p in enumerate(curve):  # light 3-point median filter
        window = sorted(bpms[max(0, i - 1):i + 2])
        p["bpm"] = window[len(window) // 2]
    return curve


def track_beats_dp(env: list[float], curve: list[dict], tightness: float = 100.0) -> list[float]:
    """Dynamic-programming beat tracking following the local tempo curve (seconds)."""
    if not env or not curve:
        return []
    times = [p["t"] for p in curve]

    def period_at(frame: int) -> float:
        t = frame / FPS
        k = min(range(len(times)), key=lambda i: abs(times[i] - t))
        return 60 * FPS / curve[k]["bpm"]

    score = list(env)
    back = [-1] * len(env)
    for t in range(len(env)):
        period = period_at(t)
        lo, hi = int(round(t - 2 * period)), int(round(t - period / 2))
        best, arg = -1e18, -1
        for tau in range(max(0, lo), hi + 1):
            dev = math.log((t - tau) / period)
            cand = score[tau] - tightness * dev * dev
            if cand > best:
                best, arg = cand, tau
        if arg >= 0:  # always link (Ellis 2007): a weak stretch must not break the chain
            score[t] = env[t] + max(best, 0.0) if best > 0 else env[t] + best
            back[t] = arg
    last_period = int(period_at(len(env) - 1))
    tail = range(max(0, len(env) - last_period), len(env))
    end = max(tail, key=lambda i: score[i])
    frames = []
    while end >= 0:
        frames.append(end)
        end = back[end]
    frames.reverse()
    return [round(_refine_peak(env, f) / FPS, 4) for f in frames]


def _refine_peak(env: list[float], f: int) -> float:
    """Sub-frame onset position by parabolic interpolation around a local maximum."""
    if 0 < f < len(env) - 1:
        a, b, c = env[f - 1], env[f], env[f + 1]
        denom = a - 2 * b + c
        if denom < 0:
            return f + max(-0.5, min(0.5, 0.5 * (a - c) / denom))
    return float(f)


def sections(loudness: list[float], brightness: list[float], window_s: float = 6.0,
             min_gap_s: float = 10.0, threshold: float = 1.6) -> list[dict]:
    """Boundaries where loudness (dB) and brightness change most between adjacent windows."""
    step = max(1, int(FPS / 4))
    w = int(window_s * FPS)
    if len(loudness) < 2 * w + step:
        return []
    bmean = (sum(brightness) / len(brightness)) or 1.0
    novelty = []
    for i in range(w, len(loudness) - w, step):
        dl = abs(sum(loudness[i:i + w]) - sum(loudness[i - w:i])) / w / 6.0
        db = abs(sum(brightness[i:i + w]) - sum(brightness[i - w:i])) / w / (0.25 * bmean)
        novelty.append((i, dl + db))
    values = [v for _, v in novelty]
    mean = sum(values) / len(values)
    sd = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5 or 1.0
    picks: list[dict] = []
    for k, (i, v) in enumerate(novelty):
        neighbourhood = novelty[max(0, k - 8):k + 9]
        if (v - mean) / sd > threshold and v >= max(n[1] for n in neighbourhood):
            t = round(i / FPS, 2)
            if not picks or t - picks[-1]["t"] >= min_gap_s:
                picks.append({"t": t, "strength": round((v - mean) / sd, 2)})
    return picks


def downbeat_index(env: list[float], beats: list[float], beats_per_bar: int = 4) -> int | None:
    if len(beats) < beats_per_bar:
        return None
    sums = [0.0] * beats_per_bar
    for i, b in enumerate(beats):
        f = int(round(b * FPS))
        if f < len(env):
            sums[i % beats_per_bar] += max(env[max(0, f - 1):f + 2])
    return max(range(beats_per_bar), key=lambda k: sums[k])


def percussiveness(env: list[float]) -> float:
    """Peak-to-mean ratio of the onset envelope (high for drums/clicks, low for strings)."""
    if not env:
        return 0.0
    mean = sum(env) / len(env)
    top = sorted(env)[-max(1, len(env) // 50):]
    return round((sum(top) / len(top)) / mean, 2) if mean > 0 else 0.0


LEAD_S = 0.25  # leading silence so a note at t=0 has history to stand out against
# Frames are indexed by window start; energy is reported where the event sits in the
# window, measured as -22 ms on click tracks. Time-stamp frames at the window centre.
CENTRE_S = (FFT_N / 2) / SR


def analyze_samples(samples: list[float]) -> dict:
    lead_frames = int(round(LEAD_S * FPS))
    pad = [0.0] * (lead_frames * HOP)
    lead = len(pad) / SR - CENTRE_S
    energies, loudness, brightness = subband_frames(pad + samples)
    env = onset_strength(energies, prime_from=lead_frames)
    curve = tempo_curve(env)
    beats = [round(b - lead, 4) for b in track_beats_dp(env, curve) if b - lead > -0.06]
    beats = [max(0.0, b) for b in beats]
    for p in curve:
        p["t"] = round(p["t"] - lead, 2)
    env, loudness, brightness = env[lead_frames:], loudness[lead_frames:], brightness[lead_frames:]
    if len(beats) >= 3:
        ibis = sorted(b - a for a, b in zip(beats, beats[1:]))
        bpm = round(60.0 / ibis[len(ibis) // 2], 2)
    else:
        bpm = None
    confidence = round(sum(p["confidence"] for p in curve) / len(curve), 3) if curve else 0.0
    bpms = sorted(p["bpm"] for p in curve)
    spread = round(bpms[int(0.9 * (len(bpms) - 1))] - bpms[int(0.1 * (len(bpms) - 1))], 2) if bpms else None
    onsets = [round(_refine_peak(env, i) / FPS + CENTRE_S, 3) for i in range(1, len(env) - 1)
              if env[i] > 0.3 and env[i] >= env[i - 1] and env[i] > env[i + 1]]
    return {
        "bpm": bpm, "confidence": confidence if bpm else 0.0,
        "status": "ok" if bpm else "no_beat_detected",
        "alternatives": [round(bpm / 2, 2), round(bpm * 2, 2)] if bpm else [],
        "beats": beats if bpm else [], "offset_s": beats[0] if bpm and beats else None,
        "downbeat_index": downbeat_index(env, beats) if bpm else None,
        "tempo_curve": curve, "tempo_spread_bpm": spread,
        "sections": sections(loudness, brightness),
        "onsets": onsets[:2000], "percussiveness": percussiveness(env),
        "method": "Patin-style sub-band energy onsets, prior-weighted local tempo, DP beat tracking (heuristic)",
    }
