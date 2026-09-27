# synthesia-video

A Claude Code plugin that makes Synthesia avatar videos **as a build**, not by hand: a scene table in
Python is the source of truth, graphics are HTML pages exported frame by frame, assets are uploaded once,
and every render is a free, watermarked test until you say otherwise.

It grew out of a set of real conference films and carries what they taught: how to sync an animation to a
voice the API will not let you time, how to hand off between two presenters, how to recover wording a
colleague changed in Studio, and a few dozen smaller gotchas of the Synthesia API.

> Not affiliated with or endorsed by Synthesia. You need your own Synthesia account with API access
> (Creator plan or above).

## What it does

Ask Claude for a Synthesia video and the skill:

- **scaffolds a working project**: the scaffold *is* a seven-clip reference film, each clip demonstrating
  one lesson and saying which, so the first render proves your setup end to end;
- **plans with you** in a `SCENEPLAN.md` (runtime budget, pronunciations, one row per clip, render log);
- **builds**: exports HTML cards and animations to PNG/MP4, uploads only what changed, writes the request;
- **renders test videos** titled with a take number and time, and checks them without watching
  (silence map, cut detection, frame strips);
- **syncs animations to the voice**: the API has no word triggers and its voice is not the same twice, so
  it freezes one render's voice, measures the pauses, re-exports the picture on them and splices the clip
  back in, watermark-free;
- **casts a second presenter**: a host hands off to an expert, who can stand scaled down beside a picture;
- **uses a real person's voice**: prints a recording sheet, and joins the recordings to the pictures when the
  Synthesia render is only the animatic.

## Install

In Claude Code:

```
/plugin marketplace add StephanWald/synthesia-video
/plugin install synthesia-video@stephanwald
```

or from a terminal:

```
claude plugin marketplace add StephanWald/synthesia-video
claude plugin install synthesia-video@stephanwald
```

Then start a session in an empty folder and ask for a video ("make a 90-second Synthesia explainer about …").

### Requirements

- A Synthesia API key (account settings on app.synthesia.io), put in the project's `.env` as
  `SYNTHESIA_API_KEY=…`. It never leaves your machine except to Synthesia's API.
- Python 3 and `curl` (no Python packages), `ffmpeg`, Node.js.
- Playwright in the project (`npm install`) and a browser: Google Chrome, `$CHROME_PATH`, or
  `npx playwright install chromium`.
- Network at export time (the cards load a Google Font).
- Optional: `pdftoppm` for slide decks, Whisper (e.g. `mlx-whisper`) to recover edits made in Studio.

## Make it yours: pronunciations, presenters, house rules

The easiest way is to just say it: *"always pronounce kubectl as cube control"*, *"our host is Carly with
the Zola voice"*, *"never say game changer"*. Claude offers to save it where it belongs.

There are two levels:

| level | where | for |
|---|---|---|
| this film | `SUBS` and `CAST` in the project's `tools/build.py` | a term or presenter only this film uses |
| you or your team | a **house file** (JSON) | everything you want in every film |

The build looks for the house file in this order: `$SYNTHESIA_HOUSE`, then `house.json` in the project,
then `~/.claude/synthesia-house.json`. Share one across a team by committing it as `house.json` or pointing
`SYNTHESIA_HOUSE` at a shared path. Plugin updates never touch it, so there is no need to fork for any of this.

```json
{
  "subs":  [["kubectl", "cube control"], ["nginx", "engine X", "ˈɛndʒɪn ɛks"]],
  "cast":  {"host":   {"avatar": "<avatar id>", "voice": "<voice id>"},
            "expert": {"avatar": "<avatar id>", "voice": "<voice id>"}},
  "rules": ["Never say 'game changer'."]
}
```

- **`subs`**: `[written, said]` or `[written, said, IPA]`. Spell the alias the way it should sound
  (`"B B J"` for letters, `"engine X"`); add IPA only for names and stress. Matching is whole-word and
  case-sensitive; the film's own `SUBS` win over the house file's. The build turns each into Synthesia's
  `<sub alias="…">` tag, so scripts stay plain prose.
- **`cast`**: roles to avatar and voice IDs. `host` speaks by default; a clip picks another role with
  `who="expert"`. IDs come from Studio (the avatar's ⋯ menu → Copy ID) or Synthesia's
  [avatar](https://docs.synthesia.io/reference/avatars) and [voice](https://docs.synthesia.io/reference/voices)
  tables. Some IDs in those tables are refused by the API, so confirm a new one with a short test render.
- **`rules`**: plain sentences Claude reads before writing any script (words to avoid, how to name products).

A fuller example is in [`examples/software-company-house.json`](examples/software-company-house.json).
Check any new pronunciation by ear: render a short test and listen; the API cannot report how a word sounded.

## What is inside

```
skills/synthesia-video/
  SKILL.md            what Claude knows: the workflow, the API's shape, every gotcha found so far
  reference/          api.md (endpoints, limits, what the API cannot do), verifying.md (ffmpeg recipes)
  scaffold/           the reference film = the project template
    tools/build.py      scene table, cast, pronunciations; words, script, export, upload, render, mux, assemble
    tools/sync.py       cuts, voice, beats: the voice-sync loop
    tools/synthesia.py  a minimal API client (curl)
    tools/export-frames.mjs  deterministic frame export (virtual clock, Playwright)
    cards.css, stage.css, stage.js, r*.html   the look: off-white on black, one SVG stage for animations
    SCENEPLAN.md, CLAUDE.md                   the plan and notes of the reference film
examples/             a worked house file
```

## Costs and safety

- Test renders are free and watermarked (the docs cap them at 30 a day). A **final render spends your video
  minutes**; the skill only does one when you explicitly ask.
- Your API key stays in `.env`, which the scaffold's `.gitignore` excludes. The skill never prints it.
- Test videos are private. The skill never deletes videos unless you ask.

## License

MIT, see [LICENSE](LICENSE).
