# CLAUDE.md

A Synthesia film built from a scene table. As shipped, this is the **reference build**: a ~1:53 film in seven
clips, each demonstrating one lesson of the `synthesia-video` skill and saying which. It doubles as the scaffold
a new film starts from: copy it, replace `SCENES`, `TITLE`, `CALLBACK` and the `r*.html` pages, rewrite
`SCENEPLAN.md` and this file, start with an empty `out/`.

## Build

```
python3 tools/build.py words     # word count and runtime estimate
python3 tools/build.py script    # the clean text per clip, with its speaker: a recording sheet
python3 tools/build.py all       # export pages -> out/*.png|mp4, upload changed assets, write out/request.json
python3 tools/build.py render    # TEST render (free, watermarked), waits, downloads out/film.mp4 (+ out/film-takeN.mp4)
python3 tools/build.py render --final   # spends video minutes; only on an explicit ask
python3 tools/sync.py cuts       # clip boundaries of out/film.mp4 -> out/cuts.json, with the silence map
python3 tools/sync.py voice      # each clip with audio= : its voice cut out of the render (never overwrites)
python3 tools/sync.py beats      # beat times measured from those voices -> out/beats.json
python3 tools/build.py export    # animated pages re-exported on the measured beats
python3 tools/build.py mux       # picture + voice -> out/scenes/<id>.mp4, exact sync, no watermark
python3 tools/build.py assemble  # the render with the muxed scenes spliced in -> out/assembled.mp4
sh tools/verify.sh [file]        # duration, silence map, contact sheet in out/check/
```

- The seven clips: r1 presenter (stock host on an uploaded black PNG; the "." before a leading break), r2 text
  card (`cards.css`; the `SUBS` pronunciation table incl. an IPA alias; paragraphs and "..."), r3 animation on
  `stage.js` timed by `BEAT`s and synced by the loop above, r4 a still drawn with `stage.js` (no beats, so the
  cold frame is the card), r5 the host handing off (cam, `align="left"`), r6 the expert (`who="expert"`)
  standing scaled down in the corner of a card (`inset=`), r7 the silent end card (a lone break).
- Speakers come from `CAST`, pronunciations from `SUBS`, both merged with a house file if one exists
  (`$SYNTHESIA_HOUSE`, `./house.json`, `~/.claude/synthesia-house.json`). The house file's `rules` are for
  whoever writes the scripts: read them before writing.
- A new voice or a re-render invalidates `out/voice/`, `out/beats.json`, `out/cuts.json` and `out/scenes/`;
  delete them and run the sync loop again.
- `stage.js` computes every frame from time; never use CSS animation or transitions (the exporter's clock is
  virtual). Beat times come in as `?beats=`; the list in the page only sets the order.
- `.env` holds `SYNTHESIA_API_KEY` (git-ignored). Never print it.
- The exporter needs Playwright (`npm install`) and a browser: `$CHROME_PATH`, Chrome in /Applications, or
  `npx playwright install chromium`. `cards.css` loads Barlow Condensed from Google Fonts, so exports need network.
- Take numbers: `out/take.txt`, stamped into every title. Log each take in `SCENEPLAN.md` §8.
