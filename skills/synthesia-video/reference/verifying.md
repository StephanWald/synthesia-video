# Verifying a render without watching it

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 out/film.mp4

# speech map: silences >= 0.7 s below -35 dB, printed as start -> end (length)
ffmpeg -i out/film.mp4 -af "silencedetect=noise=-35dB:d=0.7" -f null - 2>&1 \
  | grep -oE 'silence_(start|end): [0-9.]+' | paste - - | awk '{printf "%s -> %s (%.1f s)\n",$2,$4,$4-$2}'

# contact sheet, one tile every 2.5 s at 30 fps
ffmpeg -y -i out/film.mp4 -filter_complex "[0:v]select='not(mod(n\,75))',scale=320:-1,tile=6x6" -frames:v 1 out/check/contact.png

# frame strip around a cut (drawtext may be unavailable; keep the timestamps in your notes)
i=0; for t in 17.0 18.0 19.0 20.0 21.0 22.0; do i=$((i+1)); ffmpeg -loglevel error -y -ss $t -i out/film.mp4 -frames:v 1 -vf scale=480:-1 out/check/a_$i.png; done
ffmpeg -y -i out/check/a_%d.png -filter_complex tile=3x2 out/check/strip.png
```

Then Read the PNGs. Match the silence map against the scene table: each clip boundary shows as a
~2 s silence; a graphic frozen for long means the speech outran the picture (re-time the picture),
and a long silence inside a clip means a `<break>` or a leading-break delay.

Pronunciation and voice quality cannot be checked this way; ask the user to listen at the timestamp.
