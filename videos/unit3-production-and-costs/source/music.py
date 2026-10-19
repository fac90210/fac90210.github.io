import numpy as np, soundfile as sf
sr = 44100; bpm = 78; beat = 60/bpm; bar = 4*beat
chords = [[57,60,64,67],[53,57,60,64],[48,52,55,59],[55,59,62,65]]  # Am7 Fmaj7 Cmaj7 G6-ish
def f(m): return 440*2**((m-69)/12)
def env(n, a, r):
    e = np.ones(n); na, nr = int(a*sr), int(r*sr)
    e[:na] = np.linspace(0, 1, na); e[-nr:] = np.linspace(1, 0, nr); return e
out = np.zeros(int(sr*bar*len(chords)*2))
rng = np.random.RandomState(3)
for rep in range(2):
    for ci, ch in enumerate(chords):
        t0 = int((rep*len(chords) + ci)*bar*sr); n = int(bar*sr); t = np.arange(n)/sr
        pad = sum(np.sin(2*np.pi*f(m)*t) + .4*np.sin(2*np.pi*f(m)*2*t + 1) for m in ch) * env(n, 1.2, 1.5)
        out[t0:t0+n] += pad*.10
        # soft arpeggio pluck
        for k in range(8):
            m = ch[k % 4] + 12; tt = np.arange(int(beat*sr))/sr; s = int(t0 + k*beat/2*sr)
            p = np.sin(2*np.pi*f(m)*tt)*np.exp(-tt*5)*.12
            out[s:s+len(p)] += p[:max(0, len(out)-s)]
        # gentle kick + hat
        for k in range(4):
            s = int(t0 + k*beat*sr); tk = np.arange(int(.25*sr))/sr
            out[s:s+len(tk)] += np.sin(2*np.pi*(50+90*np.exp(-tk*25))*tk)*np.exp(-tk*10)*.22
            s2 = int(t0 + (k+.5)*beat*sr); th = np.arange(int(.05*sr))/sr
            out[s2:s2+len(th)] += rng.randn(len(th))*np.exp(-th*70)*.03
out /= np.max(np.abs(out))*1.0
fade = int(.05*sr); out[:fade] *= np.linspace(0,1,fade); out[-fade:] *= np.linspace(1,0,fade)
sf.write("music_loop.wav", (out*.9).astype(np.float32), sr)
print(len(out)/sr)
