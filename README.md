<div align="center">
  
# 🚀 SynthHire
**The Ultimate Enterprise AI Interview & Career Advancement Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

*Practice with hyper-realistic AI Personas. Optimize your ATS score. Land the job.*

</div>

---

## 🌟 The Vision

SynthHire isn't just an interview simulator—it's an end-to-end career advancement ecosystem. Built on a production-ready microservices architecture, SynthHire bridges the gap between applying for a job and acing the final technical round.

Whether you are a **Company** looking to streamline recruitment or a **Candidate** aiming to master system design and algorithms under pressure, SynthHire provides real-time, multi-modal AI feedback to elevate your game.

---

## ✨ Flagship Features

### 🧠 The Career Command Center
- **Resume ATS Scorer**: Instantly parse and grade resumes against thousands of industry benchmarks. Get actionable suggestions to bypass algorithmic filters.
- **LinkedIn Profile Optimizer**: Connect your LinkedIn directly. Our AI analyzes your digital footprint to suggest bullet-point improvements, keyword injections, and headline adjustments.
- **Semi-Auto Apply**: Stop filling out repetitive forms. SynthHire generates targeted cover letters and automatically scaffolds your job applications based on the Role Description.
- **Prep Hub**: A dedicated learning center with dynamic flashcards, algorithmic warm-ups, and company-specific "cheat sheets" generated on the fly.

### 🎤 Hyper-Realistic Interview Simulation
- **WebRTC Voice Integration**: Talk naturally to your interviewer. Powered by lightning-fast **Groq Speech-to-Text** and immersive **Edge TTS**, the sub-second latency makes it feel like a real conversation.
- **5 Dynamic AI Personas**: 
  - *Kind Mentor*: High warmth, frequent hints, supportive tone.
  - *Tough Lead*: Low warmth, deep probing, rigorous standards.
  - *Tricky HR*: High ambiguity, tests emotional intelligence and conflict resolution.
  - *Collaborative Peer*: Friendly, brainstorms with you.
  - *Silent Observer*: Minimal interaction, high pressure.

### 💻 The Advanced Interview Room
- **Multi-Layout Interface**: Seamlessly drag and split your view between *Default*, *Code*, *Chat*, and *Code+Chat* layouts.
- **Live Monaco Code Editor**: Built-in syntax highlighting and autocomplete.
- **Real-Time Code Execution**: Run Python, JavaScript, Java, C++, and Go instantly via securely sandboxed remote execution environments.
- **Screen Sharing**: Built-in screen casting for system design rounds. 

### 📊 8-Dimensional Assessment Engine
Stop guessing how you did. Get real-time, objective scoring across 8 vectors:
1. Technical Correctness 
2. Problem Decomposition 
3. Communication Clarity 
4. Handling Ambiguity 
5. Edge Case Awareness 
6. Time Management 
7. Collaborative Signals 
8. Growth Mindset

---

## 🏗️ Enterprise Architecture

SynthHire is structured as a scalable monorepo capable of handling thousands of concurrent WebSocket connections.

### Microservices (Python / FastAPI)
- **Auth Service**: Asymmetric RSA-256 JWT Authentication
- **Session Orchestrator**: High-frequency WebSockets & State Machine
- **Evaluation Engine**: LLM-based parsing and real-time grading
- **Code Executor**: Isolated docker-in-docker execution environment
- **Speech Pipeline**: Audio stream chunking and STT/TTS translation
- *...and dedicated services for Resumes, Companies, Jobs, and Reports!*

### Data Layer
- **PostgreSQL**: Relational truth (Users, Subscriptions, Roles)
- **MongoDB**: Unstructured document storage (Transcripts, Chat Memory)
- **Redis**: Low-latency PubSub, Rate-limiting, and Session constraints

---

## 🚀 Deployment Guide

SynthHire is fully containerized. You do not need to configure ports or install local runtimes—Docker handles everything.

### 1. Environment Setup
Clone the repository and set up your environment keys.
```bash
git clone https://github.com/YourUsername/SynthHire-Interview-Platform.git
cd SynthHire-Interview-Platform/backend
cp .env.template .env
```
*(Ensure your `.env` contains the required keys for OpenAI, Groq, and database URIs).*

### 2. Generate RSA Keys
Generate secure cryptographic keys for internal microservice communication:
```bash
python scripts/generate_keys.py
```

### 3. Launch the Stack
Start the databases, cache layers, backend microservices, Next.js frontend, and Nginx reverse proxy in detached mode:
```bash
docker-compose up -d --build
```

### 4. Database Initialization
Once the containers are healthy, seed the initial database schema:
```bash
docker exec -it synthhire-auth python scripts/init_db.py
```

Your enterprise testing environment is now live and routing traffic securely.

---

## 🛡️ Security Posture
- **Zero-Trust Microservices**: All internal service-to-service calls require signed JWTs.
- **Pterodactyl-Style Execution**: Candidate code is executed in isolated, resource-capped, ephemeral containers preventing host-escape vulnerabilities.
- **Environment Isolation**: No hardcoded secrets. Strict separation of local, staging, and production `.env` files.

---

<div align="center">
  <b>Built to revolutionize technical hiring and preparation.</b>
</div>
