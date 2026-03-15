#!/usr/bin/env python3
"""Script to easily switch between different video sources."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def update_env_file(source: str, source_type: str, livekit_url: str = "", livekit_token: str = "") -> None:
    """Update the .env file with the new video source configuration."""
    env_path = Path(".env")
    if not env_path.exists():
        print("Error: .env file not found")
        return

    content = env_path.read_text()

    # Update VIDEO_SOURCE
    if "VIDEO_SOURCE=" in content:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("VIDEO_SOURCE="):
                lines[i] = f"VIDEO_SOURCE={source}"
                break
        content = "\n".join(lines)
    else:
        content += f"\nVIDEO_SOURCE={source}"

    # Update VIDEO_SOURCE_TYPE
    if "VIDEO_SOURCE_TYPE=" in content:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("VIDEO_SOURCE_TYPE="):
                lines[i] = f"VIDEO_SOURCE_TYPE={source_type}"
                break
        content = "\n".join(lines)
    else:
        content += f"\nVIDEO_SOURCE_TYPE={source_type}"

    # Update LiveKit settings if provided
    if livekit_url:
        if "LIVEKIT_URL=" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("LIVEKIT_URL="):
                    lines[i] = f"LIVEKIT_URL={livekit_url}"
                    break
            content = "\n".join(lines)
        else:
            content += f"\nLIVEKIT_URL={livekit_url}"

    if livekit_token:
        if "LIVEKIT_TOKEN=" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("LIVEKIT_TOKEN="):
                    lines[i] = f"LIVEKIT_TOKEN={livekit_token}"
                    break
            content = "\n".join(lines)
        else:
            content += f"\nLIVEKIT_TOKEN={livekit_token}"

    env_path.write_text(content)
    print(f"Updated .env file to use {source_type} source: {source}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Switch video source configuration")
    parser.add_argument(
        "source_type",
        choices=["file", "webcam", "rtsp", "livekit"],
        help="Type of video source"
    )
    parser.add_argument(
        "source",
        help="Video source value (file path, camera index, RTSP URL, or LiveKit URL)"
    )
    parser.add_argument(
        "--livekit-token",
        help="LiveKit token (required for livekit source)"
    )

    args = parser.parse_args()

    if args.source_type == "livekit":
        if not args.livekit_token:
            print("Error: --livekit-token is required for livekit source")
            return
        update_env_file(args.source, args.source_type, livekit_url=args.source, livekit_token=args.livekit_token)
    else:
        update_env_file(args.source, args.source_type)


if __name__ == "__main__":
    main()