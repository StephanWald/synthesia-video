#!/usr/bin/env python3
"""Minimal Synthesia API client. Reads SYNTHESIA_API_KEY from the environment or .env.

  tools/synthesia.py upload <file>                 -> prints the asset id (mp4, webm, png, jpg, svg, mp3)
  tools/synthesia.py create <request.json>         -> submits a render, prints the video id
  tools/synthesia.py status <video_id>             -> prints the video record
  tools/synthesia.py wait <video_id> [outfile.mp4] -> polls until done, downloads if an outfile is given
  tools/synthesia.py videos | templates            -> lists what the account can see

Uses curl, so no Python packages are needed (and a Python without a CA bundle still works).
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


def curl(url, method="GET", data=None, file=None, ctype="application/json"):
    # the key goes to curl as a config on stdin, never on the command line, where `ps` would show it
    auth = 'header = "Authorization: %s"\n' % key().replace("\\", "\\\\").replace('"', '\\"')
    cmd = ["curl", "-s", "-K", "-", "-X", method, "-w", "\n%{http_code}",
           "-H", "Content-Type: " + ctype, url]
    if data is not None:
        cmd += ["--data", json.dumps(data)]
    if file is not None:
        cmd += ["--data-binary", "@" + file]
    out = subprocess.run(cmd, input=auth, capture_output=True, text=True, timeout=600).stdout
    body, _, code = out.rpartition("\n")
    try:
        return int(code), json.loads(body or "{}")
    except json.JSONDecodeError:
        return int(code), {"raw": body[:1000]}


def fail(code, body):
    sys.exit(f"HTTP {code}: {json.dumps(body)[:800]}")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "upload":
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
        code, d = curl(API + "/v2/videos", "POST", data=req)
        if code != 201:
            fail(code, d)
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
