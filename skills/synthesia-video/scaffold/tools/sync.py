#!/usr/bin/env python3
"""Make animated clips follow the voice. The API cannot tie a picture to a word, and the TTS is not
repeatable (the same script moved its pauses by up to 6 s between two renders), so the voice of one render is
frozen, measured, and the picture is exported on it and joined to it locally.

  python3 tools/sync.py cuts [out/film.mp4]   # clip boundaries of a render -> out/cuts.json, prints the silence map
  python3 tools/sync.py voice [--force]       # each clip with audio= : its voice cut out of that render (mp3)
  python3 tools/sync.py beats                 # each animated clip's beat times, measured from its voice -> out/beats.json

then `build.py export` (pictures on the measured beats), `build.py mux`, `build.py assemble`.

`voice` never overwrites an existing file without --force: audio= may be a real person's recording, which is
measured the same way (`beats` reads whatever file audio= names).
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build

OUT = build.OUT


def ff(src, args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src] + args + ["-f", "null", "-"],
                          capture_output=True, text=True).stderr


def silences(src, d=0.5):
    log = ff(src, ["-af", f"silencedetect=n=-40dB:d={d}", "-vn"])
    return list(zip([float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)],
                    [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]))


def cuts(film):
    """A clip boundary is ~2 s of silence with a picture change in it. Beats inside an animated clip are
    silences too (1.5 s), and a beat's fade scores ~0.01 while two pictures on one stylesheet may differ by as
    little as 0.02, so each long silence contributes its strongest picture change and the N-1 strongest of
    those are the cuts (presenter cuts score 0.4-0.7)."""
    sil = silences(film)
    meta = ff(film, ["-vf", "select='gt(scene,0.008)',metadata=print", "-an"])
    events = [(float(t), float(s)) for t, s in zip(re.findall(r"pts_time:([\d.]+)", meta), re.findall(r"scene_score=([\d.]+)", meta))]
    cand = []
    for s0, e0 in sil:
        if e0 - s0 < 1.2:
            continue
        inside = [(sc, t) for t, sc in events if s0 - 0.1 <= t <= e0 + 0.1]
        if inside:
            cand.append(max(inside))
    need = len(build.SCENES) - 1
    best = sorted(cand, reverse=True)[:need]
    dur = build.duration(film)
    print(f"{os.path.relpath(film, ROOT)}: {dur:.1f} s, {len(sil)} silences >= 0.5 s, {len(cand)} candidate cuts, {need} needed")
    for s0, e0 in sil:
        mark = next((f"  cut {t:.2f} (score {sc:.3f})" for sc, t in best if s0 - 0.1 <= t <= e0 + 0.1), "")
        print(f"  silence {s0:7.2f} -> {e0:7.2f} ({e0 - s0:.2f} s){mark}")
    if len(best) < need:
        sys.exit("not enough cut candidates; check the render (contact sheet: sh tools/verify.sh)")
    out = {"film": os.path.relpath(film, ROOT), "duration": dur, "cuts": [0.0] + sorted(round(t, 3) for sc, t in best)}
    json.dump(out, open(os.path.join(OUT, "cuts.json"), "w"), indent=1)
    print("cuts:", " ".join(f"{c:.2f}" for c in out["cuts"]), "-> out/cuts.json")


def voice(force=False):
    c = json.load(open(os.path.join(OUT, "cuts.json")))
    film, bounds = os.path.join(ROOT, c["film"]), c["cuts"] + [c["duration"]]
    for k, sc in enumerate(build.SCENES):
        if not sc.get("audio"):
            continue
        dst = os.path.join(ROOT, sc["audio"])
        if os.path.exists(dst) and not force:
            print(sc["id"], "kept", sc["audio"], "(exists; --force to replace)"); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        build.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{bounds[k]:.3f}", "-to", f"{bounds[k + 1]:.3f}",
                   "-i", film, "-vn", "-c:a", "libmp3lame", "-q:a", "2", dst])   # test renders watermark only the picture
        print(sc["id"], f"{bounds[k]:.2f}-{bounds[k + 1]:.2f} ->", sc["audio"], f"{build.duration(dst):.1f}s")


def beats():
    """Beat 0 is where the voice starts (end of the lead-in silence); every later beat is the end of a pause of
    >= 1.3 s (a BEAT asks 1.5 s and renders >= 1.5 s; sentence pauses stay under ~1.1 s). The silence that runs
    to the end of the file is the clip's tail, not a beat."""
    path = os.path.join(OUT, "beats.json")
    out = json.load(open(path)) if os.path.exists(path) else {}
    for sc in build.SCENES:
        a = build.voice_file(sc)
        if sc["kind"] != "video" or build.BEAT not in sc["script"] or not a:
            continue
        dur, sil = build.duration(a), silences(a)
        lead = [e for s, e in sil if s < 0.05]
        b = [round(lead[0], 2) if lead else 0.0]
        b += sorted(round(e, 2) for s, e in sil if s >= 0.05 and e < dur - 0.1 and e - s >= 1.3)
        want = sc["script"].count(build.BEAT) + 1
        ok = len(b) == want
        print(f"{sc['id']:6s} {os.path.relpath(a, ROOT)} {dur:.1f}s  beats {b}" + ("" if ok else f"   <-- expected {want}, not written"))
        if ok:
            out[sc["id"]] = b
    json.dump(out, open(path, "w"), indent=1)
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "cuts": cuts(sys.argv[2] if len(sys.argv) > 2 else os.path.join(OUT, "film.mp4"))
    elif cmd == "voice": voice(force="--force" in sys.argv)
    elif cmd == "beats": beats()
    else: print(__doc__)
