#!/usr/bin/env python3
"""Minimal Synthesia API client. Reads SYNTHESIA_API_KEY from the environment or .env.

  tools/synthesia.py check                         -> checks the key and API access before anything is built
  tools/synthesia.py upload <file>                 -> prints the asset id (mp4, webm, png, jpg, svg, mp3)
  tools/synthesia.py create <request.json>         -> submits a render, prints the video id
  tools/synthesia.py status <video_id>             -> prints the video record
  tools/synthesia.py wait <video_id> [outfile.mp4] -> polls until done, downloads if an outfile is given
  tools/synthesia.py videos | templates            -> lists what the account can see

Uses curl, so no Python packages are needed (and a Python without a CA bundle still works).
A 429 is retried after its RateLimit-Reset; a 5xx or a failed connection is retried too, except on
POST /v2/videos, where the render may have been created and a retry could start a second one.
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.synthesia.io"
UPLOAD = "https://upload.api.synthesia.io"
TYPES = {".mp4": "video/mp4", ".webm": "video/webm", ".png": "image/png", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".mp3": "audio/mpeg"}


def key():
    k = os.environ.get("SYNTHESIA_API_KEY")
    env = os.path.join(ROOT, ".env")
    if not k and os.path.exists(env):
        for line in open(env):
            if line.strip().startswith("SYNTHESIA_API_KEY="):
                k = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    if not k:
        sys.exit("SYNTHESIA_API_KEY not set (env or .env)")
    return k


def curl(url, method="GET", data=None, file=None, ctype="application/json", retry_5xx=True):
    for attempt in range(4):
        code, body, reset = curl_once(url, method, data, file, ctype)
        transient = code == 429 or (retry_5xx and (code == 0 or code >= 500))
        if not transient or attempt == 3:
            return code, body
        # RateLimit-Reset is seconds until the window resets (an epoch time is tolerated too)
        wait = reset - time.time() if reset > 1e9 else reset
        wait = min(max(wait, 2 ** (attempt + 1)), 65)
        print(f"HTTP {code or 'connection failed'}, retrying in {wait:.0f} s", file=sys.stderr, flush=True)
        time.sleep(wait)


def curl_once(url, method, data, file, ctype):
    # the key goes to curl as a config on stdin, never on the command line, where `ps` would show it
    auth = 'header = "Authorization: %s"\n' % key().replace("\\", "\\\\").replace('"', '\\"')
    # The request id traces the call in Synthesia's logs: quote it in any bug report (curl >= 7.84). Errors carry
    # Request-Id; a successful call only the gateway's x-amzn-requestid.
    cmd = ["curl", "-s", "-K", "-", "-X", method, "-w",
           "\n%{http_code} %header{request-id} %header{x-amzn-requestid} %header{ratelimit-reset}",
           "-H", "Content-Type: " + ctype, url]
    if data is not None:
        cmd += ["--data", json.dumps(data)]
    if file is not None:
        cmd += ["--data-binary", "@" + file]
    out = subprocess.run(cmd, input=auth, capture_output=True, text=True, timeout=600).stdout
    body, _, tail = out.rpartition("\n")
    code, rid, amzn, reset = (tail.split(" ") + ["", "", "", ""])[:4]
    global REQUEST_ID
    REQUEST_ID = next((r for r in (rid, amzn) if r and "%" not in r), "")   # older curl echoes %header{} as is
    reset = float(reset) if reset.replace(".", "", 1).isdigit() else 0
    code = int(code) if code.isdigit() else 0
    try:
        return code, json.loads(body or "{}"), reset
    except json.JSONDecodeError:
        return code, {"raw": body[:1000]}, reset


REQUEST_ID = ""


def fail(code, body, hint=""):
    sys.exit(f"HTTP {code} (request-id {REQUEST_ID or '?'}): {json.dumps(body)[:800]}" + (f"\n{hint}" if hint else ""))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "check":
        code, d = curl(API + "/v2/videos?limit=1")
        if code == 200:
            print("key ok: the API answers with this key")
        elif code in (401, 403):
            fail(code, d, "the key is wrong or has no API access. It comes from account settings on "
                          "app.synthesia.io; API access needs a Creator plan or above.")
        else:
            fail(code, d)
    elif cmd == "upload":
        f = argv[2]
        ext = os.path.splitext(f)[1].lower()
        if ext not in TYPES:
            sys.exit(f"unsupported type {ext}")
        path = "/v2/scriptAudio" if ext == ".mp3" else "/v2/assets"
        code, d = curl(UPLOAD + path, "POST", file=f, ctype=TYPES[ext])
        if code not in (200, 201):
            fail(code, d)
        print(d["id"])
    elif cmd == "create":
        req = json.load(open(argv[2]))
        code, d = curl(API + "/v2/videos", "POST", data=req, retry_5xx=False)
        if code != 201:
            fail(code, d)
        print("request-id", REQUEST_ID or "?", file=sys.stderr)   # stdout stays the bare video id
        print(d["id"])
    elif cmd == "status":
        code, d = curl(API + f"/v2/videos/{argv[2]}")
        print(json.dumps(d, indent=1))
    elif cmd == "wait":
        vid = argv[2]
        while True:
            code, d = curl(API + f"/v2/videos/{vid}")
            st = d.get("status")
            print(time.strftime("%H:%M:%S"), st, flush=True)
            if st != "in_progress":
                break
            time.sleep(30)
        if st != "complete":
            fail(code, d)
        print("duration", d.get("duration"))
        if len(argv) > 3:
            subprocess.run(["curl", "-sL", d["download"], "-o", argv[3]], check=True)
            print("saved", argv[3])
        else:
            print(d["download"])
    elif cmd == "videos":
        code, d = curl(API + "/v2/videos?limit=100")
        for v in d.get("videos", []):
            print(v["id"], v.get("status"), v.get("duration"), v.get("title"))
    elif cmd == "templates":
        code, d = curl(API + "/v2/templates?limit=100")
        for t in d.get("templates", []):
            print(t["id"], t.get("title"), json.dumps(t.get("variables")))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
