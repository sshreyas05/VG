import os
import json
import subprocess
import glob
import cv2
import re
import uuid
import time

# Configuration
FLUX_URL = "https://satyamashtikar--flux-kontext-fluxkontext-generate.modal.run"
WAN_URL = "https://satyamashtikar--wan2-1-i2v-wani2v-generate.modal.run"
AUDIO_URL = "https://satyamashtikar--cinematic-audio-api-serve.modal.run"
from gemma_video_pipeline import generate_video_json, ask_gemma

script_dir = os.path.dirname(os.path.abspath(__file__))
START_NOISE_IMG = os.path.normpath(os.path.join(script_dir, "WhatsApp Image 2026-04-05 at 22.46.57.jpeg"))

# Inject FFmpeg Path
import imageio_ffmpeg
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def extract_last_frame(video_path, output_image_path):
    print(f"Extracting last frame from {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Failed to open video {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 1))
    ret, frame = cap.read()
    if not ret:
        print("Warning: Could not read the last frame, trying previous frame.")
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 2))
        ret, frame = cap.read()
        if not ret:
             raise Exception(f"Failed to extract frame from video {video_path}")
             
    cv2.imwrite(output_image_path, frame)
    cap.release()
    print(f"Saved last frame to {output_image_path}")
    return output_image_path

def generate_pseudo_keyframe_prompt(prev_desc, next_keyframe_prompt):
    prompt = f"""
You are a cinematic prompt engineer.
We are transitioning between two scenes.
The END of the previous scene was described as: {prev_desc}
The TARGET keyframe for the next scene is: {next_keyframe_prompt}
TASK: Write a single paragraph visual prompt representing a "pseudo-keyframe" exactly halfway between these two moments.
"""
    return ask_gemma(system_prompt=prompt)

def merge_audio_video(video_path, audio_path, output_path):
    """Merge visual clip with audio using FFmpeg."""
    if not os.path.exists(video_path) or not os.path.exists(audio_path):
        print(f"Skipping merge: Missing {video_path} or {audio_path}")
        return video_path # Fallback to silent video if best-effort
        
    print(f"Merging {video_path} and {audio_path} -> {output_path}")
    cmd = [
        FFMPEG_EXE, "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", "-y", output_path
    ]
    subprocess.run(cmd, check=False)
    return output_path if os.path.exists(output_path) else video_path

def concatenate_clips(clip_paths, final_out):
    """Concatenate multiple video clips into one."""
    print(f"Stitching {len(clip_paths)} clips into {final_out}...")
    list_file = "concat_list.txt"
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
            
    cmd = [FFMPEG_EXE, "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", "-y", final_out]
    subprocess.run(cmd, check=True)
    if os.path.exists(list_file):
        os.remove(list_file)
    return final_out

def run_rife(input_video, exp=6):
    """Run RIFE interpolation on the final video."""
    print(f"\n--- PHASE 3: RIFE INTERPOLATION (exp={exp}) ---")
    repo_dir = "arXiv2020-RIFE"
    if not os.path.isdir(repo_dir):
        print("RIFE repo not found! Skipping interpolation.")
        return input_video
        
    abs_video = os.path.abspath(input_video)
    cwd = os.getcwd()
    os.chdir(repo_dir)
    try:
        # Interpolated output name logic usually ends in _Nx.mp4
        cmd = ["python", "inference_video.py", f"--exp={exp}", f"--video={abs_video}"]
        subprocess.run(cmd, check=True)
    finally:
        os.chdir(cwd)
        
    # Standard RIFE output naming
    output_fps = 2**exp
    rife_out = abs_video.replace(".mp4", f"_{output_fps}x.mp4")
    return rife_out if os.path.exists(rife_out) else input_video

