import e2e_pipeline

story = "A futuristic car flying through a neon lit city at night"
T = 10

if __name__ == "__main__":
    final_video = e2e_pipeline.run_e2e_pipeline(story, T)
    print("Final video generated at:", final_video)
