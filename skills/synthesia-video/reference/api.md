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
- **Outside 16:9, `left` and `right` misplace the avatar** (reported Sep 2026, 4:5): at scale 0.36, `right` put
  Carly at x ≈ 1076 of a 1080-wide frame, width 374, almost entirely off-screen; `left` was off-screen the other
  way; `center` worked. Use `center` in other aspect ratios, or place the presenter in Studio.
- A `voiceOnly` clip stays voice-only: Studio shows an avatar box, but moving it does not make the presenter
  appear. If a clip may need the face, render it `rectangular` from the start.
- **4:5 background offset, one observation, to confirm:** a 1080×1350 uploaded card at `backgroundSettings.position`
  0,0 appeared in Studio at X −420, Y 270; position X 420, Y −270 put it at X 0, Y 0, 1080×1350. One take in that
  session had been resized in Studio, so check on an untouched API take before relying on the correction.

## Limits not documented

Asset size and duration limits, resolution of the output, and the per-clip silence padding are not in
the spec. Observed: 1920×1080 MP4 at 30 fps uploads and renders fine; a 47 s film rendered in ~3 min,
a 100 s film in ~4 min.
