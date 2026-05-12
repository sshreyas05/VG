import argparse
import requests
import sys

def main():
    parser = argparse.ArgumentParser(description="Call Modal Flux Kontext Endpoint")
    parser.add_argument("prompt", help="Text prompt to guide the keyframe generation")
    parser.add_argument("image_path", help="Path to the initial image")
    parser.add_argument("--url", required=True, help="Modal web endpoint URL")
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--output", default="output.png", help="Path to save the generated image")

    args = parser.parse_args()

    # Read the file to upload
    try:
        with open(args.image_path, "rb") as f:
            image_data = f.read()
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)

    print(f"Sending request to {args.url} ...")
    
    files = {
        "image_file": (args.image_path, image_data, "image/png")
    }
    data = {
        "prompt": args.prompt,
        "width": args.width,
        "height": args.height,
        "num_inference_steps": 28
    }

    try:
        response = requests.post(args.url, data=data, files=files, timeout=300)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if 'response' in locals() and response is not None:
             print(f"Response text: {response.text}")
        sys.exit(1)

    # Save the resulting image
    with open(args.output, "wb") as f:
        f.write(response.content)
    
    print(f"Successfully generated and saved image to {args.output}")

if __name__ == "__main__":
    main()
