import io
import os
import modal
from fastapi import Request, UploadFile, Form, File, Response

app = modal.App("wan2-1-i2v")

def download_model():
    # This caches the large Wan 2.1 weights during image build for faster boots
    import os
    import torch
    from diffusers import DiffusionPipeline

    hf_token = os.environ.get("HF_TOKEN")
    print("Downloading Wan 2.1 weights. (This might take a while the first time)...")
    DiffusionPipeline.from_pretrained(
        "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers", 
        torch_dtype=torch.bfloat16,
        token=hf_token
    )

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch",
        "transformers",
        "accelerate",
        "diffusers>=0.33.0",
        "sentencepiece",
        "protobuf",
        "Pillow",
        "fastapi[standard]",
        "python-multipart",
        "imageio",
        "imageio-ffmpeg",
        "hf_transfer",
        "ftfy"
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_model,
        secrets=[modal.Secret.from_name("my-huggingface-secret")],
        timeout=7200
    )
)

# We use an H100 GPU. The 14B model takes ~30GB VRAM, easily fitting in H100
@app.cls(gpu="H100", image=image, timeout=1200, min_containers=0, secrets=[modal.Secret.from_name("my-huggingface-secret")])
class WanI2V:
    @modal.enter()
    def setup(self):
        import os
        import torch
        from diffusers import DiffusionPipeline

        hf_token = os.environ.get("HF_TOKEN")
        print("Loading Wan 2.1 into GPU...")
        self.pipe = DiffusionPipeline.from_pretrained(
            "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers",
            torch_dtype=torch.bfloat16,
            token=hf_token
        ).to("cuda")

    @modal.fastapi_endpoint(method="POST")
    def generate(
        self,
        prompt: str = Form(""),
        image_file: UploadFile = File(...),
        num_inference_steps: int = Form(40) # 40 steps is generally a good balance for Wan 2.1
    ):
        from PIL import Image
        import torch
        from diffusers.utils import export_to_video

        # Read and prepare the uploaded image
        init_image = Image.open(image_file.file).convert("RGB")
        
        # Resize to standard Wan 2.1 480p resolution (max 854x480)
        init_image.thumbnail((854, 480))

        print(f"Generating video with prompt: '{prompt}'")
        
        # Run Wan 2.1 Inference
        output = self.pipe(
            prompt=prompt,
            image=init_image,
            num_inference_steps=num_inference_steps,
            guidance_scale=7.0
        ).frames[0]

        # Export raw frames to H264 MP4 format
        export_to_video(output, "/tmp/temp.mp4", fps=16)
        
        # Return video bytes
        with open("/tmp/temp.mp4", "rb") as f:
            video_bytes = f.read()
            
        return Response(content=video_bytes, media_type="video/mp4")
