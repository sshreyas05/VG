import asyncio
import base64
import subprocess
from pathlib import Path
from typing import List, Optional

import modal

# --- Configuration ---
MODEL_DIR = "/ollama_models"
MODELS_TO_DOWNLOAD = ["gemma4:31b"]
MODELS_TO_TEST = ["gemma4:31b"]

OLLAMA_VERSION = "v0.20.0-rc1"
OLLAMA_PORT = 11434



# --- Container Image ---
ollama_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("curl", "ca-certificates", "ffmpeg", "zstd")
    .uv_pip_install(
        "fastapi==0.115.8",
        "uvicorn[standard]==0.34.0",
        "openai~=1.30",
        "opencv-python-headless",
        "Pillow",
    )
    .run_commands(
        "echo 'Installing Ollama (latest)...'",
        "curl -fsSL https://ollama.com/install.sh | sh",  # no version pin = always latest
        "echo 'Ollama installed.'",
        f"mkdir -p {MODEL_DIR}",
    )
    .env(
        {
            "OLLAMA_HOST": f"0.0.0.0:{OLLAMA_PORT}",
            "OLLAMA_MODELS": MODEL_DIR,
        }
    )
)

app = modal.App("ollama-creative-director", image=ollama_image)

model_volume = modal.Volume.from_name("ollama-models-store", create_if_missing=True)


# --- Helper: encode image to base64 ---
def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# --- Helper: extract frames from video locally before sending ---
def extract_video_frames(video_path: str, num_frames: int = 4) -> List[str]:
    """Extract evenly spaced frames from a video, return as base64 strings."""
    try:
        import cv2
    except ImportError:
        print("opencv not available locally — install with: pip install opencv-python")
        return []

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0

    print(f"Video: {total_frames} frames, {fps:.1f} fps, {duration:.1f}s duration")

    indices = [int(total_frames * i / (num_frames - 1)) for i in range(num_frames)]
    indices[-1] = min(indices[-1], total_frames - 1)

    frames_b64 = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            import cv2 as cv
            _, buffer = cv.imencode(".jpg", frame)
            frames_b64.append(base64.b64encode(buffer).decode("utf-8"))

    cap.release()
    print(f"Extracted {len(frames_b64)} frames from video.")
    return frames_b64


