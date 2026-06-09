# 🎥 VG - AI Video Generation Pipeline

VG is an end-to-end **AI-powered video generation system** that transforms **user prompts into generated videos** using state-of-the-art generative AI models and orchestration pipelines.

The project combines **prompt enhancement, model orchestration, video generation, interpolation, and deployment infrastructure** to create high-quality AI-generated videos from natural language input.

---

## ✨ Features

* 📝 **Prompt-to-Video Generation**

  * Convert text prompts into AI-generated videos.

* 🧠 **Prompt Enhancement**

  * Improves user prompts for better generation quality.

* 🎬 **Multiple Generation Pipelines**

  * Supports different model clients and workflows.

* ⚡ **Frame Interpolation**

  * Uses RIFE interpolation for smoother video transitions.

* ☁️ **Scalable Deployment**

  * Modal integration for scalable cloud execution.

* 🔄 **Orchestrated Pipeline**

  * Modular orchestration system for handling generation stages.

* 🎥 **End-to-End Workflow**

  * From user input → processing → generation → final video output.

---

## 🏗️ Project Architecture

```text
User Prompt
      │
      ▼
Prompt Enhancement
      │
      ▼
Generation Pipeline
(Flux / WAN / Gemma)
      │
      ▼
Frame Processing
      │
      ▼
RIFE Interpolation
      │
      ▼
Final Generated Video
```

---

## 📂 Project Structure

```text
VG/
│── frontend/                 # Frontend interface
│── .gitignore
│── aaahhaa.ipynb             # Experimental notebook
│── audio_client.py           # Audio processing client
│── client.py                 # Main client
│── convert.py                # Conversion utilities
│── e2e_pipeline.py           # End-to-end generation pipeline
│── fix_pipeline.py           # Pipeline fixes
│── flux_client.py            # Flux model integration
│── gemma_video_pipeline.py   # Gemma-based video pipeline
│── generate_test.py          # Generation testing
│── modal_app.py              # Modal deployment
│── orchestrator.py           # Pipeline orchestration
│── patch_nb.py               # Patch utilities
│── patch_transitions.py      # Video transition patches
│── prompt_enhancer.py        # Prompt enhancement
│── raw_post.py               # Raw post-processing
│── read_log.py               # Logging utility
│── rife_interpolation.py     # Frame interpolation (RIFE)
│── rife_modal_app.py         # RIFE Modal deployment
│── server.py                 # Backend server
│── wan_client.py             # WAN model integration
│── wan_modal_app.py          # WAN deployment
│── requirements.txt          # Project dependencies
```

---

## 🛠️ Tech Stack

### AI / ML Models

* Flux
* WAN
* Gemma Video Pipeline
* RIFE Frame Interpolation

### Backend

* Python
* FastAPI / Server-based Architecture

### Deployment

* Modal

### Frontend

* Custom Frontend Interface

---

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/sshreyas05/VG.git
cd VG
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project

### 1. Start the backend server

```bash
python server.py
```

### 2. Run the end-to-end pipeline

```bash
python e2e_pipeline.py
```

### 3. Test generation

```bash
python generate_test.py
```

---

## 💡 Example Workflow

### Input Prompt

```text
"A cinematic cyberpunk city at night with flying cars and neon lights"
```

### Processing Pipeline

1. User enters a text prompt.
2. Prompt enhancer optimizes the text.
3. Video generation model (Flux/WAN/Gemma) creates frames.
4. RIFE interpolation smooths motion.
5. Final video is generated.

### Output

🎥 AI-generated cinematic video generated from the prompt.

---

## 🔧 Core Components

### Prompt Enhancer (`prompt_enhancer.py`)

Optimizes user prompts to improve video quality and model understanding.

### Orchestrator (`orchestrator.py`)

Handles coordination between different pipelines and model workflows.

### Generation Pipelines

Supports multiple video generation approaches:

* **Flux Client**
* **WAN Client**
* **Gemma Video Pipeline**

### RIFE Interpolation (`rife_interpolation.py`)

Adds intermediate frames for smoother and more realistic motion.

### Modal Deployment

Cloud deployment support for scalable GPU inference.

---

## 🔄 End-to-End Pipeline

```text
Text Prompt
     │
     ▼
Prompt Enhancement
     │
     ▼
Video Generation
(Flux / WAN / Gemma)
     │
     ▼
Frame Processing
     │
     ▼
RIFE Interpolation
     │
     ▼
Post Processing
     │
     ▼
Generated Video
```

---

## 📈 Future Improvements

* Real-time video generation
* Faster inference optimization
* Multi-style video generation
* Voice-to-video support
* Custom model fine-tuning
* Better frontend UI/UX
* Cloud-scale deployment improvements

---

## 🧪 Research / Experimental Work

This repository also includes experimentation notebooks and prototype pipelines for:

* Model benchmarking
* Pipeline optimization
* Transition patching
* Latency improvements
* Video quality enhancement

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a new branch

```bash
git checkout -b feature-name
```

3. Commit changes

```bash
git commit -m "Add feature"
```

4. Push changes

```bash
git push origin feature-name
```

5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Shreyas Shedge**

GitHub: https://github.com/sshreyas05

---

⭐ If you found this project useful, consider starring the repository.
