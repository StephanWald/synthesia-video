---
name: synthesia-video
description: Build Synthesia avatar videos from a scene table with the Synthesia API. Use when the user mentions Synthesia, an avatar video, api.synthesia.io, a SYNTHESIA_API_KEY, or wants to script, render, or iterate on a presenter video. Scaffolds a working project (a seven-clip reference film), knows the API's shape and gotchas, and runs a Python build that exports HTML graphics, uploads assets, renders free test videos, syncs animations to the measured voice, casts a second presenter, and joins pictures to a real person's recorded voice when the render is only an animatic.
license: MIT
---

# Synthesia video projects

A Synthesia video is best treated as a **build**, not a document: a scene table in Python is the
source of truth, graphics are exported to MP4/PNG, assets are uploaded once (cached by hash), and
every render is a fresh, immutable video. Studio is the preview and hand-tweak surface, not the source.

## The scaffold is a working reference film

`scaffold/` is a complete project, the **reference build**: a ~1:53 film in seven clips, each demonstrating one
lesson and saying which. Its plan and render log are `scaffold/SCENEPLAN.md`, and `scaffold/CLAUDE.md` lists
every command. Rendering it once (`all`, `render`, then the sync loop) is the quickest way to see every piece
work on a new machine and account; it costs one free test render.

| clip | kind | lesson |
|---|---|---|
| r1 | cam | stock presenter full frame on an uploaded black PNG; "." before a leading break |
| r2 | image, `cards.css` | the `SUBS` pronunciation table (incl. an IPA alias); paragraphs and "..." shape the read |
| r3 | video, `stage.js` | animation timed by `BEAT`s, then synced to its frozen voice: `sync.py` → `export` → `mux` → `assemble` |
| r4 | image, `stage.js` | a still drawn with the animation stylesheet (no `beats()`: the cold frame is the card) |
| r5 | cam, `align="left"` | the host hands off to a second presenter on a cut |
| r6 | image + `inset=` | the expert (`who="expert"` from `CAST`) standing scaled down in the corner of his card |
| r7 | image, `cards.css` | silent end card, a lone break, last so it can be cut off |

In the rendered reference, every clip but r3 carries the test watermark: r3 was re-synced and muxed locally.

**Default cast** (stock, confirmed to render via the API, Sep 2026): host Carly
`c43d0b11-61e9-483c-a0f7-26a7bfcb6510` with voice Zola - Neutral en-US `13173f72-713d-49b9-a511-2b1f575a5a5d`
(Studio calls it Noa); expert Jaz (EXPRESS-1) `894c9b8a-e3a7-40b7-b7e6-7441faceb46e` with his matching voice
Jaz - Breezy en-US `0f023a7e-c569-4c50-ac93-6f365ac722ee`. Also known to work: Joshua (EXPRESS-1)
`0d2356ca-b688-419a-b08b-9264e5a6a94e` with Jude – Kind en-GB `aa8eec58-2776-488d-9f52-b9bece58c5a6`. Never use
the user's own avatar or voice unless they ask.

**Needs:** Python 3 (no packages; the API client uses `curl`), `ffmpeg`, Node with Playwright (`npm install` in
the project) and a browser (`$CHROME_PATH`, Chrome in /Applications, or `npx playwright install chromium`).
Pages that load Google Fonts need network at export time, or they fall back silently (Barlow Condensed → Arial
Narrow). Optional: `pdftoppm` for decks, `mlx-whisper` (or any Whisper) for recovering Studio edits.

## The house file: a user's or team's standing choices

Pronunciations, the default cast and house rules belong to a person or a company, not to one film and not to
this skill. They live in a JSON file outside the plugin, which an update never touches:
`$SYNTHESIA_HOUSE`, else `./house.json` in the project, else `~/.claude/synthesia-house.json`.

```json
{
  "subs":  [["kubectl", "cube control"], ["nginx", "engine X", "ˈɛndʒɪn ɛks"]],
  "cast":  {"host": {"avatar": "<id>", "voice": "<id>"}, "expert": {"avatar": "<id>", "voice": "<id>"}},
  "rules": ["Never say 'game changer'.", "Product names as on the website."]
}
```

