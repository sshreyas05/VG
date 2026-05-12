#!/usr/bin/env python3
"""
RIFE Video Frame Interpolation
================================
Installs dependencies, downloads the pretrained model,
and runs inference on a given video file.

Usage (Colab / local):
    python rife_interpolation.py --video scene_1_clip_1.mp4 --exp 6
"""

import argparse
import os
import subprocess
import sys

# Injecting the local downloaded FFmpeg into PATH for execution
FFMPEG_BIN_PATH = r"c:\Users\tirth\Downloads\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin"
os.environ["PATH"] = FFMPEG_BIN_PATH + os.pathsep + os.environ.get("PATH", "")



# ─────────────────────────────────────────────
# 1. Helpers
# ─────────────────────────────────────────────

def run(cmd: str, check: bool = True) -> None:
    """Run a shell command, streaming output live."""
    print(f"\n>  {cmd}\n{'-'*60}")
    result = subprocess.run(cmd, shell=True, check=check)
    if check and result.returncode != 0:
        sys.exit(result.returncode)


def pip_install(*packages: str) -> None:
    run(f"{sys.executable} -m pip install {' '.join(packages)} -q")


# ─────────────────────────────────────────────
# 2. Install dependencies
# ─────────────────────────────────────────────

def install_dependencies() -> None:
    print("\n[1/4] Installing Python dependencies …")
    pip_install("gdown==4.6.3", "scikit-video", "moviepy==1.0.3")


# ─────────────────────────────────────────────
# 3. Clone repo
# ─────────────────────────────────────────────

REPO_DIR = "arXiv2020-RIFE"
REPO_URL = "https://github.com/hzwer/arXiv2020-RIFE"

def clone_repo() -> None:
    if os.path.isdir(REPO_DIR):
        print(f"\n[2/4] Repo already cloned at ./{REPO_DIR}, skipping.")
    else:
        print("\n[2/4] Cloning RIFE repository …")
        run(f"git clone {REPO_URL}")

    # Patch for skvideo numpy deprecated aliases
    patch_file = os.path.join(REPO_DIR, "inference_video.py")
    if os.path.isfile(patch_file):
        with open(patch_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'np.float = np.float64' not in content:
            patch = "import numpy as np\nnp.float = np.float64\nnp.int = np.int64\nnp.bool = np.bool_\nnp.object = object\n"
            with open(patch_file, 'w', encoding='utf-8') as f:
                f.write(patch + content)


# ─────────────────────────────────────────────
# 4. Download & extract pretrained model
# ─────────────────────────────────────────────

MODEL_DIR  = os.path.join(REPO_DIR, "train_log")
MODEL_ZIP  = os.path.join(MODEL_DIR, "RIFE_trained_model_v3.6.zip")
MODEL_GDID = "1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_"

def download_model() -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.isfile(MODEL_ZIP):
        print(f"\n[3/4] Model archive already present, skipping download.")
    else:
        print("\n[3/4] Downloading pretrained model …")
        run(f"gdown {MODEL_GDID} -O \"{MODEL_ZIP}\"")

    # Extract only if the zip hasn't been extracted yet
    extracted_flag = os.path.join(MODEL_DIR, ".extracted")
    if not os.path.isfile(extracted_flag):
        print("      Extracting model …")
        import zipfile
        with zipfile.ZipFile(MODEL_ZIP, 'r') as zf:
            for member in zf.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue
                source = zf.open(member)
                target = open(os.path.join(MODEL_DIR, filename), "wb")
                with source, target:
                    import shutil
                    shutil.copyfileobj(source, target)
        open(extracted_flag, "w").close()
        print("      Extraction complete.")
    else:
        print("      Model already extracted, skipping.")


# ─────────────────────────────────────────────
# 5. Download sample video (optional helper)
# ─────────────────────────────────────────────

SAMPLE_GDID = "1i3xlKb7ax7Y70khcTcuePi6E7crO_dFc"

def download_sample_video(dest_dir: str = ".") -> str:
    """Download the sample video provided by the RIFE authors."""
    sample_path = os.path.join(dest_dir, "sample_video.mp4")
    if not os.path.isfile(sample_path):
        print("\n   Downloading sample video …")
        run(f"gdown {SAMPLE_GDID} -O \"{sample_path}\"")
    else:
        print(f"\n   Sample video already present at {sample_path}.")
    return sample_path


# ─────────────────────────────────────────────
# 6. Run inference
# ─────────────────────────────────────────────

def run_inference(video_path: str, exp: int) -> None:
    """
    Run RIFE frame interpolation.

    Parameters
    ----------
    video_path : str
        Path to the input video file.
    exp : int
        Exponent for frame interpolation (output frames = input × 2^exp).
    """
    abs_video = os.path.abspath(video_path)

    if not os.path.isfile(abs_video):
        print(f"\n[X] Video not found: {abs_video}")
        print("   Use --sample to download the example video first.")
        sys.exit(1)

    print(f"\n[4/4] Running inference  (exp={exp}, video={abs_video}) …")

    # Change into repo dir so relative imports inside inference_video.py work
    cwd = os.getcwd()
    os.chdir(REPO_DIR)
    try:
        run(f"{sys.executable} inference_video.py --exp={exp} --video=\"{abs_video}\"")
    finally:
        os.chdir(cwd)

    print("\n[V] Interpolation complete!")
    print(f"   Output saved inside ./{REPO_DIR}/  (look for a file ending in _{2**exp}x.mp4)")

# ─────────────────────────────────────────────
# 7. CLI entry-point
# ─────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RIFE video frame interpolation – one-click setup & inference."
    )
    parser.add_argument(
        "--video", "-v",
        type=str,
        default="scene_1_clip_1.mp4",
        help="Path to the input video file (default: scene_1_clip_1.mp4).",
    )
    parser.add_argument(
        "--exp", "-e",
        type=int,
        default=6,
        choices=range(1, 11),
        metavar="[1-10]",
        help="Interpolation exponent. Output = input × 2^exp frames (default: 6).",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Download the RIFE sample video and use it as input.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip pip install step (useful if dependencies are already installed).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 60)
    print("  RIFE Video Frame Interpolation  –  Setup & Inference")
    print("=" * 60)

    if not args.skip_install:
        install_dependencies()

    clone_repo()
    download_model()

    video_path = args.video
    if args.sample:
        video_path = download_sample_video()

    run_inference(video_path, args.exp)


if __name__ == "__main__":
    main()
