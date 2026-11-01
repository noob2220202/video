"""Re-dub mixer.

Usage: python mix.py lines.json no_vocals.wav vocals.wav gen_dir video_in out.mp4

- Keeps music/SFX (no_vocals) intact.
- Keeps the original vocal stem everywhere EXCEPT the dialogue windows listed in
  lines.json (so screams / effort sounds stay), with short fades at the edges.
- Each generated line (gen_dir/line_XX.wav) is trimmed, time-fitted to its slot,
  lightly EQ'd + reverbed, loudness-matched to the original line, and placed.
"""
import json, subprocess, sys, tempfile, os
import numpy as np
import soundfile as sf

SR = 44100
PAD_PRE, PAD_POST, FADE = 0.08, 0.15, 0.05
MAX_SPEEDUP = 1.35


def ff(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def load(path):
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    assert sr == SR, (path, sr)
    return a


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


def prep_line(src, target_dur, tmp):
    """Trim silence, fit to target duration, EQ + small room, stereo 44.1k."""
    trimmed = os.path.join(tmp, "t.wav")
    ff(["-i", src, "-af",
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,"
        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse",
        "-ar", str(SR), "-ac", "1", trimmed])
    dur = sf.info(trimmed).duration
    tempo = 1.0
    if dur > target_dur:
        tempo = min(dur / target_dur, MAX_SPEEDUP)
    out = os.path.join(tmp, "p.wav")
    ff(["-i", trimmed, "-af",
        f"atempo={tempo:.4f},highpass=f=90,equalizer=f=3000:t=q:w=1:g=1.5,"
        "acompressor=threshold=-22dB:ratio=3:attack=5:release=80:makeup=2,"
        "aecho=0.85:0.5:35|70:0.18|0.10,"
        "afade=t=in:d=0.01",
        "-ar", str(SR), "-ac", "2", out])
    return load(out), dur, tempo


def main(cfg_path, nov_path, voc_path, gen_dir, video_in, out_mp4):
    cfg = json.load(open(cfg_path))
    nov, voc = load(nov_path), load(voc_path)
    n = min(len(nov), len(voc))
    nov, voc = nov[:n], voc[:n]

    gain = np.ones(n, dtype=np.float32)
    new = np.zeros_like(voc)
    f = int(FADE * SR)
    report = []
    with tempfile.TemporaryDirectory() as tmp:
        for L in cfg["lines"]:
            s = int(max(0, L["start"] - PAD_PRE) * SR)
            e = int(min(n / SR, L["end"] + PAD_POST) * SR)
            orig_level = rms(voc[int(L["start"] * SR):int(L["end"] * SR)])
            # duck original vocal with fades
            gain[s:e] = 0.0
            gain[max(0, s - f):s] = np.minimum(gain[max(0, s - f):s], np.linspace(1, 0, s - max(0, s - f)))
            gain[e:e + f] = np.minimum(gain[e:e + f], np.linspace(0, 1, len(gain[e:e + f])))

            src = os.path.join(gen_dir, f"line_{L['id']:02d}.wav")
            seg, dur, tempo = prep_line(src, L["end"] - L["start"], tmp)
            seg *= orig_level / rms(seg)
            p = int(L["start"] * SR)
            m = min(len(seg), n - p)
            new[p:p + m] += seg[:m]
            report.append(f"line {L['id']:2d} {L['spk']:7s} slot={L['end']-L['start']:.2f}s gen={dur:.2f}s tempo={tempo:.2f}")

    mix = nov + voc * gain[:, None] + new
    peak = np.abs(mix).max()
    if peak > 0.98:
        mix *= 0.98 / peak
    wav = os.path.splitext(out_mp4)[0] + "_audio.wav"
    sf.write(wav, mix, SR)
    sf.write(os.path.splitext(out_mp4)[0] + "_dialogue_only.wav", new, SR)
    ff(["-i", video_in, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4])
    print("\n".join(report))


if __name__ == "__main__":
    main(*sys.argv[1:7])
