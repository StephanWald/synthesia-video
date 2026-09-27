# Scene plan — Synthesia reference build

One document the build reads off. Every section maps onto something the build needs; an empty field means
the build guesses and the first render shows the guess. For a new film, copy this project, keep the section
structure, and fill every section with the user before writing code or HTML.

This plan is filled in for the reference film: seven clips, one lesson each, no real use case.

## 1. Frame

| Field | Value |
|---|---|
| Runtime target / ceiling | 1:50 / 2:00. Take 5 measured 1:53. |
| Format | 16:9, 1920×1080, true black, off-white Barlow Condensed, no colour, hard cuts |
| Presenter (host) | stock Carly `c43d0b11-61e9-483c-a0f7-26a7bfcb6510`, voice Zola - Neutral en-US `13173f72-713d-49b9-a511-2b1f575a5a5d` (Studio calls it Noa). Two other Carly IDs in the docs table (`c75b9aaf…`, `595f50a9…`) are refused as "Avatar not found" |
| Second presenter (expert) | Jaz (EXPRESS-1) `894c9b8a-e3a7-40b7-b7e6-7441faceb46e`, voice Jaz - Breezy en-US `0f023a7e-c569-4c50-ac93-6f365ac722ee`. `CAST` in `tools/build.py` (a house file can override it); a clip picks its speaker with `who=` |
| Presenter framing | full frame on an uploaded black PNG (there is no black stock background); the host stands left when handing off; the expert stands scaled down (0.6) in the bottom-right corner of his card |
| Voice | stock TTS. For a film that needs a real person: the user's recording, read from `build.py script`, set as `audio=`, joined by `mux` |
| What Synthesia is for | here: the render is the film, with the animated clip re-synced and spliced by `assemble`. With the user's own voice: the render is only the animatic |
| Test renders | `test: true` always; final render only on the user's explicit word |

**Budget rule:** each clip boundary costs ~1.9–2.3 s of silence; stock voices read 2.8 (long narration) to 3.4
(short card scripts) words a second. Runtime ≈ words ÷ 2.8 + 2.2 × (clips − 1) + holds. `build.py words`.

## 2. Vocabulary and pronunciation

`SUBS` in `tools/build.py` wraps every occurrence at request time; scripts stay plain prose. Terms from the
house file (`~/.claude/synthesia-house.json` or `./house.json`) are added; a term listed in `SUBS` wins.

| Term | Say | SSML |
|---|---|---|
| nginx | "engine X" | `<sub alias="engine X" ipaAlias="ˈɛndʒɪn ɛks">nginx</sub>` |
| kubectl | "cube control" | `<sub alias="cube control">kubectl</sub>` |
| SQL | "sequel" | `<sub alias="sequel">SQL</sub>` |
| PostgreSQL | "Postgres Q L" | `<sub alias="Postgres Q L">PostgreSQL</sub>` |

## 3. Clips

**A clip is one background plus one script.** A presenter and a graphic at once are two clips, or one clip
with the presenter scaled into a corner (`inset=`); the API cannot put two avatars in one frame.

| # | id | kind | picture | ~words | lesson |
|---|---|---|---|---|---|
| 1 | r1 | cam | black | 45 | presenter clip; "." before a leading break |
| 2 | r2 | image | `r2.html` (cards.css) | 34 | pronunciation table; paragraphs and "..." shape the read |
| 3 | r3 | video | `r3.html` (stage.js, 4 beats) | 46 | animation synced to the voice: BEAT, measure, export, mux |
| 4 | r4 | image | `r4.html` (stage.js, no beats) | 54 | a still on the animation stylesheet; why the voice is frozen |
| 5 | r5 | cam, `align="left"` | black | 19 | the host hands off on a cut |
| 6 | r6 | image + expert, `inset=` | `r6.html` (cards.css, right 800 px empty) | 63 | a second presenter from `CAST`, standing over the picture |
| 7 | r7 | image | `r7.html` (cards.css) | 0 | silent end card: a lone `<break time="5s"/>` ≈ 6.5 s |