def run_e2e_pipeline(story, duration, on_progress=None):
    unique_run_id = str(uuid.uuid4())[:8]
    print(f"\n--- STARTING PIPELINE [ID: {unique_run_id}] ---")
    
    if on_progress: on_progress("Generating video structure...", 5)
    # 1. Generate JSON Structure
    while True:
        scenes_data = generate_video_json(story, duration)
        
        # If running from terminal, allow the user to review and regenerate
        if on_progress is None:
            print("\n" + "="*60)
            print(" GENERATED VIDEO SCRIPT & ENHANCED PROMPTS ")
            print("="*60)
            print(json.dumps(scenes_data, indent=2))
            print("="*60)
            
            choice = input("\nProceed with this script? [y/N/regenerate]: ").strip().lower()
            if choice == 'regenerate' or choice == 'r':
                print("Regenerating script...\n")
                continue
            elif choice != 'y':
                print("Aborting pipeline.")
                return None
        break

    
    # 2. Rendering Loop
    all_final_clips = []
    
    current_input_img = START_NOISE_IMG
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flux_client_path = os.path.normpath(os.path.join(script_dir, "flux_client.py"))
    wan_client_path = os.path.normpath(os.path.join(script_dir, "wan_client.py"))
    audio_client_path = os.path.normpath(os.path.join(script_dir, "audio_client.py"))
    
    for scene_idx, scene in enumerate(scenes_data):
        print(f"\n SCENE {scene['scene']}")
        if on_progress: on_progress(f"Processing Scene {scene['scene']}...", 10 + scene_idx * 10)
        target_keyframe_prompt = scene["keyframe_prompt"]
        
        if scene_idx > 0:
            print("Bridging scenes with Pseudo-Keyframe...")
            pseudo_prompt = generate_pseudo_keyframe_prompt(scenes_data[scene_idx-1]["description"], target_keyframe_prompt)
            pseudo_img_out = f"run_{unique_run_id}_s{scene['scene']}_pseudo.png"
            subprocess.run(["python", flux_client_path, pseudo_prompt, current_input_img, "--url", FLUX_URL, "--width", "832", "--height", "480", "--output", pseudo_img_out], check=True)
            current_input_img = pseudo_img_out
            
        scene_start_img_out = f"run_{unique_run_id}_s{scene['scene']}_start.png"
        subprocess.run(["python", flux_client_path, target_keyframe_prompt, current_input_img, "--url", FLUX_URL, "--width", "832", "--height", "480", "--output", scene_start_img_out], check=True)
        current_input_img = scene_start_img_out
        
        for clip in scene["clips"]:
            clip_idx = clip["clip"]
            vid_out = f"run_{unique_run_id}_s{scene['scene']}_c{clip_idx}.mp4"
            subprocess.run(["python", wan_client_path, current_input_img, "--prompt", clip.get("transition_prompt", ""), "--url", WAN_URL, "--out", vid_out], check=True)
            
            # Extract frame for next clip
            next_frame = f"run_{unique_run_id}_s{scene['scene']}_c{clip_idx}_last.png"
            current_input_img = extract_last_frame(vid_out, next_frame)
            
            # Audio
            print(f"Generating audio for clip {clip_idx}...")
            cmd_audio = [
                "python", audio_client_path, "generate", "--url", AUDIO_URL,
                "--dialogue", clip.get("dialogue", " "), "--music", clip.get("music", ""),
                "--sfx", clip.get("sound_effect", ""), "--duration", str(clip.get("duration", 5.0)),
                "--dialogue_start", str(clip.get("dialogue_start", 0.0)),
                "--download", "--output_dir", "."
            ]
            audio_proc = subprocess.run(cmd_audio, capture_output=True, text=True)
            
            # Best-effort audio filename extraction
            audio_file = None
            match = re.search(r"Saved\s+:\s+\.\\([^\s]+\.wav)", audio_proc.stdout)
            if match:
                audio_file = match.group(1).strip()
            
            # Merge
            merged_out = f"run_{unique_run_id}_s{scene['scene']}_c{clip_idx}_final.mp4"
            final_clip = merge_audio_video(vid_out, audio_file if audio_file else "None", merged_out)
            all_final_clips.append(final_clip)

    # 3. Final Assembly
    if all_final_clips:
        composite_out = f"movie_raw_{unique_run_id}.mp4"
        concatenate_clips(all_final_clips, composite_out)
        
        # 4. RIFE
        if on_progress: on_progress("Interpolating final video...", 90)
        final_movie = run_rife(composite_out, exp=6)
        if on_progress: on_progress("Pipeline complete!", 100)
        print(f"\n PIPELINE COMPLETE! Final output: {final_movie}")
        return final_movie
    else:
        print("No clips generated!")

if __name__ == "__main__":
    story = input("Enter story:\n")
    try:
        T = int(input("Enter video length (seconds): "))
    except ValueError:
        T = 10
    run_e2e_pipeline(story, T)
