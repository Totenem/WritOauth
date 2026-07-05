# Chapter 4 – Database Design

# 4.3 Relationship Explanations

## TEACHER → SUBJECT

**Relationship:** One-to-Many

A teacher can manage multiple subjects, while each subject belongs to only one teacher. This relationship allows subjects to be organized under the teacher responsible for managing them.

---

## STUDENT → PAPERS

**Relationship:** One-to-Many

A student may produce multiple papers throughout the academic term. This relationship enables the system to collect sufficient writing samples for authorship analysis and profile evolution.

---

## SUBJECT → PAPERS

**Relationship:** One-to-Many

Each paper is associated with a specific subject. This relationship provides academic context and allows submissions to be filtered and analyzed according to subject.

---

## PAPERS → FEATURE_VECTOR

**Relationship:** One-to-One

Every submitted paper generates a corresponding feature vector containing stylometric characteristics extracted during preprocessing. These features are used by the AI pipeline to assist in authorship verification.

---

## PAPERS → ANALYSIS_RESULT

**Relationship:** One-to-One

Each analyzed paper receives one analysis result containing the overall consistency score, confidence level, and additional evaluation metrics.

---

## PAPERS → FEEDBACK

**Relationship:** One-to-One

Each paper may receive one teacher validation after analysis. This allows human verification of the AI-generated assessment and supports continuous improvement of the student's writing profile.

---

## STUDENT → BASELINE_PROFILE

**Relationship:** One-to-Many

Each student maintains one or more writing profile versions throughout the system's lifetime. Versioning allows WritOath to adapt to natural improvements in writing while preserving historical profile data.

---

# 4.4 Data Dictionary

## TEACHER

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| name | VARCHAR | Teacher's full name |
| email | VARCHAR | Teacher email address |
| password | VARCHAR | Encrypted password |
| created_at | DATETIME | Record creation timestamp |

---

## SUBJECT

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| teacher_id | INT | References Teacher |
| name | VARCHAR | Subject name |
| created_at | DATETIME | Record creation timestamp |

---

## STUDENT

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| name | VARCHAR | Student full name |
| created_at | DATETIME | Record creation timestamp |

---

## PAPERS

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| student_id | INT | References Student |
| subject_id | INT | References Subject |
| type | ENUM | Verified Sample or Submission |
| content | LONGTEXT | Document content |
| created_at | DATETIME | Upload timestamp |

---

## FEATURE_VECTOR

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| paper_id | INT | References Papers |
| features | JSON | Extracted stylometric features |

---

## BASELINE_PROFILE

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| student_id | INT | References Student |
| version | INT | Profile version |
| confidence_level | FLOAT | Profile confidence score |
| aggregated_features | JSON | Aggregated writing characteristics |

---

## ANALYSIS_RESULT

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| paper_id | INT | References Papers |
| consistency_score | FLOAT | Overall consistency score |
| confidence_level | FLOAT | AI confidence level |
| breakdown | JSON | Detailed scoring breakdown |

---

## FEEDBACK

| Field | Type | Description |
| --- | --- | --- |
| id | INT | Primary Key |
| paper_id | INT | References Papers |
| decision | ENUM | Genuine or Flagged |
| remarks | TEXT | Teacher comments |
| created_at | DATETIME | Validation timestamp |

---

# 4.5 Database Constraints

To ensure data consistency and integrity, WritOath enforces the following database constraints.

## Primary Keys

Every table contains a unique primary key (`id`) that uniquely identifies each record.

---

## Foreign Keys

The database enforces referential integrity through foreign key relationships.

| Parent Table | Child Table |
| --- | --- |
| Teacher | Subject |
| Student | Papers |
| Subject | Papers |
| Papers | Feature_Vector |
| Papers | analysis_result |
| Papers | Feedback |
| Student | Baseline_Profile |

---

## Unique Constraints

The following fields must remain unique:

- Teacher email address
- Student profile version per student
- One feature vector per paper
- One score per paper
- One feedback record per paper

---

## Cascading Rules

The following cascading policies are recommended:

| Operation | Action |
| --- | --- |
| Delete Teacher | Restrict if subjects exist |
| Delete Subject | Restrict if papers exist |
| Delete Student | Cascade to papers, feature vectors, scores, and feedback |
| Delete Paper | Cascade to feature vector, score, and feedback |

These rules preserve database consistency while preventing orphaned records.

---

# 4.6 Storage Architecture

WritOath uses two independent storage systems, each optimized for a different purpose.

## Relational Database (MySQL)

MySQL stores structured application data and serves as the system's primary transactional database.

Stored information includes:

- Teachers
- Subjects
- Students
- Papers
- Writing Profiles
- Feature Metadata
- Analysis Results
- Teacher Feedback

---

## Vector Database (ChromaDB)

ChromaDB stores semantic embeddings generated from verified writing samples and teacher-approved submissions.

Unlike MySQL, ChromaDB does not store relational data. Its sole purpose is to perform semantic similarity searches during the Retrieval-Augmented Generation (RAG) workflow.

This separation allows WritOath to efficiently manage structured application data and high-dimensional vector representations independently.

---

# 4.7 Database Design Considerations

The database design was guided by the following principles:

### Normalization

Entities are normalized to reduce redundancy while maintaining efficient relationships between teachers, students, subjects, and papers.

### Scalability

The schema supports future expansion, including additional user roles, institution-level deployments, and larger collections of writing samples without requiring structural redesign.

### Separation of Concerns

Structured application data and semantic vector embeddings are maintained in separate storage systems. MySQL manages transactional data, while ChromaDB is dedicated to vector retrieval.

### Versioning

Student writing profiles are versioned to allow the system to adapt to natural writing development while preserving historical data for comparison and auditing.