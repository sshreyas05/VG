import modal
from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse
import os
import subprocess

app = modal.App("rife-interpolation-api")

# Provision environment, fix numpy array deprecated bugs, clone RIFE, and download pretrained models natively!
rife_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "ffmpeg", "libgl1-mesa-glx", "libglib2.0-0", "unzip")
    .pip_install(
        "torch", 
        "torchvision", 
        "numpy==1.23.5", # Critical: old numpy required for scikit-video
        "moviepy==1.0.3", 
        "scikit-video", 
        "gdown==4.6.3", 
        "fastapi", 
        "python-multipart"
    )
    .run_commands(
        "git clone https://github.com/hzwer/arXiv2020-RIFE /rife",
        "mkdir -p /rife/train_log",
        "gdown 1APIzVeI-4ZZCEuIRE1m6WYfSCaOsi_7_ -O /rife/train_log/RIFE_trained_model_v3.6.zip",
        "cd /rife/train_log && unzip RIFE_trained_model_v3.6.zip",
    )
)

@app.function(image=rife_image, gpu="T4", timeout=1200)
@modal.web_endpoint(method="POST")
def interpolate(video_file: UploadFile = File(...), exp: int = Form(2)):
    import shutil
    import uuid
    
    unique_id = uuid.uuid4().hex[:8]
    in_path = f"/tmp/in_{unique_id}.mp4"
    
    # Save the uploaded local file to the cloud ephemeral tmp system
    with open(in_path, "wb") as f:
        shutil.copyfileobj(video_file.file, f)
        
    cwd = "/rife"
    # Run the heavy pytorch video interpolator!
    cmd = ["python", "inference_video.py", f"--exp={exp}", f"--video={in_path}"]
    subprocess.run(cmd, cwd=cwd, check=True)
    
    output_fps = 2**exp
    out_path = in_path.replace(".mp4", f"_{output_fps}x.mp4")
    
    # Ship the hyper-smoothed cinematic video back to the local computer
    return FileResponse(out_path, media_type="video/mp4", filename=f"interpolated_{unique_id}.mp4")
