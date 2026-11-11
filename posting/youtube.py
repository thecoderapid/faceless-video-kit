#!/usr/bin/env python3
"""Upload to YouTube with the official YouTube Data API (no browser automation, nothing against the rules).

  python posting/youtube.py login                                # once: connect your channel
  python posting/youtube.py upload out/example/final.mp4 --title "Why is the sky blue?" \
         --description-file out/example/description.txt --tags science,sky [--thumbnail thumb.jpg] [--public]

Uploads are UNLISTED by default so you can watch the real upload before switching it to public.
Setup (Google Cloud console, free): create a project -> enable "YouTube Data API v3" -> OAuth consent screen
(External, add yourself as a test user) -> Credentials -> OAuth client ID, type "Desktop app"
-> put client_id and client_secret into config.json -> youtube.
Note: an unverified Google app's uploads may be locked to private until the app passes Google's audit;
check the API's current rules if that happens.
"""
import argparse
import base64
import hashlib
import secrets
import sys
import urllib.parse
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from common import PORT, catch_redirect, load, ok, save  # noqa: E402

AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
REDIRECT = f"http://127.0.0.1:{PORT}/"


def login():
    cfg = load()
    yt = cfg.setdefault("youtube", {})
    if not (yt.get("client_id") and yt.get("client_secret")):
        sys.exit("Put your OAuth client_id and client_secret into config.json -> youtube first.")
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    url = AUTH + "?" + urllib.parse.urlencode({
        "client_id": yt["client_id"], "redirect_uri": REDIRECT, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    back = catch_redirect(url)
    if back.get("state") != state or "code" not in back:
        sys.exit(f"Login failed: {back}")
    tok = ok(requests.post(TOKEN, data={
        "client_id": yt["client_id"], "client_secret": yt["client_secret"], "code": back["code"],
        "redirect_uri": REDIRECT, "grant_type": "authorization_code", "code_verifier": verifier}))
    if "refresh_token" not in tok:
        sys.exit("Google returned no refresh token: remove the app's access in your Google account and log in again.")
    yt["refresh_token"] = tok["refresh_token"]
    save(cfg)
    print("Connected. config.json now holds your YouTube refresh token (keep it private).")


def access_token(yt):
    return ok(requests.post(TOKEN, data={"client_id": yt["client_id"], "client_secret": yt["client_secret"],
                                         "refresh_token": yt["refresh_token"], "grant_type": "refresh_token"}))[
        "access_token"]


def upload(video, title, description="", tags=(), thumbnail=None, privacy="unlisted", category="27"):
    """category 27 = Education, 24 = Entertainment, 22 = People & Blogs."""
    yt = load().get("youtube", {})
    if not yt.get("refresh_token"):
        sys.exit("Not connected: run  python posting/youtube.py login")
    auth = {"Authorization": f"Bearer {access_token(yt)}"}
    blob = Path(video).read_bytes()
    description = description.replace("<", "‹").replace(">", "›")  # YouTube rejects < and > in descriptions
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos",
                      params={"uploadType": "resumable", "part": "snippet,status"},
                      headers={**auth, "X-Upload-Content-Length": str(len(blob)), "X-Upload-Content-Type": "video/*"},
                      json={"snippet": {"title": title[:100], "description": description[:5000], "tags": list(tags),
                                        "categoryId": category},
                            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}})
    ok(r)
    vid = ok(requests.put(r.headers["Location"], headers={**auth, "Content-Type": "video/*"}, data=blob))["id"]
    if thumbnail:  # custom thumbnails need a verified channel; a failure here must not lose the upload
        try:
            ok(requests.post("https://www.googleapis.com/upload/youtube/v3/thumbnails/set", params={"videoId": vid},
                             data=Path(thumbnail).read_bytes(), headers={**auth, "Content-Type": "image/jpeg"}))
        except RuntimeError as e:
            print(f"(thumbnail not set: {e})")
    print(f"uploaded ({privacy}): https://youtu.be/{vid}")
    return vid


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    up = sub.add_parser("upload")
    up.add_argument("video")
    up.add_argument("--title", required=True)
    up.add_argument("--description-file")
    up.add_argument("--tags", default="")
    up.add_argument("--thumbnail")
    up.add_argument("--category", default="27")
    up.add_argument("--public", action="store_true", help="publish immediately instead of unlisted")
    a = ap.parse_args()
    if a.cmd == "login":
        login()
    else:
        desc = Path(a.description_file).read_text(encoding="utf-8") if a.description_file else ""
        upload(a.video, a.title, desc, [t.strip() for t in a.tags.split(",") if t.strip()], a.thumbnail,
               "public" if a.public else "unlisted", a.category)
