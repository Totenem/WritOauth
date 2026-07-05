# Chapter 7 - Project Cost Analysis and Budget Estimation

## 7.1 Cost Overview

This chapter presents the estimated financial requirements for the development and deployment of WritOath. The system is intentionally designed to utilize open-source technologies and free-tier cloud services wherever possible, minimizing operational costs while maintaining a scalable and production-ready architecture.

Considering the expected deployment environment of approximately 5–10 teachers managing 100–200 students, the projected monthly operational cost remains low. This makes WritOath a practical solution for educational institutions with limited technical and financial resources.

The cost estimates presented in this chapter represent the expected expenses during both the development phase and the initial production deployment.

---

# 7.2 Development Cost

The development phase primarily relies on open-source software and educational licenses, resulting in minimal upfront expenses.

| Item | Technology | Cost |
| --- | --- | --- |
| IDE | Visual Studio Code | Free |
| Version Control | Git & GitHub | Free |
| Frontend Framework | Next.js | Free |
| Backend Framework | FastAPI | Free |
| Database | MySQL | Free |
| Vector Database | ChromaDB | Free |
| AI Framework | LangChain | Free |
| Open-Source LLM | Qwen 2.5 Instruct | Free |
| Embedding Model | Embedding model served via Ollama | Free |
| Containerization | Docker | Free |
| API Testing | Postman | Free |
| Project Management | GitHub Projects / Trello | Free |

**Estimated Development Software Cost:** **₱0.00**

---

# 7.3 Infrastructure Cost

The initial deployment leverages free-tier cloud services while allowing future upgrades if user demand increases.

| Component | Service | Estimated Monthly Cost |
| --- | --- | --- |
| Frontend Hosting | Vercel (Free Tier) | ₱0 |
| Backend Hosting | Railway or Render (Starter) | ₱0–₱600 |
| Database | Railway MySQL / Aiven Free | ₱0–₱300 |
| Vector Database | Self-hosted ChromaDB | ₱0 |
| AI Model Hosting | Ollama (Local) | ₱0 |
| Domain Name *(Optional)* | .com Domain | ~₱900/year |
| SSL Certificate | Let's Encrypt | ₱0 |
| Monitoring | UptimeRobot | ₱0 |
| Error Monitoring | Sentry Free Tier | ₱0 |
| Container Registry | GitHub Container Registry | ₱0 |

### Estimated Monthly Operational Cost

| Scenario | Cost |
| --- | --- |
| Development | ₱0 |
| Free Deployment | ₱0 |
| Small Production Deployment | ₱300–₱900/month |

---

# 7.4 Artificial Intelligence Cost Analysis

Unlike many AI-powered systems that depend on paid API services, WritOath utilizes an open-source language model integrated through LangChain and Retrieval-Augmented Generation (RAG).

This architecture eliminates per-request API charges and avoids recurring subscription fees associated with commercial AI providers.

The AI subsystem consists entirely of open-source components, including:

| Component | Cost |
| --- | --- |
| Qwen 2.5 Instruct | Free |
| LangChain | Free |
| ChromaDB | Free |
| Ollama (LLM & embedding runtime) | Free |

As a result, the system incurs no direct AI usage fees during normal operation.

---

# 7.5 Hardware Requirements

The proposed hardware specifications are sufficient for development and small-scale deployment.

### Development Machine

| Component | Recommended Specification |
| --- | --- |
| Processor | Intel Core i5 (10th Gen or newer) / AMD Ryzen 5 |
| Memory | 16 GB RAM |
| Storage | 512 GB SSD |
| GPU | Optional |
| Operating System | Windows 11, Ubuntu 22.04, or macOS |

### Production Server

| Component | Recommended Specification |
| --- | --- |
| CPU | 2–4 vCPUs |
| Memory | 8–16 GB RAM |
| Storage | 80–100 GB SSD |
| Network | Stable broadband connection |

These specifications are adequate for supporting the target deployment size while leaving room for moderate growth.

---

# 7.6 Scalability Considerations

The infrastructure is designed to support future expansion without requiring major architectural changes.

Potential scaling strategies include:

- Upgrading backend compute resources
- Migrating MySQL to a managed database service
- Deploying ChromaDB on a dedicated server
- Hosting the language model on a dedicated inference server
- Load balancing backend services
- Horizontal scaling of API instances

Because the application follows a modular architecture, each component can be upgraded independently based on demand.

---

# 7.7 Cost Optimization Strategies

To minimize operational expenses, WritOath incorporates several cost-saving measures:

- Use of open-source AI models instead of commercial APIs.
- Deployment on free-tier cloud platforms during development.
- Local hosting of ChromaDB and AI inference where feasible.
- Containerization with Docker to simplify deployment and resource management.
- Efficient Retrieval-Augmented Generation to reduce unnecessary model computation.
- Lightweight embedding models to lower memory and processing requirements.

These strategies ensure that the system remains affordable while preserving functionality and scalability.

---

# 7.8 Budget Summary

| Category | Estimated Cost |
| --- | --- |
| Development Software | ₱0 |
| AI Services | ₱0 |
| Cloud Infrastructure | ₱300–₱900/month *(if using paid starter tiers)* |
| Domain Name *(Optional)* | ~₱900/year |
| SSL Certificate | ₱0 |
| Monitoring Tools | ₱0 |
| Container Registry | ₱0 |

### Total Estimated Budget

| Phase | Estimated Cost |
| --- | --- |
| Development Phase | **₱0** |
| Initial Deployment (Free Tier) | **₱0/month** |
| Small Production Deployment | **₱300–₱900/month** |

---

# 7.9 Cost Justification

The financial design of WritOath aligns with the project's objective of providing an accessible and sustainable authorship verification system for educational institutions. By relying on open-source software, free development tools, and low-cost cloud infrastructure, the project minimizes implementation costs without compromising functionality or scalability.

The adoption of Retrieval-Augmented Generation with locally hosted or open-source language models further reduces long-term operational expenses by eliminating dependence on commercial AI APIs. This approach ensures that institutions can deploy and maintain the system with minimal recurring costs while retaining full control over their data and AI infrastructure.