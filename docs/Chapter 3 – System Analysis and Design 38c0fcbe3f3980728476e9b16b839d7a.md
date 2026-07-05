# Chapter 3 – System Analysis and Design

# 3.1 Use Case Diagram

The Use Case Diagram illustrates the interactions between the primary users of WritOath and the system's core functionalities. It identifies the services available to each actor and defines the system's functional scope.

During the initial release, WritOath supports a single primary actor:

- **Teacher**

Although administrators may be introduced in future versions, teacher users are responsible for all operational tasks within the system.

The Teacher can perform the following functions:

- Authenticate into the system
- Manage subjects
- Manage students
- Upload verified writing samples
- Submit student papers for analysis
- View analysis reports
- Validate analysis results
- View student writing profiles

```mermaid
flowchart

Teacher([Teacher])

subgraph WritOath

UC1((Login))

UC2((Manage Subjects))

UC3((Manage Students))

UC4((Upload Verified Writing Samples))

UC5((Upload Student Paper))

UC6((Analyze Paper))

UC7((View Analysis Report))

UC8((Validate Analysis Result))

UC9((View Student Writing Profile))

end

Teacher --> UC1
Teacher --> UC2
Teacher --> UC3
Teacher --> UC4
Teacher --> UC5
Teacher --> UC6
Teacher --> UC7
Teacher --> UC8
Teacher --> UC9
```

---

# 3.2 Activity Diagrams

Activity diagrams model the flow of control for the system's primary business processes.

Each activity diagram captures the sequence of actions, decision points, and outputs associated with a specific use case.

The following workflows are included:

| Activity Diagram | Purpose |
| --- | --- |
| Teacher Registration | Registers a new teacher account and initializes the system. |
| Student Management | Adds and manages student records under subjects. |
| Verified Writing Sample Upload | Registers the student's initial writing profile using verified documents. |
| Paper Analysis | Performs authorship verification using the AI pipeline. |
| Teacher Validation | Records the teacher's final decision after reviewing the AI analysis. |
| Student Writing Profile Update | Updates the student's writing profile using teacher-validated submissions. |

```mermaid
flowchart TD

Start([Start])

Login[Teacher Login]

Subject[Create Subject]

Student[Register Students]

Baseline[Upload 3 Verified Writing Samples]

Feature[Generate Writing Fingerprints]

Embed[Generate Embeddings]

StoreVector[Store in ChromaDB]

CreateProfile[Create Student Writing Profile]

Ready([System Ready])

Start --> Login
Login --> Subject
Subject --> Student
Student --> Baseline
Baseline --> Feature
Feature --> Embed
Embed --> StoreVector
StoreVector --> CreateProfile
CreateProfile --> Ready
```

```mermaid
flowchart TD

Start([Teacher Uploads Paper])

Validate[Validate Upload]

Orchestrator[AI Orchestrator]

Fingerprint[Writing Fingerprint Service]

Embedding[Generate Embedding]

Retrieve[Retrieve Verified Writing Samples]

Prompt[Build RAG Prompt]

LLM[Qwen 2.5 Analysis]

Scoring[Consistency Scoring]

Explain[Generate Explanation]

Result[Display Analysis]

Teacher[Teacher Reviews]

Decision{Accept Result?}

Update[Update Student Profile]

End([Finish])

Start --> Validate

Validate --> Orchestrator

Orchestrator --> Fingerprint

Fingerprint --> Embedding

Embedding --> Retrieve

Retrieve --> Prompt

Fingerprint --> Prompt

Prompt --> LLM

LLM --> Scoring

Scoring --> Explain

Explain --> Result

Result --> Teacher

Teacher --> Decision

Decision -- Yes --> Update

Decision -- No --> End

Update --> End
```

---

# 3.3 Sequence Diagrams

Sequence diagrams describe the chronological interaction between system components during a given process.

Unlike activity diagrams, sequence diagrams emphasize communication between actors, backend services, databases, and AI components.

The following sequence diagrams are included:

| Sequence Diagram | Purpose |
| --- | --- |
| Teacher Registration | Registers a new teacher account. |
| Upload Verified Writing Samples | Stores verified documents and initializes the student's writing profile. |
| Analyze Student Paper | Executes the complete AI pipeline from upload to report generation. |
| Teacher Validation | Saves teacher feedback and final verdict. |
| Student Writing Profile Update | Updates the writing profile after validation. |