@app.cls(
    gpu="H100",
    volumes={MODEL_DIR: model_volume},
    timeout=60 * 15,  # 15 min for large model cold starts
)
class OllamaServer:
    ollama_process: subprocess.Popen | None = None

    @modal.enter()
    async def start_ollama(self):
        """Starts the Ollama server and ensures required models are downloaded."""
        print("Starting Ollama setup...")

        self.ollama_process = subprocess.Popen(["ollama", "serve"])
        print(f"Ollama server started with PID: {self.ollama_process.pid}")

        await asyncio.sleep(10)
        print("Ollama server should be ready.")

        loop = asyncio.get_running_loop()
        models_pulled = False

        ollama_list_proc = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True
        )

        if ollama_list_proc.returncode != 0:
            raise RuntimeError(f"Failed to list Ollama models: {ollama_list_proc.stderr}")

        current_models_output = ollama_list_proc.stdout
        print("Current models detected:", current_models_output)

        for model_name in MODELS_TO_DOWNLOAD:
            model_tag = model_name if ":" in model_name else f"{model_name}:latest"
            if model_tag not in current_models_output:
                print(f"Pulling model '{model_name}'...")
                models_pulled = True
                pull_process = await asyncio.create_subprocess_exec("ollama", "pull", model_name)
                retcode = await pull_process.wait()
                if retcode != 0:
                    print(f"Error pulling model '{model_name}': exit code {retcode}")
                else:
                    raise RuntimeError(f"Failed to pull model '{model_name}': exit code {retcode}")
            else:
                print(f"Model '{model_name}' pulled successfully.")
                models_pulled = True

        # Commit volume ONCE after all pulls (outside the loop)
        if models_pulled:
            print("Committing model volume...")
            await loop.run_in_executor(None, model_volume.commit)
            print("Volume commit finished.")

        print("Ollama setup complete.")

    @modal.exit()
    def stop_ollama(self):
        print("Shutting down Ollama server...")
        if self.ollama_process and self.ollama_process.poll() is None:
            try:
                self.ollama_process.terminate()
                self.ollama_process.wait(timeout=10)
                print("Ollama server terminated.")
            except subprocess.TimeoutExpired:
                self.ollama_process.kill()
                self.ollama_process.wait()
            except Exception as e:
                print(f"Error shutting down Ollama server: {e}")
        print("Shutdown complete.")

    @modal.web_server(port=OLLAMA_PORT, startup_timeout=180)
    def serve(self):
        print(f"Serving Ollama API on port {OLLAMA_PORT}")

    @modal.method()
    async def generate(
        self,
        text: Optional[str] = None,
        image_b64_list: Optional[List[str]] = None,  # list of base64 encoded images
        video_frames_b64: Optional[List[str]] = None,  # extracted frames as base64
        model: str = "gemma4:31b",
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a creative prompt from any combination of text, images, and/or video frames.
        All inputs are optional — passing None for any of them is safe.
        """
        import openai

        client = openai.AsyncOpenAI(
            base_url=f"http://localhost:{OLLAMA_PORT}/v1",
            api_key="not-needed",
        )

        # Build the user message content block
        content = []

        # Add text if provided
        if text:
            content.append({"type": "text", "text": text})

        # Add images if provided
        if image_b64_list:
            for i, img_b64 in enumerate(image_b64_list):
                if img_b64:  # skip None/empty entries
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    })
                    print(f"Added image {i+1} to message.")

        # Add video frames if provided (sent as sequential images with context label)
        if video_frames_b64:
            content.append({
                "type": "text",
                "text": f"The following {len(video_frames_b64)} images are evenly spaced frames extracted from a video clip, in chronological order. Analyze motion, composition, color, and mood across the sequence.",
            })
            for i, frame_b64 in enumerate(video_frames_b64):
                if frame_b64:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"},
                    })
                    print(f"Added video frame {i+1}/{len(video_frames_b64)} to message.")

        # Fallback if nothing was passed
        if not content:
            content.append({
                "type": "text",
                "text": "Generate a detailed cinematic keyframe image prompt.",
            })

        curr_system_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT

        messages = [
            {"role": "system", "content": curr_system_prompt},
            {"role": "user", "content": content},
        ]

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during generation: {e}"


# --- Local entrypoint ---
@app.local_entrypoint()
async def local_main(
    text: str = "",
    image: str = "",   # path to a single image file
    video: str = "",   # path to a video file
):
    """
    Run the creative director with any combination of inputs.

    Examples:
      modal run ollama.py --text "generate a transition prompt for a rainy city scene"
      modal run ollama.py --image /path/to/frame.jpg --text "generate a keyframe prompt"
      modal run ollama.py --video /path/to/clip.mp4
      modal run ollama.py --video /path/to/clip.mp4 --text "suggest music for this scene"
      modal run ollama.py  # runs with no input — defaults to keyframe prompt
    """

    # --- Safely handle inputs (None or empty string both treated as absent) ---
    text_input: Optional[str] = text.strip() if text and text.strip() else None

    image_b64_list: Optional[List[str]] = None
    if image and image.strip():
        image_path = Path(image.strip())
        if image_path.exists():
            print(f"Loading image: {image_path}")
            image_b64_list = [encode_image_to_base64(str(image_path))]
        else:
            print(f"Warning: image file not found at '{image_path}', skipping.")

    video_frames_b64: Optional[List[str]] = None
    if video and video.strip():
        video_path = Path(video.strip())
        if video_path.exists():
            print(f"Extracting frames from video: {video_path}")
            video_frames_b64 = extract_video_frames(str(video_path), num_frames=4)
            if not video_frames_b64:
                print("Warning: no frames extracted from video, skipping.")
                video_frames_b64 = None
        else:
            print(f"Warning: video file not found at '{video_path}', skipping.")

    print("\nSending to OllamaServer...")
    result = await OllamaServer().generate.remote.aio(
        text=text_input,
        image_b64_list=image_b64_list,
        video_frames_b64=video_frames_b64,
    )

    print("\n" + "=" * 60)
    print("CREATIVE DIRECTOR OUTPUT:")
    print("=" * 60)
    print(result)
    print("=" * 60)