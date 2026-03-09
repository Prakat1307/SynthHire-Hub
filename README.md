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
| 📄 **Resume ATS Scorer** | Parses & grades resumes against benchmarks | GPT-4o |
| 🎤 **AI Interview Simulation** | Voice interviews with 5 AI personas | Groq STT + Edge TTS |
| 🔗 **LinkedIn Optimizer** | Keyword & headline suggestions | GPT-4o |
| ⚡ **Semi-Auto Apply** | Cover letters from job descriptions | GPT-4o |
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

![Architecture](./docs/assets/architecture.png)

SynthHire is structured as a scalable monorepo capable of handling thousands of concurrent WebSocket connections.
- **Microservices**: Auth, Session Orchestrator, Evaluation Engine, Code Executor, Speech Pipeline, Resumes, Jobs.
- **Data Layer**: PostgreSQL (Relational), MongoDB (Document Storage), Redis (PubSub/Cache).

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, TailwindCSS, Monaco Editor, WebRTC |
| **Backend** | FastAPI, Python 3.11, Microservices |
| **AI / ML** | OpenAI GPT-4o, Groq STT, Edge TTS |
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
- [ ] Mobile app (React Native)
- [ ] Behavioral interview mode
- [ ] LeetCode-style problem bank
- [ ] Recruiter / Company dashboard

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