```mermaid
sequenceDiagram

actor Teacher

participant Frontend

participant FastAPI

participant AI_Orchestrator

participant Fingerprint

participant ChromaDB

participant LangChain

participant Qwen

participant Scoring

participant MySQL

Teacher->>Frontend: Upload Paper

Frontend->>FastAPI: POST /analysis

FastAPI->>AI_Orchestrator: Analyze()

AI_Orchestrator->>Fingerprint: Extract Features

Fingerprint-->>AI_Orchestrator: Writing Fingerprint

AI_Orchestrator->>ChromaDB: Retrieve Verified Samples

ChromaDB-->>AI_Orchestrator: Top-k Samples

AI_Orchestrator->>LangChain: Build Prompt

LangChain->>Qwen: Compare Writing

Qwen-->>LangChain: Analysis

LangChain-->>AI_Orchestrator: Structured Response

AI_Orchestrator->>Scoring: Compute Score

Scoring-->>AI_Orchestrator: Score + Confidence

AI_Orchestrator->>MySQL: Save Result

AI_Orchestrator-->>FastAPI: Analysis Report

FastAPI-->>Frontend: Response

Frontend-->>Teacher: Display Report
```

---

# 3.4 Component Diagram

The Component Diagram illustrates the internal software modules that compose WritOath and the dependencies between them.

Unlike the architectural overview presented in Chapter 2, this diagram focuses on the logical organization of the application's software components.

Major components include:

- Next.js Frontend
- FastAPI Backend
- Application Layer
- AI Orchestrator
- Writing Fingerprint Service
- Embedding Service
- LangChain Pipeline
- Consistency Scoring Engine
- Explainability Engine
- Student Writing Profile Engine
- MySQL Database
- ChromaDB Vector Database
- Open-Source Language Model

```mermaid
flowchart LR

Frontend["Next.js"]

API["FastAPI"]

Application["Application Layer"]

AI["AI Orchestrator"]

Fingerprint["Writing Fingerprint Service"]

Embedding["Embedding Service"]

Retrieval["Retrieval Service"]

Prompt["Prompt Builder"]

LLM["Qwen 2.5"]

Scoring["Consistency Scoring Engine"]

Explain["Explainability Engine"]

Profile["Student Writing Profile Engine"]

MySQL[(MySQL)]

Chroma[(ChromaDB)]

Frontend --> API

API --> Application

Application --> AI

AI --> Fingerprint

AI --> Embedding

AI --> Retrieval

Retrieval --> Chroma

AI --> Prompt

Prompt --> LLM

AI --> Scoring

AI --> Explain

Explain --> MySQL

Profile --> MySQL

Profile --> Chroma
```

---

# 3.5 Deployment Diagram

The Deployment Diagram illustrates the physical infrastructure required to deploy WritOath.

The system consists of:

- Client Browser
- Next.js Web Application
- FastAPI Backend
- MySQL Database
- ChromaDB Vector Database
- Open-Source LLM Runtime

This deployment architecture separates presentation, application logic, AI processing, and persistence into independent layers, allowing each component to scale independently.

```mermaid
flowchart TD

Teacher["Teacher Browser"]

Vercel["Next.js Frontend
(Vercel)"]

Backend["FastAPI Backend
(Render/Railway)"]

MySQL[(MySQL)]

Chroma[(ChromaDB)]

LLM["Qwen 2.5 Runtime
(Ollama)"]

Teacher --> Vercel

Vercel --> Backend

Backend --> MySQL

Backend --> Chroma

Backend --> LLM
```

---

# 3.6 System Workflows

System workflows describe the end-to-end execution of the major processes within WritOath.

Unlike activity diagrams, workflows combine business logic and system behavior into a single implementation-oriented description.

The documented workflows include:

### Initial System Setup

- Teacher registration
- Subject creation
- Student registration
- Verified writing sample upload

---

### Paper Analysis Workflow

- Teacher uploads student paper
- AI Orchestrator coordinates the analysis
- Writing Fingerprint Service extracts stylometric features
- Embedding Service generates document embeddings
- ChromaDB retrieves the student's verified writing samples
- LangChain constructs the Retrieval-Augmented Generation context
- Open-source language model performs authorship comparison
- Consistency Scoring Engine computes evaluation metrics
- Explainability Engine generates the analysis report
- Results are presented to the teacher

---

### Teacher Validation Workflow

- Teacher reviews the generated report
- Teacher records the final verdict
- Feedback is stored in the database

---

### Student Writing Profile Evolution

- Teacher-approved submissions are evaluated for inclusion
- Student Writing Profile Engine updates the student's profile through versioning
- Future analyses use the updated profile for comparison