
@'
# MemoraAI – AI-Powered Personal Knowledge Intelligence Platform

MemoraAI is an AI-powered knowledge management platform that helps users organize their documents and retrieve information through natural-language questions.

## Features

- User registration and authentication
- Upload and manage PDF, DOCX, and TXT documents
- Document text extraction and processing
- Semantic search across personal documents
- Retrieval-Augmented Generation (RAG) for question answering
- Conversation management
- PostgreSQL database integration

## Technology Stack

**Frontend:** React.js, JavaScript, HTML, CSS

**Backend:** Python, FastAPI

**Database:** PostgreSQL

**AI and Search:** Groq integration, embeddings, semantic similarity, RAG

## Project Structure

```text
MemoraAI_Project/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   └── main.py
├── frontend/
│   └── src/
├── database/
├── docs/
├── tests/
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Preranasisodiya/MemoraAI.git
cd MemoraAI
```

### 2. Set up the backend

Create and activate a Python virtual environment, then install the dependencies listed in your backend requirements file.

Create a backend `.env` file with your local PostgreSQL connection URL and required AI API credentials. Never commit this file or expose your secrets.

Start the FastAPI server using the command appropriate for your project configuration.

### 3. Set up the frontend

Install the frontend dependencies:

```bash
cd frontend
npm install
npm run dev
```

### 4. Access the application

Open the local frontend URL displayed by the development server. The backend API documentation is generally available at `/docs` on the backend server.

## Future Enhancements

- Support for additional document formats
- Improved retrieval and response evaluation
- Enhanced document organization and knowledge discovery

## Author

Prerana Sisodiya

GitHub: [Preranasisodiya](https://github.com/Preranasisodiya)
'@ | Set-Content -Path .\README.md -Encoding utf8
