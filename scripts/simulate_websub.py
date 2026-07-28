"""Simulate a YouTube WebSub "new video uploaded" push (no real upload needed).

Usage:
  make simulate-websub channel=UCp4CBeq4nzeg9smAvdjPrig video=VIDEO_ID
  make simulate-websub channel=UCp4CBeq4nzeg9smAvdjPrig video=VIDEO_ID mode=discovery_only

  # or:
  PYTHONPATH=. uv run python scripts/simulate_websub.py \\
    --youtube-channel-id UCp4CBeq4nzeg9smAvdjPrig \\
    --video-id dQw4w9WgXcQ \\
    --mode full
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simulate a WebSub new-upload notification"
    )
    parser.add_argument(
        "--youtube-channel-id",
        help="YouTube channel id (UC...)",
    )
    parser.add_argument(
        "--channel-id",
        help="Internal DB channel UUID",
    )
    parser.add_argument(
        "--video-id",
        required=True,
        help="YouTube video id to pretend was just uploaded",
    )
    parser.add_argument(
        "--title",
        default="Simulated new upload (dry run)",
        help="Title for the fake Atom entry",
    )
    parser.add_argument(
        "--mode",
        choices=("full", "discovery_only"),
        default="full",
        help="full = detect+process; discovery_only = detect only",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="API base URL (default local)",
    )
    args = parser.parse_args()

    if not args.youtube_channel_id and not args.channel_id:
        print("ERROR: pass --youtube-channel-id or --channel-id", file=sys.stderr)
        return 1

    payload: dict = {
        "youtube_video_id": args.video_id,
        "title": args.title,
        "mode": args.mode,
    }
    if args.youtube_channel_id:
        payload["youtube_channel_id"] = args.youtube_channel_id
    if args.channel_id:
        payload["channel_id"] = args.channel_id

    url = args.api_base.rstrip("/") + "/api/websub/simulate"
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            print(body)
            data = json.loads(body)
    except HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err}", file=sys.stderr)
        return 1
    except URLError as e:
        print(
            f"Could not reach API at {url}: {e}\n"
            "Is the API running? (make run / docker compose up)",
            file=sys.stderr,
        )
        return 1

    print()
    print("Queued. With worker running, check:")
    print("  - Activity bell → 'Detected' (and 'Ready' if mode=full)")
    print(f"  - Task id: {data.get('task_id')}")
    if args.mode == "full":
        print(
            "  Tip: use a real YouTube video id not already in your DB "
            "so transcript/analysis can succeed."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
