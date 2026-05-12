import io
import os
import modal
from fastapi import Request, UploadFile, Form, File, Response

app = modal.App("flux-kontext")

def download_model():
    # This step caches the 12B model weights into the Modal image during the build
    import os
    import torch
    from diffusers import DiffusionPipeline

    hf_token = os.environ.get("HF_TOKEN")
    print("Downloading FLUX.1-Kontext-dev weights...")
    DiffusionPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-Kontext-dev", 
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
        "hf_transfer"
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_model,
        secrets=[modal.Secret.from_name("my-huggingface-secret")],
        timeout=7200
    )
)

@app.cls(gpu="H100", image=image, timeout=600, min_containers=0, secrets=[modal.Secret.from_name("my-huggingface-secret")])
class FluxKontext:
    @modal.enter()
    def setup(self):
        # This step runs once when the container boots up
        import os
        import torch
        from diffusers import DiffusionPipeline

        hf_token = os.environ.get("HF_TOKEN")
        print("Loading FLUX.1-Kontext-dev into GPU...")
        self.pipe = DiffusionPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-Kontext-dev",
            torch_dtype=torch.bfloat16,
            token=hf_token
        ).to("cuda")

    @modal.fastapi_endpoint(method="POST")
    def generate(
        self,
        prompt: str = Form(...),
        image_file: UploadFile = File(...),
        num_inference_steps: int = Form(28), # FLUX "dev" foundation usually requires ~28 steps
        width: int = Form(832),
        height: int = Form(480)
    ):
        from PIL import Image
        import torch

        # Read the uploaded image
        init_image = Image.open(image_file.file).convert("RGB")
        
        # Resize to exact dimensions required
        init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)

        print(f"Generating image edit with instruction: '{prompt}' at {width}x{height}")
        
        # Run inference using FLUX Kontext
        result_image = self.pipe(
            prompt=prompt,
            image=init_image,
            height=height,
            width=width,
            num_inference_steps=num_inference_steps,
            guidance_scale=4.0 # Standard for Flux DEV
        ).images[0]

        # Convert back to PNG bytes
        out_io = io.BytesIO()
        result_image.save(out_io, format="PNG")
        out_io.seek(0)
        return Response(content=out_io.getvalue(), media_type="image/png")
