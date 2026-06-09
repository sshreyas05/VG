# 🎥 VG - AI Video Generation Pipeline

VG is an end-to-end **AI-powered video generation system** that transforms **user prompts into generated videos** using state-of-the-art generative AI models and orchestration pipelines.

The project combines **prompt enhancement, model orchestration, video generation, interpolation, and deployment infrastructure** to create high-quality AI-generated videos from natural language input.

---

## ✨ Features

- 📝 **Prompt-to-Video Generation**
  - Convert text prompts into AI-generated videos.

- 🧠 **Prompt Enhancement**
  - Improves user prompts for better generation quality.

- 🎬 **Multiple Generation Pipelines**
  - Supports different model clients and workflows.

- ⚡ **Frame Interpolation**
  - Uses RIFE interpolation for smoother video transitions.

- ☁️ **Scalable Deployment**
  - Modal integration for scalable cloud execution.

- 🔄 **Orchestrated Pipeline**
  - Modular orchestration system for handling generation stages.

- 🎥 **End-to-End Workflow**
  - From user input → processing → generation → final video output.

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