- `build.py` merges `subs` into `SUBS` (a term in the film's own `SUBS` wins) and `cast` over the stock `CAST`.
- `rules` are for whoever writes the scripts: **read the house file before writing or editing any script**, and
  follow its rules like the user's own instructions.
- Two levels: a term only this film uses goes in the film's `SUBS` (`tools/build.py`, and `SCENEPLAN.md` §2);
  a term the user or their company says in every film goes in the house file.
- When the user fixes a pronunciation or states a lasting preference ("always say it like this", "our host is
  …"), offer to add it to the house file rather than only to the film. If there is no house file yet, offer
  to create `~/.claude/synthesia-house.json` with that first entry; do not create it unasked.
- A worked example for a software company is in the plugin repo's `examples/` folder.

**Writing a pronunciation** (`[term, alias]` or `[term, alias, ipa]`):
- The alias is what the voice should read, spelled the way it sounds: `engine X`, `cube control`, `sequel`.
  Letters are spaced capitals (`B B J`, `A P I`); a word that must stay one word stays one word (`webfor Jay`,
  not `web for Jay`).
- Add IPA only when spelling cannot pin it down (a name, a stress, a vowel): `["Louwman", "Lauman", "ˈlaʊmɑn"]`.
- Matching is whole-word and case-sensitive, longest term first, so `PostgreSQL` is not caught by `SQL`; list
  each written form that occurs (`BBj`, `BBjServices`).
- Two terms that must sound different in one breath (e.g. "AI" and "API") both get an entry.
- Verify by ear: the API cannot tell you how a word sounded. Put new terms in a short clip, render a test,
  and ask the user to listen at the timestamp. If the user fixes a word in Studio's pronunciation tool, copy
  the fix back into `SUBS` or the house file, or the next API render loses it.

## First thing in a new project

0. Write `SCENEPLAN.md` with the user, keeping the sections of `scaffold/SCENEPLAN.md` (filled in there for
   the reference film). It is the contract the build reads off: runtime budget, vocabulary and every `<sub>`
   pronunciation, one row per clip (kind, speaker, picture, exact script, picture cues), the graphics to build
   with their tunables, external material with expected paths and placeholders, decisions not to reopen, the
   verification checklist and the render log. Most first-render surprises come from fields this plan makes
   mandatory. **Settle first whose voice and face the film carries** (see "Synthesia as the animatic" below):
   it decides whether a render is the deliverable or a preview.
1. Copy the whole `scaffold/` folder into the project root, then replace the reference film's content:
   `SCENES`, `TITLE` and `CALLBACK` in `tools/build.py`, the `r*.html` pages, `SCENEPLAN.md` and `CLAUDE.md`.
   Keep `tools/` (`build.py`: `words`, `script`, `export`, `upload`, `request`, `all`, `render`, `mux`,
   `assemble`; `sync.py`: `cuts`, `voice`, `beats`; `synthesia.py` API client; `export-frames.mjs`; `verify.sh`),
   `cards.css`, `stage.css`, `stage.js`, `.env.example`, `.gitignore`, `package.json`. Drop the exporter, the CSS
   and `package.json` only if nothing is HTML (e.g. a PDF deck). Start with an empty `out/`; run `npm install`.
2. The API key lives in `.env` as `SYNTHESIA_API_KEY=…` (git-ignored). Never print it or commit it.
   If `.env` is missing, ask the user to create it; the key comes from account settings on app.synthesia.io
   and belongs to the account, not the workspace. API access needs a Creator plan or above.
3. Presenters: keep the default cast, take the house file's, or ask for **avatar and voice IDs** (Studio:
   three-dot menu on the avatar, "Copy ID"), or look them up in the docs tables
   (`https://docs.synthesia.io/reference/avatars.md` and `/voices.md`: the `.md` form is the raw table; grep by
   name and locale). **The docs list IDs the API refuses:** of four "Carly" rows, two returned 400
   `Avatar not found` (Sep 2026), and the table does not say how variants differ, so let the user pick in
   Studio or confirm with one short test render. The API checks every clip before rendering and names only
   the first bad ID, so a request with several unknown IDs fails once per ID. Personal avatars and voice clones
   are IDs too, but EXPRESS-2 avatars were refused by the API: render with a stock avatar and let the user swap
   theirs in Studio on the draft the render creates.
4. Write the project's agent file, `CLAUDE.md` for Claude Code or `AGENTS.md` for Codex: the build commands and
   every project-specific decision.

## Working loop

```
python3 tools/build.py words      # word count and runtime estimate (check against the budget before rendering)
python3 tools/build.py all        # export graphics -> out/, upload changed assets, write out/request.json
python3 tools/build.py render     # TEST render (free, watermarked), wait, download out/film.mp4
python3 tools/build.py render --final   # spends video minutes; ONLY on an explicit ask
sh tools/verify.sh                # duration, silence map (out/check/silences.txt), contact sheet
```

- **Always `test: true` unless the user explicitly asks for a final render.** Test renders cost nothing
  and are watermarked; a watermark cannot be removed afterwards, so a final render is a one-way decision.
  Docs cap test videos at 30 per day, and a scene's script at 5 minutes of speech. A request the API refuses
  still uses up a take number; that is fine, log it.
- Every render is a new video (version 1). The API cannot edit scenes, add a version, or see Studio
  drafts; `PATCH` changes title/description/visibility only. Superseded test videos can be deleted with
  `DELETE /v2/videos/{id}` on request — never unprompted.
- Verify renders without watching them: `ffprobe` for duration, `silencedetect` for the speech map,
  and ffmpeg frame strips at the cut points (see `reference/verifying.md`). Read the PNGs.
- Iterate with the user reviewing in Studio; fold anything they fix there (a pause, a pronunciation)
  back into the scene table so the repo stays the source. **The API cannot show you those edits**: the video
  record has no script. A Studio edit puts the record back to `in_progress` with the thumbnail under
  `versions/N`; download the new version, transcribe it locally (e.g. mlx-whisper, `whisper-large-v3-turbo`,
  word timestamps), diff the word list against the previous version's transcript, and read the user's
  paragraph breaks and full stops off the inter-word gaps (0.4–0.7 s), inserted breaks off gaps ≥ 1.5 s.
  Then write wording and paragraphs back into the scene table.
- **A download can contain Studio edits the request never asked for.** Each render leaves a draft in Studio;
  when the user edits it (e.g. swaps in their own avatar on the presenter clips), later downloads of that video
  id return the edited version. Before blaming the build for an odd picture, ask whether they touched it in
  Studio. `render` keeps each take's own file as `out/film-takeN.mp4`.

## Synthesia as the animatic (a real person's voice and camera)

When the film's point is that a real person is speaking (an invitation, a personal close), the render is
only the animatic: stock voice and avatar, for reviewing wording, timing and card order as a film. The
finished film is made outside Synthesia:

- `build.py script` prints each clip's text clean (no SSML, one paragraph per line, with its speaker): the
  recording sheet. Recordings go to `out/voice/<id>.mp3` (set `audio=` on the clip); camera clips to
  `out/cam/<id>.mp4`.
- `build.py mux` joins each picture to its recording in `out/scenes/<id>.mp4` (a still holds for the voice +
  1 s; an animation keeps its length). An editor cuts those with the camera files. No watermark, no final render.
- The ~2 s per clip boundary exists only in the animatic; the finished film is shorter by that much per cut.
- The speaker reads the same pronunciations as the `SUBS` table; put them in the plan so the reading matches.

The opposite case is just as common: **when the Synthesia-hosted video is the deliverable, it stays native.**
A local composite (a presenter placed where the API cannot put it, a muxed voice) is then only a timing or
layout check, never the result; say so when showing it, and deliver the Synthesia render.

## Two presenters: a host and an expert

The API puts **exactly one avatar in each clip**, so a second presenter is a cast, not a composite:

- `CAST` in `tools/build.py` maps a role to an avatar and its voice (`host`, `expert`, …); a clip picks its
  speaker with `who=` (default `host`). Keep each voice next to its avatar: the API takes any voice with any
  face, so a mismatch is easy to make and only audible. Matched pairs exist in the voices table (avatar Jaz,
  voice "Jaz - Breezy"). If `voice` is omitted, the API uses the avatar's recommended voice.
- **The hand-off is a cut.** Write it as a turn: the host ends on the hand-off line ("over to our expert..."),
  the expert opens by answering it ("Thanks, Carly."). Standing the host to one side (`align="left"` on a cam
  clip, i.e. `horizontalAlign`) makes the next clip read as someone else's turn.
- **The expert over a picture:** `inset=dict(align="right", scale=0.6)` on an image/video clip renders the
  speaker as a `rectangular` avatar scaled from the bottom corner (`verticalAlign` is fixed to bottom and not
  exposed). At 0.6 bottom-right the figure takes roughly the right 650 px, head at mid-height; leave the right
  ~800 px of the page empty. That is 16:9. **In other aspect ratios `left` and `right` put the avatar off-screen;
  only `center` is reliable**, and there is no X/Y field (`reference/api.md`).
- **Not `circular`** for this: a circle is fixed to the centre of the frame, `horizontalAlign` with it is a 400
  (`Not applicable when style: circular`), and scale 1.0 fills the full height. It suits a round cut-out over a
  screen recording, nothing beside a card.
- **Both presenters in one frame is Studio-only** (two avatars on a scene). If a film needs it, render the
  clips from the API and add the second avatar to that scene in Studio, or use a template.

## Request shape (what actually works)

One `POST /v2/videos` with `input: [clip, clip, …]`; each clip is `avatar`, `background`, `scriptText`
(or `scriptAudio`), `avatarSettings`, optional `backgroundSettings`, `transition`.

- Graphic clip: uploaded MP4/PNG as `background`, `avatarSettings.style: "voiceOnly"`,
  `backgroundSettings.videoSettings: { shortBackgroundContentMatchMode: "freeze", longBackgroundContentMatchMode: "extend_content" }`
  so the picture plays out fully and holds its end frame.
- Presenter clip: `avatarSettings.style: "rectangular"` (full body) on a background asset (upload a
  solid PNG for a plain colour; no black stock background exists).
- **Decide the face at request time.** A `voiceOnly` clip cannot be turned into a visible presenter in Studio
  afterwards; if a clip may need the avatar, send it `rectangular`.
- Any aspect ratio other than 16:9: presenters at `center` only, and check where the background lands in
  the first test (a 4:5 card was once seen offset; `reference/api.md`).
- Upload host is different: `POST https://upload.api.synthesia.io/v2/assets`, raw body, `Content-Type`
  `video/mp4 | video/webm | image/png | image/jpeg | image/svg+xml`; MP3 goes to `/v2/scriptAudio`
  (async: poll `GET /v2/assets/{id}` before rendering).
- `scriptLanguage` is valid **only with `scriptAudio`**; with text the API returns 400. The voice sets
  the language, so choose voice IDs from the right locale row of the docs' voice table.
- `test`, `title`, `visibility: "private"`, `aspectRatio: "16:9"`, `callbackId` at the top level.
- **Every render gets a take number and a timestamp in its title**, e.g. `Film title · take 4 · 2026-09-16 11:40`
  (the scaffold's `render` does this from `out/take.txt`, and puts the same tag in `callbackId`). Studio's list
  shows every video as "1 hour ago" after a short while, so the title is the only way to tell takes apart.
  Log each take (take, runtime, what changed, measured cuts) in `SCENEPLAN.md` §8.

## Script gotchas (SSML)

- `<break time="1.5s"/>` pauses; `<sub alias="engine X" ipaAlias="ˈɛndʒɪn ɛks">nginx</sub>` fixes pronunciation.
  Keep scripts as plain prose and let `SUBS` (plus the house file) add the `<sub>` markup at request time.
- A script that **begins** with a bare `<break>` delays the picture by the same time. Put a "." first:
  `. <break time="2s"/> Owning it is.`
- A clip whose script is only a `<break>` renders about 1.5 s longer than asked (`5s` ≈ 6.5 s, `10s` ≈ 11.5 s).
  That is how to make a silent card, e.g. an end card.
- Every clip boundary carries roughly 1.9–2.3 s of silence (lead-in plus tail) that the API cannot trim.
  Nine clips cost about 18 s of air; budget for it and prefer fewer clips.
- **Budget the pauses first, then measure.** In a short film the air dominates: five clips and 73 words ran
  43.6 s; cutting two inserted 1.5 s breaks to 0.1 s and the end card's break from 2 s to 1 s gave 38.2 s, the
  end card 2.9 s, and the boundaries still carried ~2 s each. Count words at the measured rate, add ~2 s per
  boundary and every break (+1.5 s for a break-only clip), then render and measure.
- Speech rate depends on the material: a stock voice read 2.8 words/s on long narration but 3.4 words/s on
  short card scripts. Do not time animations to a storyboard's guesses; measure the rendered speech with
  `silencedetect` and pace the picture to it.
- **Anything that expires (a date, a place, a price, an address) goes on a silent end card, last in the film,**
  never in the spoken script: when the details change, the editor cuts the card and nothing else moves.

**Punctuation and paragraphs shape the voice, not just the pauses:**
- Ending a sentence with "..." or with "!" makes the read more natural, especially on a segue line
  ("That is what is next..."). The voice modulates on the punctuation, not only on the break.
- Paragraph breaks (line feeds in `scriptText`) give the narration structure: a new paragraph is read
  with a new tonal onset. Write scripts as short paragraphs, one thought each, rather than one block,
  and put a paragraph break where the picture changes.
- So when a read sounds flat, fix the text first (punctuation, paragraphing, sentence length) before
  reaching for `<break>` or Studio's speed control.

## Graphics

HTML pages are rendered deterministically by `tools/export-frames.mjs` (virtual clock, headless Chromium via
Playwright, 1920×1080 PNG frames) and encoded by ffmpeg. Two stylesheets ship with the scaffold: `cards.css`
(text cards) and `stage.css` + `stage.js` (one SVG per page, drawn from primitives, animated by beats). Pages
accept tuning via URL query (`?beats=…`), which the exporter passes through. The build clears the frames
folder before each export, since stale frames would be encoded too.

### Voice-synced animation (no word triggers in the API)

Studio can trigger an element on a spoken word; the API cannot (no trigger, marker or animation field; spec
checked Sep 2026). Templates would carry Studio's triggers, but whether they survive a script filled in as a
variable is untested, and the picture would have to be Studio elements. So the animation is timed to the
*measured* speech, locally:

- Every beat boundary in the script is one `BEAT` (`<break time="1.5s"/>`); every beat is one step of the
  animation. Not shorter: sentence pauses in long narration reach 1.0 s, and a 0.8 s break could not be told
  apart from them; 1.5 s renders as >= 1.5 s. Compute every frame from time alone in JS (`render(t)`), never
  CSS animation or transitions: the exporter's clock is virtual and CSS runs on real time.
- **The TTS is not repeatable between renders.** The same script, re-rendered, moved its beats by up to 6 s
  within a two-minute scene. It is not random either: a voice may have two or three reads of a script and
  return one of them, identical to the hundredth of a second. So measure-and-re-render never locks the sync;
  **freeze the voice** of one render instead and sync the picture to that file.
- The loop in the scaffold: `render` (the first export uses an estimate: 0.8 s lead, 2.8 words/s, plus the
  pauses), then `sync.py cuts` (clip boundaries: the strongest picture change inside each silence of >= 1.2 s;
  presenter cuts score 0.4–0.7, two pictures on one stylesheet as little as 0.02), `sync.py voice` (each
  `audio=` clip's voice cut out of the render; test renders watermark only the picture; it never overwrites an
  existing file, so a real recording is safe), `sync.py beats` (beat 0 = end of the lead-in silence, then every
  pause >= 1.3 s), `build.py export` (re-exported on the measured beats, never shorter than the voice), `mux`,
  and `assemble` (the render cut at its boundaries with the muxed scenes spliced in: `out/assembled.mp4`).
- A new voice or a re-render invalidates the frozen voice, the beats and the cuts: delete `out/voice/`,
  `out/beats.json`, `out/cuts.json`, `out/scenes/` and run the loop again. An estimate drifted 5.5 s over a
  one-minute scene, so measure every time.
- `scriptAudio` (an uploaded MP3 as the clip's voice) would let Synthesia play the frozen voice itself, but some
  plans refuse it (400 `FEATURES_AUDIO_UPLOAD_DISABLED`); check before designing around it.
- With `longBackgroundContentMatchMode: extend_content` and `short…: freeze`, the clip lasts as long as the
  longer of voice and animation. Export throughput is ~15 frames/s from headless Chromium: a ten-minute film
  is ~20 minutes of export, so run long exports in the background.

### Stills from the animation stylesheet

A picture card does not need beats: a `stage.js` page with every element drawn as base and no `beats()` call is
a still, and `kind="image"` exports its one frame at 4 s, which is then the finished card. One stylesheet
serves animated and still cards, so stills match the animations they sit next to.

## Slides and decks (PPTX, Google Slides, PDF)

The API has no deck import. A slide is a still: one PNG per slide, uploaded as an asset, used as the
`background` of an `image` clip with `voiceOnly` (or an `inset=` presenter over it).

- PPTX → `soffice --headless --convert-to pdf deck.pptx`, then `pdftoppm -png -r 144 deck.pdf out/slides/s`
  (or Keynote/PowerPoint export). Google Slides → File ▸ Download ▸ PDF, then the same. Author on 16:9,
  1920×1080; a 4:3 deck letterboxes.
- Each slide is a clip and costs the same ~2 s boundary silence as any clip. Merge adjacent slides where the
  script allows; many thin slides inflate the runtime.
- **Slide animations do not survive.** Studio's `Import PowerPoint` is Studio-only (not on the API) and the
  docs state animations are not imported; speaker notes become scripts. Studio's own per-element animations
  live in Studio only and are lost on the next API render.
- To keep motion, export the deck to MP4 yourself (PowerPoint ▸ Export ▸ Video) and use it as a `video` clip;
  timing is then fixed per slide. A slide that needs one build is cheaper as a small `stage.js` page, which the
  sync loop can time to the voice.

## Reference

- `reference/api.md` — endpoints, fields, limits, verified against the OpenAPI spec (Sep 2026); what the API
  cannot put on screen and the template route around it.
- `reference/verifying.md` — ffmpeg recipes for checking a render without watching it.
- Docs: https://docs.synthesia.io/reference/introduction · avatars: /reference/avatars · voices: /reference/voices
- OpenAPI: https://api.synthesia.io/api/openapi/swagger.json
