"""
Audio Client - CLI tool to interact with the Modal Cinematic Audio API.

Usage:
    python audio_client.py generate --url <AUDIO_URL> --dialogue "Hello world" --music "piano" --sfx "wind" --duration 5 --dialogue_start 0 --download --output_dir .
"""
import argparse
import requests
import sys
import os
import json


def main():
    parser = argparse.ArgumentParser(description="Cinematic Audio API Client")
    subparsers = parser.add_subparsers(dest="command")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a cinematic audio mix")
    gen_parser.add_argument("--url", required=True, help="Base URL of the Modal audio API")
    gen_parser.add_argument("--dialogue", default=" ", help="Dialogue text for TTS")
    gen_parser.add_argument("--music", default="", help="Music prompt description")
    gen_parser.add_argument("--sfx", default="", help="Sound effect description")
    gen_parser.add_argument("--duration", type=float, default=5.0, help="Total audio duration in seconds")
    gen_parser.add_argument("--dialogue_start", type=float, default=0.0, help="Dialogue start offset in seconds")
    gen_parser.add_argument("--music_volume", type=float, default=0.4, help="Music volume level")
    gen_parser.add_argument("--sfx_volume", type=float, default=1.0, help="SFX volume level")
    gen_parser.add_argument("--dialogue_volume", type=float, default=1.5, help="Dialogue volume level")
    gen_parser.add_argument("--download", action="store_true", help="Auto-download the generated file")
    gen_parser.add_argument("--output_dir", default=".", help="Directory to save downloaded audio")

    args = parser.parse_args()

    if args.command == "generate":
        generate(args)
    else:
        parser.print_help()
        sys.exit(1)


def generate(args):
    url = args.url.rstrip("/")
    generate_url = f"{url}/generate"

    payload = {
        "dialogue": args.dialogue or " ",
        "music": args.music or "",
        "sfx": args.sfx or "",
        "total_duration": args.duration,
        "dialogue_start": args.dialogue_start,
        "music_volume": args.music_volume,
        "sfx_volume": args.sfx_volume,
        "dialogue_volume": args.dialogue_volume,
    }

    print(f"Sending audio generation request to {generate_url} ...")
    print(f"  dialogue: {payload['dialogue'][:60]}...")
    print(f"  music:    {payload['music'][:60]}...")
    print(f"  sfx:      {payload['sfx'][:60]}...")
    print(f"  duration: {payload['total_duration']}s")

    try:
        response = requests.post(generate_url, json=payload, timeout=180)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if 'response' in locals() and response is not None:
            print(f"Response text: {response.text}")
        sys.exit(1)

    data = response.json()
    print(f"Generation result: {json.dumps(data, indent=2)}")

    filename = data.get("filename", "")
    if not filename:
        print("Warning: No filename returned from server.")
        return

    if args.download and filename:
        download_url = f"{url}/download/{filename}"
        print(f"Downloading audio from {download_url} ...")

        try:
            dl_response = requests.get(download_url, timeout=120)
            dl_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {e}")
            sys.exit(1)

        os.makedirs(args.output_dir, exist_ok=True)
        output_path = os.path.join(args.output_dir, filename)
        with open(output_path, "wb") as f:
            f.write(dl_response.content)

        print(f"Saved : .\\{filename}")


if __name__ == "__main__":
    main()
