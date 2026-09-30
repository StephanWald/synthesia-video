# Troubleshooting: symptom → cause → fix

Match the error text or the symptom here before changing code. The first table is what a new machine or
account usually hits on the first run. Everything below was observed with this skill (Sep 2026) unless marked
"docs". A Synthesia bug worth reporting: `reference/api.md`, "Bug reports need the request id".

## First run

| Symptom | Cause | Fix |
|---|---|---|
| `SYNTHESIA_API_KEY not set (env or .env)` | No `.env` in the project root, or the line is misspelt | Ask the user to create `.env` with `SYNTHESIA_API_KEY=…` (account settings on app.synthesia.io). Never ask them to paste it into the chat. |
| `synthesia.py check` fails with 403 `User is not authenticated` (or a 401) | Wrong key, or the plan has no API access | The key belongs to the account, not the workspace; API access needs a Creator plan or above. |
| 400 `Avatar not found` | The ID is in the docs table but refused (two of four Carly rows), or an EXPRESS-2 / personal avatar | Use the default cast or one confirmed by a short test render; render stock and let the user swap theirs in Studio. The 400 names only the **first** bad ID, so check every ID in the request, not just that one. |
| 400 on `scriptLanguage` | `scriptLanguage` sent with `scriptText` | Drop it: it is valid only with `scriptAudio`. The voice sets the language. |
| 400 `FEATURES_AUDIO_UPLOAD_DISABLED` | The plan refuses `scriptAudio` (an uploaded MP3 as the voice) | Keep the TTS voice and sync locally (`sync.py`, `mux`, `assemble`). |
| Exporter: no browser found | Playwright has no browser | Set `$CHROME_PATH`, install Chrome, or `npx playwright install chromium`; `npm install` in the project first. |
| Cards come out in Arial Narrow | No network at export; the Google Font fell back silently | Export with network, then look at one PNG before uploading. |

## The API refuses the request

| Symptom | Cause | Fix |
|---|---|---|
| 400 `horizontalAlign: Not applicable when style: circular` | A circular avatar is fixed to the frame centre | For a presenter beside a picture use `rectangular` + `scale` + `horizontalAlign` (`inset=` in the build). |
| 400 `Unknown field` on `avatarSettings.position` | The avatar has no X/Y | Placement is `horizontalAlign` + `scale` only; exact placement needs Studio or a template. |
| 429 | Creator tier: 60 writes and 60 reads a minute | `synthesia.py` waits for `RateLimit-Reset` and retries; if it still fails, slow the loop down. |
| 5xx on `create` | Server error; the render may or may not exist | Not retried automatically (a retry could start a second render). `synthesia.py videos` first, then create again only if it is not there. |
| Test renders refused after many in a day | Docs: 30 test videos a day | Wait for the next day; batch changes into fewer takes. |
| Any refusal | The take number is spent anyway | That is fine; log it in `SCENEPLAN.md` §8 with the error. |

## The render looks or sounds wrong

| Symptom | Cause | Fix |
|---|---|---|
| The picture starts late; silence before the first word | The script **begins** with a bare `<break>` | Put a "." first: `. <break time="2s"/> …` |
| A silent card runs ~1.5 s longer than its break | A break-only clip renders ~1.5 s over (`5s` ≈ 6.5 s) | Expected; ask for 1.5 s less. |
| ~2 s of silence at every cut | Lead-in plus tail per clip; the API cannot trim it | Budget ~2 s per boundary; merge clips. |
| Film far over the estimate | Air (boundaries, breaks) dominates a short film; rate differs by material (2.8–3.4 words/s) | `build.py words`, cut breaks first, then render and measure. |
| A graphic frozen for long | The speech outran the picture | Re-time the picture to the measured speech (sync loop). |
| Animation off its beats after a re-render | The TTS is not repeatable (beats moved up to 6 s) | Delete `out/voice/`, `out/beats.json`, `out/cuts.json`, `out/scenes/`; run the sync loop again. |
| Animation does not move in the export, or jumps | CSS animation or transitions (they run on real time; the exporter's clock is virtual) | Compute every frame from `t` in JS (`stage.js`). |
| 4:5: avatar off-screen or a sliver with `left` / `right` | Synthesia bug: 4:5 is laid out on a 16:9 canvas | `center` only; a corner presenter via Studio or a template. |
| 4:5: card shifted, edges cut, blurred fill | Same bug: the background lands at −420, +270 | `backgroundSettings: {"position": {"x": 420, "y": -270}}`; check the first test of every 4:5 film. |
| A download shows an avatar, wording or pause nobody requested | The user edited that video's draft in Studio; later downloads return the edited version | Ask before blaming the build; `out/film-takeN.mp4` keeps each take's own file. Copy the edits back (transcribe and diff). |
| A presenter cannot be made visible in Studio | The clip was rendered `voiceOnly` | Re-render it `rectangular`; decide the face at request time. |
| A word is mispronounced | No `<sub>` for it, or a form of it not listed (matching is whole-word, case-sensitive) | Add each written form to `SUBS` or the house file; verify by ear at the timestamp. |
| A fix made in Studio is gone in the next render | The API cannot see Studio edits | Copy the pronunciation or wording back into `SUBS` / the scene table. |
| A flat read | Long blocks, no punctuation | Short paragraphs, "..." or "!" on segues, before any `<break>` or speed change. |
| The voice does not fit the face | The API takes any voice with any avatar | Keep matched pairs in `CAST` (avatar Jaz, voice "Jaz - Breezy"). |
