# Synthesia API reference (verified 12 Sep 2026)

Base `https://api.synthesia.io`, uploads `https://upload.api.synthesia.io`. Header `Authorization: <api key>`.
Creator plan and above have API access; Creator tier is rate-limited to 60 writes and 60 reads per minute
(429 with `RateLimit-Limit` / `RateLimit-Reset` headers). Spec: `/api/openapi/swagger.json`.

## Endpoints that matter

| Purpose | Call |
|---|---|
| Create video (renders immediately) | `POST /v2/videos` |
| Video status / download | `GET /v2/videos/{id}` → `status` (in_progress, complete, error, rejected), `download`, `duration`, `thumbnail`, `captions.srt/vtt` |
| List videos (rendered only; drafts invisible) | `GET /v2/videos?limit=100&offset=0&source=workspace,shared_with_me,my_videos` |
| Update metadata only | `PATCH /v2/videos/{id}` with `title`, `description`, `visibility`, `ctaSettings` |
| Delete | `DELETE /v2/videos/{id}` |
| Upload image/video asset | `POST upload…/v2/assets`, raw body, `Content-Type` set; returns `{id: "user.<uuid>", title}` |
| Upload voice-over MP3 | `POST upload…/v2/scriptAudio`, `Content-Type: audio/mpeg`; async, poll `GET /v2/assets/{id}` |
| Templates | `GET /v2/templates`, `GET /v2/templates/{id}` → `variables[]` with `type` string, actor, video; `POST /v2/videos/fromTemplate` with `templateId`, `templateData` |
| Webhooks | `POST /v2/webhooks`, `GET /v2/webhooks` |

No endpoint lists avatars or voices; use the docs tables. No endpoint creates a new *version* of a video;
versions come from re-rendering an edited draft in Studio.

## CreateVideoRequest

```json
{
  "test": true,
  "title": "…", "description": "…", "visibility": "private",
  "aspectRatio": "16:9",          // also 9:16, 1:1, 4:5, 5:4
  "callbackId": "free-form tag",
  "input": [ { …clip… } ]
}
```

Clip (`Input`):

| Field | Notes |
|---|---|
| `avatar` (required) | stock ID or custom avatar ID |
| `background` (required) | stock name (`white_studio`, `green_screen`, `off_white`, …) or uploaded asset id or URL |
| `scriptText` | text, SSML allowed. Not with `scriptLanguage`. |
| `scriptAudio` + `scriptLanguage` | uploaded MP3 id; language code required |
| `avatarSettings` | `style`: rectangular / circular / voiceOnly; `voice`: voice UUID; `scale`; `horizontalAlign`: left/center/right; `backgroundColor` (circular); `seamless` |
| `backgroundSettings` | `scale`, `position`, `videoSettings: { trim, volume, shortBackgroundContentMatchMode: freeze|loop|slow_down, longBackgroundContentMatchMode: trim|speed_up|extend_content }` |
| `soundSettings` | `soundtrackVolume` |
| `transition` | none, fade, fadeblack, fadewhite, fadescale, wipe*/slide*/slideover*, jumpcut |

`shortBackgroundContentMatchMode` applies when the picture is shorter than the speech (freeze = hold last
frame); `longBackgroundContentMatchMode` when the picture is longer (extend_content = let it play out).

## What the raw API cannot put on screen (checked 16 Sep 2026)

- A clip's fields are exactly `avatar`, `avatarSettings`, `background`, `backgroundSettings`, `scriptText` |
  `scriptAudio` + `scriptLanguage`, `soundSettings`, `transition`. No text element, shape, layer or overlay: one
  picture per clip is all it does, which is why cards are exported PNGs.
- Native text elements (bold, colour, per-element animation with word-linked triggers) exist only in Studio.
  The API reaches them through **templates**: build the scenes in Studio, mark canvas text and script as
  variables, publish, then `POST /v2/videos/fromTemplate` with `templateData` (plain strings, HTML-escaped,
  case-sensitive names; no formatting inside a variable, so a bold run is its own element). `GET /v2/templates/{id}`
  lists the variables. The account's templates were all stock with no variables (Sep 2026).
- `POST /v2/videos/fromAssistant` (pilot) takes a prompt plus PDFs and lets the Assistant build scenes with
  motion graphics; ~1, 2 or 5 minutes, layout of its choosing. Not used so far.
- The voice is driven by the script alone: `<break>` and `<sub>` are the supported tags; Studio adds speed
  (0.8–1.2×), pronunciation and speech regeneration. On-screen text or bold does not shape the narration.
- `scriptAudio` (own MP3 as the voice) depends on the plan: on the plan this was built with it was refused with
  400 `FEATURES_AUDIO_UPLOAD_DISABLED` (Sep 2026). Where it works, it can carry a frozen voice or a recording.
- EXPRESS-2 avatars (e.g. a personal avatar made in Studio) were refused; EXPRESS-1 and version-3 stock avatars work (Joshua,
  Carly `c43d0b11-…`). Some IDs in the docs' avatar table are refused as `Avatar not found` (Carly `c75b9aaf-…`,
  `595f50a9-…`); the 400 names only the first unknown ID in the request.
- `avatarSettings.style: circular` is fixed to the frame centre; `horizontalAlign` with it is a 400. For
  `rectangular`, `horizontalAlign` + `scale` scale the avatar from a bottom corner (`verticalAlign` is fixed to
  bottom, not exposed), which is how a small presenter stands in the corner of a picture. One avatar per clip;
  a second avatar in the same frame needs Studio or a template.
- The avatar has no X/Y: `avatarSettings.position` is a 400 `Unknown field`. Placement is `horizontalAlign` +
  `scale` only, so exact corner placement is not possible through the API.
- **4:5 is laid out on a 16:9 canvas (a Synthesia bug, verified 27 Sep 2026, reported with request id
  `87678c0f-…`).** The scene is placed on 1920×1080, and that canvas sits in the 1080×1350 frame centred and
  bottom-aligned, offset x −420, y +270, then cropped. So in 4:5:
  - `center` is correct; `left` and `right` at scale 0.36 put the avatar entirely off-screen, `right` 0.6 shows
    a sliver, `right` 1.0 about half the figure. No API setting reaches a corner.
  - A 1080×1350 background at the default position is shifted by −420, +270 (edges cut, the gap filled with a
    blurred extension). **Workaround, verified:** `backgroundSettings: {"position": {"x": 420, "y": -270}}`
    puts it exactly at 0,0. Keep it only while the bug lasts; check the first test render of every 4:5 film.
  - A presenter in a corner of a 4:5 frame: move the avatar in Studio on the draft the API creates, or build a
    4:5 template in Studio with the avatar placed and render it with `POST /v2/videos/fromTemplate`. Both stay
    native Synthesia renders.
  - 9:16, 1:1 and 5:4 are untested; expect the same and check the first render.
- A `voiceOnly` clip stays voice-only: Studio shows an avatar box, but moving it does not make the presenter
  appear. If a clip may need the face, render it `rectangular` from the start.
- **Bug reports need the request id.** Error responses carry `Request-Id`; successful ones only the gateway's
  `x-amzn-requestid`. `tools/synthesia.py` reads either, prints it with every error, and prints it on stderr
  for `create`. Report the endpoint, payload, status and body, the request id, and expected vs actual.

## Limits not documented

Asset size and duration limits, resolution of the output, and the per-clip silence padding are not in
the spec. Observed: 1920×1080 MP4 at 30 fps uploads and renders fine; a 47 s film rendered in ~3 min,
a 100 s film in ~4 min.
