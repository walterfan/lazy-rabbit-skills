#!/usr/bin/env python3
"""Upload an asciinema cast file to cast-player."""

import json
import os
import sys
import urllib.request

# Base URL of your asciinema-style cast-player service.
# Override with the CAST_PLAYER_URL environment variable.
CAST_PLAYER_URL = os.getenv("CAST_PLAYER_URL", "https://cast-player.example.com")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: upload_cast.py <cast-file> [title]", file=sys.stderr)
        return 2

    cast_file = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else "agents-md-generate demo"

    with open(cast_file, encoding="utf-8") as f:
        cast_content = f.read()

    base_url = CAST_PLAYER_URL.rstrip("/")
    body = json.dumps({"title": title, "cast": cast_content}).encode()
    request = urllib.request.Request(
        f"{base_url}/api/cast",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    response = json.loads(urllib.request.urlopen(request, timeout=30).read())
    print(f"{base_url}{response['playUrl']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
