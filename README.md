# synthesia-video

A Claude Code and Codex plugin that makes Synthesia avatar videos **as a build**, not by hand: a scene table in
Python is the source of truth, graphics are HTML pages exported frame by frame, assets are uploaded once,
and every render is a free, watermarked test until you say otherwise.

It grew out of a set of real conference films and carries what they taught: how to sync an animation to a
voice the API will not let you time, how to hand off between two presenters, how to recover wording a
colleague changed in Studio, and a few dozen smaller gotchas of the Synthesia API.

[![Watch the 2-minute intro: the reference film, made with this plugin](docs/intro-video.jpg)](https://share.synthesia.io/dbdc200a-4746-4c32-8656-f0594036400d)

**▶ [Watch the 2-minute intro](https://share.synthesia.io/dbdc200a-4746-4c32-8656-f0594036400d)**: the reference
film (its source is in [Try the reference film](#try-the-reference-film)), built and synced with this plugin.

> **Independent project, provided as is.** Not affiliated with, endorsed by or supported by Synthesia.
> It runs AI-generated actions against a paid third-party API on your account, so read the
> [disclaimer](#disclaimer) before use. You need your own Synthesia account with API access (Creator plan or above).

**Video API, not real-time.** This plugin renders videos through Synthesia's video API. For a real-time,
interactive avatar in a LiveKit voice agent, use Synthesia's own
[`synthesia-interactive-avatar`](https://github.com/synthesia-ai/skills) skill; the two can be installed side by side.

## What it does

Ask Claude or Codex for a Synthesia video and the skill:

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

The repository is a plugin marketplace for both Claude Code and Codex.

### Claude Code

```
claude plugin marketplace add StephanWald/synthesia-video
claude plugin install synthesia-video@stephanwald
```

Inside a session, the same works as `/plugin marketplace add …` and `/plugin install …`. To update:

```
claude plugin marketplace update stephanwald
claude plugin update synthesia-video@stephanwald
```

### Codex

```
codex plugin marketplace add StephanWald/synthesia-video
codex plugin add synthesia-video@stephanwald
```

To update:

```
codex plugin marketplace upgrade stephanwald
codex plugin add synthesia-video@stephanwald
```

Then start a new session in an empty folder and ask for a video ("make a 90-second Synthesia explainer
about …").

### Requirements

- A Synthesia API key (account settings on app.synthesia.io), put in the project's `.env` as
  `SYNTHESIA_API_KEY=…`. It never leaves your machine except to Synthesia's API.
- Python 3 and `curl` (no Python packages), `ffmpeg`, Node.js.
- Playwright in the project (`npm install`) and a browser: Google Chrome, `$CHROME_PATH`, or
  `npx playwright install chromium`.
- Network at export time (the cards load a Google Font).
- Optional: `pdftoppm` for slide decks, Whisper (e.g. `mlx-whisper`) to recover edits made in Studio.

## Try the reference film

The complete source of a working film ships with the plugin:
[`skills/synthesia-video/scaffold/`](skills/synthesia-video/scaffold/). It is a ~2-minute film in seven clips,
each showing one technique and saying which: a presenter on black, a pronunciation table, an animation synced
to the voice, a still diagram, a host handing off to an expert, and a silent end card. The same folder is the
template every new project starts from, and its plan and render log are in
[`SCENEPLAN.md`](skills/synthesia-video/scaffold/SCENEPLAN.md).

To render it yourself (one free test render):

```
cp -R skills/synthesia-video/scaffold my-first-film && cd my-first-film
echo "SYNTHESIA_API_KEY=<your key>" > .env
npm install                      # Playwright, for the frame exporter
python3 tools/build.py all       # export cards and the animation, upload, write the request
python3 tools/build.py render    # free, watermarked test render -> out/film.mp4
python3 tools/sync.py cuts && python3 tools/sync.py voice && python3 tools/sync.py beats
python3 tools/build.py export && python3 tools/build.py mux && python3 tools/build.py assemble
                                 # -> out/assembled.mp4, the animation synced to the voice
```

Or just ask Claude or Codex to "render the synthesia-video reference film" in an empty folder.

## Make it yours: pronunciations, presenters, house rules

The easiest way is to just say it: *"always pronounce kubectl as cube control"*, *"our host is Carly with
the Zola voice"*, *"never say game changer"*. The agent offers to save it where it belongs.

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
- **`rules`**: plain sentences the agent reads before writing any script (words to avoid, how to name products).

A fuller example is in [`examples/software-company-house.json`](examples/software-company-house.json).
Check any new pronunciation by ear: render a short test and listen; the API cannot report how a word sounded.

## What is inside

```
skills/synthesia-video/
  SKILL.md            what the agent knows: the workflow, the API's shape, every gotcha found so far
  reference/          api.md (endpoints, limits, what the API cannot do), verifying.md (ffmpeg recipes),
                      troubleshooting.md (symptom → cause → fix, first-run errors first)
  scaffold/           the reference film = the project template
    tools/build.py      scene table, cast, pronunciations; words, script, export, upload, render, mux, assemble
    tools/sync.py       cuts, voice, beats: the voice-sync loop
    tools/synthesia.py  a minimal API client (curl)
    tools/export-frames.mjs  deterministic frame export (virtual clock, Playwright)
    cards.css, stage.css, stage.js, r*.html   the look: off-white on black, one SVG stage for animations
    SCENEPLAN.md, CLAUDE.md                   the plan and notes of the reference film
examples/             a worked house file (the reference film's code is scaffold/, above)
```

## Costs and safety

- Test renders are free and watermarked (the docs cap them at 30 a day). A **final render spends your video
  minutes**; the skill only does one when you explicitly ask.
- Your API key stays in `.env`, which the scaffold's `.gitignore` excludes. The skill never prints it, and the
  client hands it to `curl` on stdin, so it never appears on a command line or in a process list.
- Test videos are private. The skill never deletes videos unless you ask.
- **What it runs:** the agent runs the project's own scripts (`python3 tools/…`, `node`, `ffmpeg`, `curl`) in the
  project folder, and deletes nothing outside its `out/` folder. There is no telemetry and no other server.
- **What it contacts:** `api.synthesia.io` and `upload.api.synthesia.io` (renders and uploads, with your key),
  the download link Synthesia returns for a finished video, `fonts.googleapis.com` (the cards' font, at
  export), and the npm registry when you run `npm install`.

## Disclaimer

**Provided "as is", without warranty of any kind**, express or implied, including fitness for a particular
purpose. In no event shall the author or contributors be liable for any claim, damages or other liability
arising from the use of this plugin, including costs charged by third parties. The full terms are in the
[MIT license](LICENSE).

- **Not affiliated with Synthesia.** "Synthesia" is a trademark of its owner and is used here only to say
  which service the plugin works with. Synthesia's API, limits and behaviour can change at any time and may
  break what is described here.
- **AI makes mistakes.** The plugin gives instructions to an AI agent (Claude Code or Codex), which writes scripts, runs
  commands and calls the Synthesia API on your behalf. It can misread a request, get a pronunciation, a fact or
  a setting wrong, or run a command you did not intend. Review what it proposes, especially before anything
  that spends money, publishes or deletes.
- **Third-party costs are your responsibility.** Calls to the Synthesia API run on your account, under your
  plan and Synthesia's terms. The plugin is written to use free test renders unless you explicitly ask for a
  final one, but a misconfiguration, a changed default, a mistake by the model or a request you approve can
  still consume video minutes or credits and lead to charges from Synthesia (or any other service you connect).
  Watch your usage and billing.
- **Your content, your responsibility.** You are responsible for what your videos say and show, for the
  rights to any material you use, for consent where a real person's likeness or voice is involved, and for
  following Synthesia's terms of use.
- **Keep your API key safe.** It belongs in the project's `.env` (git-ignored). Never commit it or paste it
  into a chat.

## License

MIT, see [LICENSE](LICENSE).
