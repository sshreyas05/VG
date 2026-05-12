import argparse
import requests
import sys
import os

def get_next_output_filename(base_dir="."):
    index = 1
    while True:
        filename = os.path.join(base_dir, f"output{index}.png")
        if not os.path.exists(filename):
            return filename
        index += 1

def main():
    parser = argparse.ArgumentParser(description="Call Modal FLUX.1 Kontext Endpoint")
    parser.add_argument("prompt", help="The text instruction to edit the image (e.g. 'Make the car red')")
    parser.add_argument("image_path", help="Path to the initial image to edit")
    parser.add_argument("--url", required=True, help="Modal web endpoint URL")
    parser.add_argument("--steps", type=int, default=28, help="Number of inference steps (default: 28)")
    parser.add_argument("--width", type=int, default=832, help="Output image width (default: 832)")
    parser.add_argument("--height", type=int, default=480, help="Output image height (default: 480)")
    parser.add_argument("--output", help="Optional output path for the image")

    args = parser.parse_args()

    # Determine auto-incrementing output filename
    # the output is stored inside the folder of the client
    client_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.output:
        out_file = args.output
    else:
        out_file = get_next_output_filename(client_dir)

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
        "num_inference_steps": args.steps,
        "width": args.width,
        "height": args.height
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
    with open(out_file, "wb") as f:
        f.write(response.content)
    
    print(f"Successfully generated and saved image to: {out_file}")

if __name__ == "__main__":
    main()
