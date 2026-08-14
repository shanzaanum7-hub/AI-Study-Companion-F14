# AI Study Companion — F14

AI Study Companion is an AI-powered study assistant built with **FastAPI, Next.js, Gemini AI, and Qdrant**. It allows students to upload PDF or TXT study material, split it into meaningful chunks, generate embeddings, store them in Qdrant, retrieve relevant information, and generate study plans using retrieved content.

## Project Overview

The project implements a retrieval-augmented study workflow:

```text
PDF / TXT Document
        ↓
   Text Extraction
        ↓
      Chunking
        ↓
 Gemini Embeddings
        ↓
      Qdrant
        ↓
   Relevant Retrieval
        ↓
   Gemini Generation
        ↓
    Study Plan
```

## Week 3 Scope

This project implements the Week 3 AI & Generative AI Fellowship requirements:

* Document upload for PDF and TXT files
* Text extraction from uploaded documents
* Meaningful document chunking
* Gemini embedding generation
* Qdrant vector storage
* Retrieval of relevant document chunks
* Basic study plan generation using retrieved content
* FastAPI backend APIs
* Next.js frontend

## Tech Stack

### Frontend

* Next.js
* React
* TypeScript

### Backend

* Python
* FastAPI
* Uvicorn
* PyMuPDF (fitz)

### AI

* Google Gemini
* `google-genai`

### Vector Database

* Qdrant

### Other Tools

* Docker
* Git
* GitHub
* python-dotenv

## Features

### 1. Document Upload

Users can upload:

* PDF study notes
* TXT study notes

The backend saves the document and starts the ingestion pipeline.

### 2. Text Extraction

For PDF files, text is extracted using PyMuPDF.

For TXT files, the file is read using UTF-8 encoding.

### 3. Chunking

The extracted text is divided into meaningful chunks.

The implementation prefers paragraphs and splits long content by sentences and words when necessary.

The current maximum chunk size is approximately **2000 characters**.

### 4. Embeddings

Each chunk is converted into a numerical vector using the configured Gemini embedding model.

The embedding model is configured through environment variables.

### 5. Qdrant Storage

Generated embeddings are stored in a Qdrant collection named:

```text
study_notes
```

Each vector stores metadata including:

* document ID
* chunk ID
* chunk index
* original chunk text

### 6. Retrieval

The retrieval layer searches the Qdrant vector database for chunks relevant to a student's query.

Retrieved chunks can then be passed to the generation layer.

### 7. Study Plan Generation

The study-plan layer uses retrieved study content together with Gemini to generate structured study-plan information.

## Qdrant Setup

Qdrant is required for the project.

Make sure Docker Desktop is running, then start Qdrant with:

```powershell
docker run -p 6333:6333 qdrant/qdrant
```

Qdrant will be available at:

```text
http://localhost:6333
```

The Qdrant dashboard can be opened at:

```text
http://localhost:6333/dashboard
```

## Environment Variables

Create a `.env` file inside the `backend` directory.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key_here

GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSION=768

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=study_notes
```

### Important

Never commit API keys or database credentials to GitHub.

The `.env` file should remain private and should be included in `.gitignore`.

## Backend Setup

Open PowerShell in the project directory:

```powershell
cd backend
```

Create and activate a virtual environment if required:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

## Document Upload API

### Endpoint

```text
POST /api/v1/upload
```

The endpoint accepts:

* PDF or TXT file
* title
* subject
* language
* tags

The endpoint performs:

```text
Upload
  ↓
Text Extraction
  ↓
Chunk Creation
  ↓
Gemini Embedding Generation
  ↓
Qdrant Storage
```

A successful response contains the document ID and indexing status.

Example successful response:

```json
{
  "success": true,
  "message": "File uploaded and indexed successfully.",
  "data": {
    "document_id": "document-id",
    "filename": "study-notes.pdf",
    "status": "completed",
    "message": "Created chunks and stored vectors in Qdrant."
  }
}
```

## API Endpoints

### Health

```text
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/health
```

### Upload

```text
POST /api/v1/upload
```

### Retrieval

```text
POST /api/v1/retrieve
POST /api/v1/retrieval/search
POST /api/v1/retrieval/ask
```

### Study Plan

```text
POST /api/v1/study-plan
POST /api/v1/study-plan/generate
POST /api/v1/study-plan/summary
POST /api/v1/study-plan/flashcards
```

## Running the Complete Project

### Step 1 — Start Qdrant

```powershell
docker run -p 6333:6333 qdrant/qdrant
```

### Step 2 — Start Backend

```powershell
cd backend
uvicorn app.main:app --reload
```

### Step 3 — Open Swagger

Open:

```text
http://localhost:8000/docs
```

### Step 4 — Upload Study Material

Use:

```text
POST /api/v1/upload
```

Upload a PDF or TXT study document.

### Step 5 — Verify Qdrant

Open:

```text
http://localhost:6333/dashboard
```

Check the `study_notes` collection and verify that vectors have been stored.

### Step 6 — Test Retrieval

Use the retrieval endpoints to search for relevant information from the uploaded study material.

### Step 7 — Generate Study Plan

Use the study-plan endpoint to generate a basic study plan using retrieved study content.

## Week 3 Build Order

The implementation follows the required Week 3 build order:

1. Document upload endpoint
2. Chunking logic
3. Generate embeddings
4. Create Qdrant collection and store embeddings
5. Retrieval of relevant chunks
6. Study plan generation
7. Frontend rendering and README documentation

## Project Structure

```text
AI-Study-Companion-F14/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── uploads/
│   │   ├── main.py
│   │   └── config.py
│   │
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── test_gemini.py
│
├── frontend/
│   └── ...
│
├── .gitignore
├── LICENSE
└── README.md
```

## Security

API keys and credentials are stored using environment variables.

Do not hardcode secrets in Python, frontend code, README files, or GitHub commits.

Make sure `.env` is included in `.gitignore`.

## Week 3 Result

The Week 3 ingestion pipeline successfully supports:

```text
Study Document
      ↓
Text Extraction
      ↓
Chunking
      ↓
Gemini Embeddings
      ↓
Qdrant Vector Storage
      ↓
Retrieval
      ↓
Study Plan Generation
```

The system provides the retrieval foundation required for the next stage of the AI Study Companion project.
