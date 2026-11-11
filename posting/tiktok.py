#!/usr/bin/env python3
"""Send a video to TikTok with the official Content Posting API.

  python posting/tiktok.py login                         # once: connect your account
  python posting/tiktok.py upload out/example/final.mp4  # -> lands in your TikTok inbox/drafts

By default the video goes to your TikTok app's inbox: open the app, add a caption (and a trending sound
if you like) and post. Direct posting needs TikTok to audit your app first; until then use the inbox.
Setup (developers.tiktok.com, free): create an app -> add Login Kit (platform Desktop) with the redirect
URI http://127.0.0.1:8765/callback/ and Content Posting API (scope video.upload)
-> put client_key and client_secret into config.json -> tiktok.
"""
import argparse
import hashlib
import secrets
import sys
import urllib.parse
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from common import PORT, catch_redirect, load, ok, save  # noqa: E402

AUTH = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN = "https://open.tiktokapis.com/v2/oauth/token/"
REDIRECT = f"http://127.0.0.1:{PORT}/callback/"
SCOPES = "user.info.basic,video.upload"


def login():
    cfg = load()
    tt = cfg.setdefault("tiktok", {})
    if not (tt.get("client_key") and tt.get("client_secret")):
        sys.exit("Put your app's client_key and client_secret into config.json -> tiktok first.")
    verifier, state = secrets.token_urlsafe(64)[:96], secrets.token_urlsafe(16)
    url = AUTH + "?" + urllib.parse.urlencode({
        "client_key": tt["client_key"], "response_type": "code", "scope": SCOPES, "redirect_uri": REDIRECT,
        "state": state,
        # TikTok's desktop flow wants the HEX sha256 of the verifier (not base64url)
        "code_challenge": hashlib.sha256(verifier.encode()).hexdigest(), "code_challenge_method": "S256"})
    back = catch_redirect(url, "/callback/")
    if back.get("state") != state or "code" not in back:
        sys.exit(f"Login failed: {back}")
    tok = requests.post(TOKEN, data={
        "client_key": tt["client_key"], "client_secret": tt["client_secret"], "code": back["code"],
        "grant_type": "authorization_code", "redirect_uri": REDIRECT, "code_verifier": verifier}).json()
    if "refresh_token" not in tok:
        sys.exit(f"Token exchange failed: {tok}")
    tt["refresh_token"] = tok["refresh_token"]
    save(cfg)
    print("Connected. config.json now holds your TikTok refresh token (keep it private).")


def upload(video):
    cfg = load()
    tt = cfg.get("tiktok", {})
    if not tt.get("refresh_token"):
        sys.exit("Not connected: run  python posting/tiktok.py login")
    tok = ok(requests.post(TOKEN, data={"client_key": tt["client_key"], "client_secret": tt["client_secret"],
                                        "grant_type": "refresh_token", "refresh_token": tt["refresh_token"]}))
    if tok.get("refresh_token") and tok["refresh_token"] != tt["refresh_token"]:
        tt["refresh_token"] = tok["refresh_token"]  # TikTok rotates it on every refresh
        save(cfg)
    blob = Path(video).read_bytes()
    size = len(blob)
    if size > 64_000_000:
        sys.exit(f"{size / 1e6:.0f} MB: this simple uploader sends one chunk (max 64 MB)")
    data = ok(requests.post("https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
                            json={"source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size,
                                                  "total_chunk_count": 1}},
                            headers={"Authorization": f"Bearer {tok['access_token']}",
                                     "Content-Type": "application/json; charset=UTF-8"}))["data"]
    ok(requests.put(data["upload_url"], data=blob,
                    headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"}))
    print("sent to your TikTok inbox: open the app to add a caption and post")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    sub.add_parser("upload").add_argument("video")
    a = ap.parse_args()
    login() if a.cmd == "login" else upload(a.video)
