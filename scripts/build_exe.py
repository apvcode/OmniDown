"""
PyInstaller build script for OmniDown.
Supports full build and --smoke-test mode.
"""

import os
import sys
import subprocess
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def build(smoke_test: bool = False):
    print("🔨 Starting OmniDown PyInstaller packaging...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=OmniDown",
        "--onefile",
        "--console",
        "--clean",
        "--collect-all=yt_dlp",
        "--collect-all=imageio_ffmpeg",
        "--collect-all=rich",
        "--collect-all=InquirerPy",
        "--collect-all=telebot",
        "--distpath=exe",
        "main.py"
    ]

    if smoke_test:
        print("⚡ Running in --smoke-test mode...")
        cmd.extend(["--log-level=WARN"])

    try:
        subprocess.check_call(cmd)
        exe_path = os.path.join("exe", "OmniDown.exe")
        if os.path.exists(exe_path):
            print(f"\n🎉 Build successful! Output: {os.path.abspath(exe_path)}")
        else:
            print("\n❌ Build finished, check exe/ folder.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with exit code: {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true", help="Run quick build smoke test")
    args = parser.parse_args()
    build(smoke_test=args.smoke_test)
