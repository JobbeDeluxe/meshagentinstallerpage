#!/usr/bin/env python3
"""Create a MeshCentral installer code from the command line."""

from __future__ import annotations

import sys

from app import generate_code, is_valid_download_url, load_codes, save_codes


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python gen_code.py "Mamas Laptop" "https://mesh.example.de/meshagents?..."')
        return 1

    name = sys.argv[1].strip()
    download_url = sys.argv[2].strip()

    if not name:
        print("Name is required.")
        return 1
    if not is_valid_download_url(download_url):
        print("Download URL must start with http:// or https://.")
        return 1

    codes = load_codes()
    code = generate_code(codes)
    codes[code] = {"name": name, "download_url": download_url}
    save_codes(codes)

    print("")
    print("Code erstellt")
    print(f"Name: {name}")
    print(f"Code: {code}")
    print("")
    print("Diesen Code an die Person schicken und auf der Webseite eingeben lassen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
