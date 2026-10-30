"""Synthesized, royalty-free music beds shared by build.py and carousel.py.
Several styles rotate by date so the account doesn't play the same loop every day:
bed(seconds, path, style=None) writes a stereo 44.1kHz wav; style None picks STYLES[today's KST date % len],
MUSIC=<name> (env) or a json "music" field forces one. The AI account (topic "ai") rotates its three
electronic styles (AI_STYLES) mixed with the original five (AI_ROTATION). Everything is generated from numpy, nothing is downloaded.
"""
import datetime, os, wave
import numpy as np

SR = 44100
midi = lambda m: 440 * 2 ** ((m - 69) / 12)

def env(n, a, d, s, r, hold):
    A = int(a * SR); Dd = int(d * SR); R = int(r * SR); H = max(int(hold * SR) - A - Dd, 0)
    e = np.concatenate([np.linspace(0, 1, A), np.linspace(1, s, Dd), np.full(H, s), np.linspace(s, 0, R)])
    return np.concatenate([e, np.zeros(max(n - len(e), 0))])[:n]

# ---------- instruments: each returns a mono signal for one note ----------
def pluck(f, dur, bright=.8):  # the original bright arpeggio voice
    n = int(SR * (dur + .2)); tt = np.arange(n) / SR
    sig = np.sin(2*np.pi*f*tt) + bright*0.35*np.sin(2*np.pi*2*f*tt) + bright*0.12*np.sin(2*np.pi*3*f*tt)
    return sig * env(n, .003, .12, .3, .2, dur)

def pad(f, dur, bright=.25):
    n = int(SR * (dur + .6)); tt = np.arange(n) / SR
    sig = sum(np.sin(2*np.pi*f*(1 + dt)*tt) for dt in (-.003, 0, .003)) / 3
    sig += bright*0.35*np.sin(2*np.pi*2*f*tt)
    return sig * (1 + 0.004*np.sin(2*np.pi*5.5*tt)) * env(n, .25, .4, .6, .6, dur)

def piano(f, dur):
    n = int(SR * (dur + .5)); tt = np.arange(n) / SR
    sig = sum(np.sin(2*np.pi*f*k*tt) * np.exp(-tt*(1.5 + k*1.2)) / k**1.3 for k in range(1, 7))
    return sig * env(n, .002, .05, 1, .4, dur)

def keys(f, dur):  # electric-piano: sine with a bell partial and slow tremolo
    n = int(SR * (dur + .4)); tt = np.arange(n) / SR
    sig = np.sin(2*np.pi*f*tt) + 0.25*np.sin(2*np.pi*f*7*tt)*np.exp(-tt*9) + 0.15*np.sin(2*np.pi*2*f*tt)
    return sig * (1 + 0.15*np.sin(2*np.pi*4.5*tt)) * env(n, .005, .6, .35, .35, dur)

def sub(f, dur, a=.005):
    n = int(SR * (dur + .15)); tt = np.arange(n) / SR
    sig = np.sin(2*np.pi*f*tt) + 0.2*np.sin(2*np.pi*2*f*tt)
    return sig * env(n, a, .2, .6, .15, dur)

def synth_bass(f, dur):  # soft square, a little brighter than sub
    n = int(SR * (dur + .08)); tt = np.arange(n) / SR
    sig = sum(np.sin(2*np.pi*f*k*tt) / k for k in (1, 3, 5)) * 0.8
    return sig * env(n, .004, .1, .5, .08, dur)

def bell(f, dur):
    n = int(SR * (dur + .8)); tt = np.arange(n) / SR
    sig = np.sin(2*np.pi*f*tt) + 0.4*np.sin(2*np.pi*f*2.76*tt)*np.exp(-tt*4) + 0.2*np.sin(2*np.pi*f*5.4*tt)*np.exp(-tt*8)
    return sig * np.exp(-tt*2.2) * env(n, .002, .05, 1, .3, dur + .5)

def saw(f, dur, cutoff=8):  # band-limited saw, a few partials: the synthwave lead/arp
    n = int(SR * (dur + .1)); tt = np.arange(n) / SR
    sig = sum(np.sin(2*np.pi*f*k*tt) / k * np.exp(-tt*k*cutoff*.15) for k in range(1, 9))
    return sig * env(n, .004, .15, .45, .1, dur)

