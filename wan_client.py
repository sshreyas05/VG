import argparse
import requests
import sys

def main():
    parser = argparse.ArgumentParser(description="Call Modal Wan 2.1 I2V Endpoint")
    parser.add_argument("image_path", help="Path to the initial image to animate")
    parser.add_argument("--prompt", default="", help="Optional text prompt to guide the video generation")
    parser.add_argument("--url", required=True, help="Modal web endpoint URL (e.g. https://your-username--wan2-1-i2v-wani2v-generate.modal.run)")
    parser.add_argument("--out", default="output.mp4", help="Path to save the generated video")
    parser.add_argument("--steps", type=int, default=40, help="Number of inference steps (default: 40)")

    args = parser.parse_args()

    # Read the file to upload
    try:
        with open(args.image_path, "rb") as f:
            image_data = f.read()
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)

    print(f"Sending request to {args.url} ...")
    
    # Multipart form data format required by FastAPI UploadFile and Form
    files = {
        "image_file": (args.image_path, image_data, "image/png")
    }
    data = {
        "prompt": args.prompt,
        "num_inference_steps": args.steps
    }

    try:
        # Since Wan 2.1 video generation takes a while, we heavily increase the timeout
        response = requests.post(args.url, data=data, files=files, timeout=900)
        response.raise_for_status() # Raise an exception for HTTP errors
    except requests.exceptions.Timeout:
        print("Request timed out. Waiting for a video can take several minutes!")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if 'response' in locals() and response is not None:
             print(f"Response text: {response.text}")
        sys.exit(1)

    # Save the resulting video
    with open(args.out, "wb") as f:
        f.write(response.content)
    
    print(f"Successfully generated and saved video to {args.out}")

if __name__ == "__main__":
    main()