Scripts: `SCENES` in `tools/build.py`; `build.py script` prints them clean. Script rules: short paragraphs,
one thought each (a new paragraph is a new tonal onset); "..." and "!" make segues natural; a leading break
needs a "." before it or the picture starts late; every beat of an animation is one `BEAT`
(`<break time="1.5s"/>`), never shorter.

## 4. Graphics

| file | kind | what it shows | tunables |
|---|---|---|---|
| `r2.html` | text card | the written / said / sent table | — |
| `r3.html` | animation | four boxes dim from the cold frame; each beat lights one and draws the wire into it; foot line on the last | `?beats=` (from build.py) |
| `r4.html` | still | the sync loop as five boxes, the last one white-stroked | — |
| `r6.html` | text card | two presenters, one cast; the right 800 px left empty for the expert | — |
| `r7.html` | text card | the end card | — |

Minimum sizes: 22 px on a picture card, 30 px on a text card, at 1920×1080.

## 5. External material

| item | expected path | supplied by | until then |
|---|---|---|---|
| a frozen voice per animated clip | `out/voice/<id>.mp3` | `sync.py voice` from a render, or the user's recording | the estimate in `beat_times()` |
| the user on camera, if any | `out/cam/<id>.mp4` | user | stock avatar |

## 6. Decisions already made

- Sync is local (`mux`), not in Synthesia: the TTS is not repeatable between renders, and uploaded audio
  (`scriptAudio`) was refused on the plan this was built with. Check your plan before designing around it.
- Studio's word triggers are not used: the API has none, and the template route is untested.
- Picture cards use the stage stylesheet with no beats rather than a separate still design, so stills match animations.
- Anything that expires sits on the silent last card, so it can be cut without touching the rest.

## 7. Verification checklist (after each render)

- [ ] `ffprobe` duration against §1
- [ ] `sync.py cuts`: one cut per boundary found; each boundary ≈ 2 s of silence
- [ ] frames either side of every measured beat in `out/assembled.mp4`: the next step lights when the voice resumes
- [ ] contact sheet: presenter full frame on black in r1 and r5; the expert in the corner of r6; the right card up in each clip
- [ ] pronunciation checked by ear at r2 (engine X, cube control, sequel, Postgres Q L)
- [ ] anything fixed in Studio copied back (the API cannot see Studio edits; transcribe and diff)

## 8. Render log

| date | take | test | runtime | notes |
|---|---|---|---|---|
| 27 Sep 2026 | 1 | yes | 1:22 | five clips, stock Joshua + Jude. Cuts 18.03, 32.53, 55.93, 75.23 s (scores 0.44 presenter, 0.075 / 0.072 / 0.116 cards). r3 estimate `[0.8, 8.01, 14.16, 18.16]`, measured from its voice `[0.7, 7.55, 13.69, 18.33]`; re-exported, muxed, assembled; every step lights on its beat. |
| 27 Sep 2026 | 2 | yes | 1:24 | Carly + Zola; voice, beats and cuts re-measured (a new voice invalidates all three). r3 measured `[0.9, 7.23, 13.55, 17.49]`. |
| 27 Sep 2026 | 3 | yes | — | refused before rendering: 400 `horizontalAlign: Not applicable when style: circular`. A circular avatar is fixed to the frame centre; the expert became a scaled rectangular avatar anchored bottom-right. The take number was spent anyway. |
| 27 Sep 2026 | 4 | yes | 1:53 | r5 (host hands off) and r6 (the expert over his card) added. The first four clips came back identical to take 2 to the hundredth: the same read again. |
| 27 Sep 2026 | 5 | yes | 1:53 | r2 with neutral example terms (nginx, kubectl, SQL, PostgreSQL). Cuts 18.47, 33.83, 56.87, 77.03, 85.17, 105.80 s; r3 measured `[0.91, 7.24, 13.56, 17.5]`; assembled 112.8 s, every step on its beat. The reference film. |