def fm(f, dur, idx=2.5, ratio=3.5):  # glassy FM blip/bell, the "digital" voice of the AI styles
    n = int(SR * (dur + .5)); tt = np.arange(n) / SR
    sig = np.sin(2*np.pi*f*tt + idx*np.exp(-tt*6)*np.sin(2*np.pi*f*ratio*tt))
    return sig * np.exp(-tt*3) * env(n, .002, .05, 1, .3, dur + .3)

def riser(LEN_s, rng):  # filtered-noise sweep up, for the last beat before a section
    n = int(SR * LEN_s); x = rng.standard_normal(n); out = np.zeros(n); k = 0
    for i, w in enumerate(np.linspace(12, 2, 8).astype(int)):
        a, b = i*n//8, (i+1)*n//8; out[a:b] = np.convolve(x[a:b], np.ones(w)/w, "same")
    return out * np.linspace(0, 1, n) ** 2

# ---------- drums ----------
def kick(rng):
    n = int(SR * .18); tt = np.arange(n) / SR
    return np.sin(2*np.pi*(55 + 90*np.exp(-tt*40))*tt) * np.exp(-tt*22)

def hat(rng, length=.05):
    n = int(SR * length)
    x = rng.standard_normal(n); x = x - np.convolve(x, np.ones(4) / 4, "same")  # crude high-pass
    return x * np.exp(-np.arange(n) / SR * (120 if length < .1 else 30))

def snare(rng):
    n = int(SR * .2); tt = np.arange(n) / SR
    return (rng.standard_normal(n) * 0.6 * np.exp(-tt*25) + np.sin(2*np.pi*190*tt) * np.exp(-tt*35)) * 0.8

def clap(rng):
    n = int(SR * .15); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    e = sum(np.exp(-np.clip(tt - o, 0, None)*60) * (tt >= o) for o in (0, .01, .02)) / 3
    return x * e

def shaker(rng):
    n = int(SR * .08); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    x = x - np.convolve(x, np.ones(3) / 3, "same")
    return x * np.sin(np.pi * tt / tt[-1]) ** 2

def lowpass(x, hz):
    X = np.fft.rfft(x, axis=-1); f = np.fft.rfftfreq(x.shape[-1], 1 / SR)
    X *= 1 / (1 + (f / hz) ** 4)
    return np.fft.irfft(X, n=x.shape[-1], axis=-1)

# ---------- styles ----------
# chords as midi notes, one per bar; bass as midi roots
STYLES = {
    # 108 BPM bright D-major plucks over a pad, four-on-the-floor-light (the original briefing bed)
    "bright": dict(bpm=108, chords=[[62, 66, 69, 74], [57, 61, 64, 69], [59, 62, 66, 71], [55, 59, 62, 67]], bass=[38, 33, 35, 31]),
    # 84 BPM lo-fi: minor-7 electric piano, swung hats, dusty and warm
    "lofi": dict(bpm=84, chords=[[57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65], [52, 55, 59, 62]], bass=[33, 29, 31, 28]),
    # 120 BPM news pulse: eighth-note synth bass, minor, steady kick + clap
    "pulse": dict(bpm=120, chords=[[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]], bass=[33, 29, 36, 31]),
    # 92 BPM calm piano: broken chords, soft shaker, no kick
    "piano": dict(bpm=92, chords=[[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]], bass=[36, 31, 33, 29]),
    # 116 BPM upbeat: offbeat stabs, claps on 2 and 4, bell hook
    "upbeat": dict(bpm=116, chords=[[65, 69, 72], [67, 71, 74], [64, 67, 71], [69, 72, 76]], bass=[41, 43, 40, 45]),
    # AI 테크 account (topic "ai"): electronic, forward-moving, a little futuristic, never dark or scary
    # 100 BPM synthwave: 16th-note saw arpeggio, gated pad, punchy kick + snare
    "synthwave": dict(bpm=100, chords=[[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 66]], bass=[33, 29, 36, 31]),
    # 122 BPM tech pulse: FM blips in a 3-against-4 pattern, pumping pad, four-on-the-floor
    "techpulse": dict(bpm=122, chords=[[62, 65, 69, 72], [58, 62, 65, 69], [60, 64, 67, 71], [57, 60, 64, 67]], bass=[38, 34, 36, 33]),
    # 90 BPM future ambient: glassy FM bells over a wide evolving pad, soft kick, shaker
    "futureglass": dict(bpm=90, chords=[[64, 67, 71, 74], [60, 64, 67, 71], [62, 65, 69, 72], [59, 62, 66, 69]], bass=[40, 36, 38, 35]),
}
AI_STYLES = ["synthwave", "techpulse", "futureglass"]
# the AI account mixes its electronic beds with the original five so no two days in a row sound alike
AI_ROTATION = ["synthwave", "pulse", "techpulse", "lofi", "futureglass", "upbeat", "synthwave", "bright", "techpulse", "piano", "futureglass"]

