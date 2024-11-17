
from pathlib import Path

import os
import sys
import subprocess
import zipfile
import urllib.request

WORKAREA = Path(__file__).resolve().parent
TWEEGO = "tweego"

# Check if Tweego is in the system's PATH
def is_tweego_in_path():
	try:
		subprocess.run([TWEEGO, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
		return True
	except FileNotFoundError:
		return False

# Determine processor architecture
def get_architecture():
	arch = os.environ.get("PROCESSOR_ARCHITECTURE", "").lower()
	if arch == "x86":
		return "x86"
	elif arch == "amd64":
		return "x64"
	else:
		sys.exit(f"No pre-built Tweego is available for CPU family {arch}. "
				"Please build Tweego from source and add it to your PATH.")

def download_file(url, dest):
	print(f"Downloading from {url} to {dest}...")
	urllib.request.urlretrieve(url, dest)

def extract_zip(src, dest):
	print(f"Unpacking {src} to {dest}...")
	with zipfile.ZipFile(src, 'r') as zip_ref:
		zip_ref.extractall(dest)

if not is_tweego_in_path():
	TWEEGO_VERSION = "2.1.1"
	TWEEGO_OS = "windows"
	TWEEGO_ARCH = get_architecture()

	print(f"TWEEGO_VERSION: {TWEEGO_VERSION}")
	print(f"TWEEGO_OS: {TWEEGO_OS}")
	print(f"TWEEGO_ARCH: {TWEEGO_ARCH}")

	TWEEGO_ARCHIVE = f"tweego-{TWEEGO_VERSION}-{TWEEGO_OS}-{TWEEGO_ARCH}.zip"
	tweego_archive_path = WORKAREA / "tools" / TWEEGO_ARCHIVE

	if not tweego_archive_path.exists():
		download_url = f"https://github.com/tmedwards/tweego/releases/download/v{TWEEGO_VERSION}/{TWEEGO_ARCHIVE}"
		download_file(download_url, tweego_archive_path)

		extract_zip(tweego_archive_path, WORKAREA / "tools")

	TWEEGO = WORKAREA / "tools" / "tweego.exe"
	print(f"Using downloaded Tweego: {TWEEGO}")
else:
	print(f"Using systemwide Tweego: {TWEEGO}")

SUGARCUBE_VERSION = "2.37.0"
SUGARCUBE_ARCHIVE = f"sugarcube-{SUGARCUBE_VERSION}-for-twine-2.1-local.zip"
sugarcube_archive_path = WORKAREA / "storyformats" / SUGARCUBE_ARCHIVE

if not sugarcube_archive_path.exists():
	sugarcube_url = f"https://github.com/tmedwards/sugarcube-2/releases/download/v{SUGARCUBE_VERSION}/{SUGARCUBE_ARCHIVE}"
	download_file(sugarcube_url, sugarcube_archive_path)

	extract_zip(sugarcube_archive_path, WORKAREA / "storyformats")

OUTPUT = "AbyssDiver.html"
print(f"Compiling to: {OUTPUT}")
TWEEGO_PATH = WORKAREA / "storyformats"
src_dir = WORKAREA / "src"
dependencies_dir = WORKAREA / "dependencies"

additional_args = sys.argv[1:]

command = [
	str(TWEEGO),
	str(src_dir),
	str(dependencies_dir),
	"-o", OUTPUT
] + additional_args

subprocess.run(command, check=True)