<div align="center">
  
# 🚀 SynthHire
**The Ultimate AI-Powered Semi-Auto Apply Job Portal & Interview Platform**

> 🎯 Practice interviews with AI personas that push back.  
> 📄 Beat ATS filters before you even hit apply.  
> ⚡ Semi-auto apply to jobs in minutes, not hours.  

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub stars](https://img.shields.io/github/stars/YourUsername/SynthHire-Interview-Platform?style=social)
![GitHub forks](https://img.shields.io/github/forks/YourUsername/SynthHire-Interview-Platform?style=social)

</div>

---

## 🎬 See It In Action

| Career Command Center | Interview Room | ATS Scorer |
|:---:|:---:|:---:|
| ![cc](./docs/assets/command-center.png) | ![ir](./docs/assets/interview-room.png) | ![ats](./docs/assets/ats-scorer.png) |

---

## ✨ Feature Overview

| Feature | Description | Powered By |
|---|---|---|
| 📄 **Resume ATS Scorer** | Parses & grades resumes against benchmarks | Gemini 2.5 Flash |
| 🎤 **AI Interview Simulation** | Voice interviews with 5 AI personas | Groq STT + Edge TTS |
| 🔗 **LinkedIn Optimizer** | Keyword & headline suggestions | Gemini 2.5 Flash |
| ⚡ **Semi-Auto Job Apply** | Cover letters from job descriptions | Gemini 2.5 Flash |
| 📚 **Prep Hub** | Flashcards, DSA warm-ups, cheat sheets | LLM-generated |
| 💻 **Live Code Execution** | Run 5 languages in sandboxed env | Docker-in-Docker |
| 📊 **8D Assessment Engine** | Scores 8 dimensions in real-time | Custom LLM Pipeline |

---

## 🎤 AI Personas

| Persona | Warmth | Probing Style | Interaction Tone |
|---|---|---|---|
| **Kind Mentor** | High | Frequent hints | Supportive and encouraging |
| **Tough Lead** | Low | Deep, rigorous probing | High standards, expects optimal solutions |
| **Tricky HR** | Medium | Tests emotional intelligence | Casual, looks for conflict resolution skills |
| **Silent Observer**| Low | Minimal interaction | High pressure, tests composure |
| **Collaborative Peer**| High | Brainstorms with you | Friendly and cooperative |

---

## 📊 8-Dimensional Assessment Engine
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

## 💻 The Advanced Interview Room
- **Multi-Layout Interface**: Seamlessly drag and split your view between *Default*, *Code*, *Chat*, and *Code+Chat* layouts.
- **Live Monaco Code Editor**: Built-in syntax highlighting and autocomplete.
- **Real-Time Code Execution**: Run Python, JavaScript, Java, C++, and Go instantly via securely sandboxed remote execution environments.
- **Screen Sharing**: Built-in screen casting for system design rounds. 

---

## 🏗️ System Architecture

SynthHire is structured as a highly scalable microservices architecture capable of handling long-running, stateful WebSocket connections for live interview sessions.

```mermaid
graph TD
    %% Define Styles
    classDef client fill:#000,stroke:#333,stroke-width:2px,color:#fff
    classDef proxy fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
    classDef service fill:#005571,stroke:#fff,stroke-width:2px,color:#fff
    classDef ai fill:#6C42A1,stroke:#fff,stroke-width:2px,color:#fff
    classDef infra fill:#316192,stroke:#fff,stroke-width:2px,color:#fff
    classDef queue fill:#DC382D,stroke:#fff,stroke-width:2px,color:#fff

    %% Frontend & Gateway
    Client["Client Browser<br/>(Next.js / React)"]:::client
    Nginx["Nginx Reverse Proxy<br/>(API Gateway)"]:::proxy
    
    %% Core Services
    Auth["Auth Service<br/>(JWT + User Auth)"]:::service
    UserSvc["User/Company Service<br/>(Profiles & Mgmt)"]:::service
    JobSvc["Job Service<br/>(Postings & Apps)"]:::service
    
    %% Interview Pipeline
    Orchestrator["Session Orchestrator<br/>(WebSocket Hub)"]:::service
    Speech["Speech Pipeline<br/>(STT/TTS Engine)"]:::service
    Executor["Code Sandbox<br/>(Docker Execution)"]:::service
    Assessor["Assessment Engine<br/>(Real-Time Scoring)"]:::service
    
    %% AI APIs
    Gemini["Google Gemini<br/>2.5 Flash"]:::ai
    Groq["Groq STT"]:::ai
    Edge["Edge TTS"]:::ai
    
    %% Databases
    Postgres[("PostgreSQL<br/>(Relational State)")]:::infra
    Mongo[("MongoDB<br/>(Session Transcripts)")]:::infra
    Redis["Redis<br/>(PubSub & Cache)"]:::queue

    %% Flow Connections
    Client <==>|HTTP / WSS| Nginx
    
    Nginx --> Auth
    Nginx --> UserSvc
    Nginx --> JobSvc
    Nginx <==>|WSS| Orchestrator
    
    Auth --> Postgres
    UserSvc --> Postgres
    JobSvc --> Postgres
    
    %% Orchestrator is the brain
    Orchestrator <--> Redis
    Orchestrator --> Mongo
    Orchestrator <--> Executor
    Orchestrator <--> Assessor
    Orchestrator <--> Speech
    
    %% External AI Communication
    Assessor --> Gemini
    Speech --> Groq
    Speech --> Edge
```

### Component Breakdown
- **Gateway Layer**: Nginx acts as the reverse proxy, intelligently routing stateless HTTP traffic to standard microservices while maintaining stateful, persistent WebSocket (WSS) tunnels specifically to the Orchestrator.
- **Session Orchestrator**: The "brain" of the platform. Maintains the real-time WebSocket connection for live coding events, synchronizes the chat state via Redis PubSub, and coordinates the AI subsystems.
- **Assessment Engine**: Passes streaming user chat context and code execution output through Google Gemini to calculate the 8-dimensions of performance.
- **Code Sandbox**: A secure Docker-in-Docker isolated environment that compiles and runs candidate code instantly without exposing the host OS to malicious attempts.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, TailwindCSS, Monaco Editor, WebRTC |
| **Backend** | FastAPI, Python 3.11, Microservices |
| **AI / ML** | Google Gemini 2.5 Flash, Groq STT, Edge TTS |
| **Databases** | PostgreSQL, MongoDB, Redis |
| **DevOps** | Docker Compose, Nginx, GitHub Actions |
| **Auth** | RSA-256 Asymmetric JWT (Zero-Trust) |

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

---

## 🗺️ Roadmap
- [x] WebRTC voice integration
- [x] 8-Dimension scoring engine
- [x] Live code execution (5 languages)
- [x] Semi-Auto Job Apply Portal
- [ ] Browser extension for accelerating semi-auto job applications
- [ ] Mobile application (iOS & Android)
- [ ] LeetCode-style problem bank
- [ ] Dedicated company portal to serve as a screening layer before physical interviews

---

## 🛡️ Security Posture
- **Zero-Trust Microservices**: All internal service-to-service calls require signed JWTs.
- **Pterodactyl-Style Execution**: Candidate code is executed in isolated, resource-capped, ephemeral containers preventing host-escape vulnerabilities.
- **Environment Isolation**: No hardcoded secrets. Strict separation of local, staging, and production `.env` files.

---

## 🤝 Contributing
PRs are welcome! Open an issue before submitting major changes.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

⭐ **If SynthHire helped you, star the repo — it helps others discover it!**