def pick(style=None, when=None, offset=0, topic=None):
    """Explicit style (or MUSIC env) wins; otherwise rotate by KST date: the AI account (topic "ai") rotates
    AI_ROTATION (its three electronic beds mixed with the original five), everything else the original five."""
    style = style or os.environ.get("MUSIC") or None
    if style:
        assert style in STYLES, f"music must be one of {', '.join(STYLES)}"
        return style
    when = when or (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()  # KST
    names = AI_ROTATION if topic == "ai" else [n for n in STYLES if n not in AI_STYLES]
    return names[(when.toordinal() + offset) % len(names)]

def bed(LEN, path, style=None, fade_in=0.1, fade_out=3.0, cuts=(), topic=None):
    """Write a LEN-second music bed to path. cuts: seconds where a soft page-turn swish should land."""
    name = pick(style, topic=topic); S = STYLES[name]
    beat = 60 / S["bpm"]; bar = beat * 4; N = int(SR * LEN); rng = np.random.default_rng(7)
    mix = np.zeros((2, N))
    def add(sig, at, gain=1.0, pan=0.0):
        i = int(at * SR); j = min(i + len(sig), N)
        if i >= N or j <= i: return
        s = sig[:j-i] * gain; mix[0, i:j] += s * (1 - max(pan, 0)); mix[1, i:j] += s * (1 + min(pan, 0))
    for b_ in range(int(LEN / bar) + 1):
        ch = S["chords"][b_ % 4]; bs = S["bass"][b_ % 4]; t0 = b_ * bar
        if name == "bright":
            for m in ch: add(pad(midi(m), bar*.95), t0, .07, (m % 3 - 1) * .3)
            for k in range(8):
                m = ch[(k*2) % 4] + (12 if k % 3 == 2 else 0)
                add(pluck(midi(m), beat*.35), t0 + k*beat/2, .09, .25*np.sin(k))
            for st in (0, beat*2): add(sub(midi(bs), beat*1.2), t0 + st, .16)
            for k in range(4):
                if k % 2 == 0: add(kick(rng), t0 + k*beat, .35)
                for h in range(2): add(hat(rng), t0 + k*beat + h*beat/2, .035 if h else .02, .4)
        elif name == "lofi":
            for m in ch: add(keys(midi(m), beat*1.8), t0, .08, (m % 3 - 1) * .25)
            for m in ch[1:]: add(keys(midi(m), beat*.9), t0 + beat*2.5, .05, (m % 3 - 1) * .25)
            add(sub(midi(bs), beat*1.5), t0, .2); add(sub(midi(bs + 7), beat*.8), t0 + beat*2.66, .14)
            swing = beat * 0.16
            for k in range(4):
                if k in (0, 2): add(kick(rng), t0 + k*beat, .3)
                if k in (1, 3): add(snare(rng), t0 + k*beat, .12, -.1)
                add(hat(rng), t0 + k*beat, .03, .35); add(hat(rng), t0 + k*beat + beat/2 + swing, .02, .35)
        elif name == "pulse":
            for m in ch: add(pad(midi(m), bar*.95, .4), t0, .06, (m % 3 - 1) * .35)
            for k in range(8): add(synth_bass(midi(bs + (12 if k in (3, 7) else 0)), beat*.4), t0 + k*beat/2, .14)
            for k in range(4):
                add(kick(rng), t0 + k*beat, .33)
                if k in (1, 3): add(clap(rng), t0 + k*beat, .11, .05)
                add(hat(rng), t0 + k*beat + beat/2, .03, .4)
            if b_ % 2 == 1: add(bell(midi(ch[-1] + 12), beat), t0 + beat*3, .05, -.3)
        elif name == "piano":
            order = [0, 1, 2, 3, 2, 1, 2, 3]
            for k, o in enumerate(order): add(piano(midi(ch[o]), beat*.6), t0 + k*beat/2, .12, (o - 1.5) * .15)
            add(piano(midi(bs + 12), bar*.9), t0, .1, -.1); add(sub(midi(bs), bar*.9, a=.05), t0, .1)
            for m in ch[:3]: add(pad(midi(m), bar*.95, .1), t0, .035, (m % 3 - 1) * .3)
            for k in range(8): add(shaker(rng), t0 + k*beat/2, .025 if k % 2 else .04, .3)
        elif name == "upbeat":
            for k in range(4):
                for m in ch: add(keys(midi(m), beat*.25), t0 + k*beat + beat/2, .06, (m % 3 - 1) * .3)
                add(kick(rng), t0 + k*beat, .33)
                if k in (1, 3): add(clap(rng), t0 + k*beat, .12, -.05)
                add(hat(rng), t0 + k*beat + beat/2, .03, .4)
            for k, st in enumerate((0, beat*1.5, beat*2, beat*3)): add(synth_bass(midi(bs), beat*.4), t0 + st, .15)
            hook = [ch[-1] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12]
            if b_ % 2 == 0:
                for k, m in enumerate(hook): add(bell(midi(m), beat*.4), t0 + k*beat*.75, .05, .25)
        elif name == "synthwave":
            for m in ch: add(pad(midi(m), bar*.95, .45), t0, .055, (m % 3 - 1) * .35)
            arp = [ch[0], ch[1], ch[2], ch[3], ch[2] + 12, ch[3], ch[2], ch[1]]
            for k in range(16): add(saw(midi(arp[k % 8] + 12), beat*.2), t0 + k*beat/4, .045, .3*np.sin(k*.8))
            for k in range(8): add(synth_bass(midi(bs), beat*.42), t0 + k*beat/2, .13)
            for k in range(4):
                add(kick(rng), t0 + k*beat, .34)
                if k in (1, 3): add(snare(rng), t0 + k*beat, .16, .05)
                add(hat(rng), t0 + k*beat + beat/2, .028, .4)
        elif name == "techpulse":
            for m in ch:  # pad pumps against the kick (sidechain feel)
                for k in range(4): add(pad(midi(m), beat*.7, .3), t0 + k*beat + beat*.18, .04, (m % 3 - 1) * .35)
            for k in range(16):
                if k % 3 == 0: add(fm(midi(ch[(k // 3) % 4] + 12), beat*.18, 3, 2.0), t0 + k*beat/4, .07, .4*np.sin(k))
            for k in range(4):
                add(kick(rng), t0 + k*beat, .36); add(synth_bass(midi(bs), beat*.3), t0 + k*beat + beat/2, .14)
                add(hat(rng), t0 + k*beat + beat/2, .035, .4); add(hat(rng, .02), t0 + k*beat + beat*.75, .015, -.4)
                if k == 3 and b_ % 4 == 3: add(riser(beat, rng), t0 + k*beat, .05)
        elif name == "futureglass":
            for m in ch: add(pad(midi(m), bar*.98, .2), t0, .07, (m % 3 - 1) * .45)
            for k, o in enumerate([0, 2, 3, 1, 3, 2]): add(fm(midi(ch[o] + 12), beat*.8, 1.8, 3.5), t0 + k*beat*2/3, .06, (o - 1.5) * .25)
            add(sub(midi(bs), bar*.9, a=.05), t0, .14)
            for k in range(4):
                if k in (0, 2): add(kick(rng), t0 + k*beat, .22)
            for k in range(8): add(shaker(rng), t0 + k*beat/2, .02 if k % 2 else .035, .3)
    mix = np.array([np.convolve(c, np.ones(6) / 6, 'same') for c in mix])
    if name == "lofi":  # darker, with a little vinyl crackle
        mix = lowpass(mix, 2600)
        crackle = (rng.random(N) > .9994) * rng.standard_normal(N) * .25 + rng.standard_normal(N) * .004
        mix += crackle[None]
    if cuts:
        n = int(SR * 0.22); tt = np.arange(n) / SR
        swish = np.convolve(rng.standard_normal(n), np.ones(7) / 7, "same") * np.sin(np.pi * tt / tt[-1]) ** 2
        for c in cuts: add(swish, c - 0.12, np.max(np.abs(mix)) * .5)
    fi = max(int(SR * fade_in), 1); fo = min(int(SR * fade_out), N)
    mix[:, :fi] *= np.linspace(0, 1, fi); mix[:, N - fo:] *= np.linspace(1, 0, fo)
    mix /= np.max(np.abs(mix)) * 1.05; pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return name

if __name__ == "__main__":  # python3 music.py out_dir: one 20s sample of every style
    import pathlib, sys
    d = pathlib.Path(sys.argv[1]); d.mkdir(parents=True, exist_ok=True)
    for s in STYLES: bed(20, d / f"{s}.wav", s); print(s, d / f"{s}.wav")
