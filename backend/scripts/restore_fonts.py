"""
Script to download and restore DejaVu fonts from the official release.

Usage: python backend/scripts/restore_fonts.py

This script downloads the official DejaVu fonts package from GitHub and
extracts the required TTF files into app/services/fonts/.
Since fonts are stored locally in the project, they work in closed/offline networks.
"""
import io
import os
import urllib.request
import zipfile
from pathlib import Path

# Official DejaVu Fonts release from GitHub
RELEASE_URL = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"

# The specific fonts we need (path inside the zip -> filename to save)
REQUIRED_FONTS = {
    "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf": "DejaVuSans.ttf",
    "dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf": "DejaVuSans-Bold.ttf",
    "dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Oblique.ttf": "DejaVuSans-Oblique.ttf",
}


def restore_fonts():
    # Target directory relative to this script
    script_dir = Path(__file__).parent
    target_dir = (script_dir / ".." / "app" / "services" / "fonts").resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Target directory: {target_dir}")
    print(f"Downloading DejaVu fonts package from:\n  {RELEASE_URL}")
    print("(This may take a few seconds...)")

    try:
        with urllib.request.urlopen(RELEASE_URL, timeout=60) as response:
            zip_data = response.read()
        print(f"Downloaded {len(zip_data):,} bytes. Extracting fonts...")
    except Exception as e:
        print(f"ERROR: Failed to download font package: {e}")
        return

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for zip_path, output_name in REQUIRED_FONTS.items():
                try:
                    font_data = zf.read(zip_path)
                    output_path = target_dir / output_name
                    with open(output_path, "wb") as f:
                        f.write(font_data)
                    print(f"  Restored {output_name} ({len(font_data):,} bytes)")
                except KeyError:
                    print(f"  WARNING: '{zip_path}' not found inside the zip.")
    except zipfile.BadZipFile as e:
        print(f"ERROR: Downloaded file is not a valid zip: {e}")
        return

    print("\nDone! All fonts restored successfully.")
    print("The font files are now part of the project and will work in offline/closed networks.")


if __name__ == "__main__":
    restore_fonts()
