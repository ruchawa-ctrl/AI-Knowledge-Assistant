# AI Knowledge Assistant (RAG)

Upload your own documents (PDF, txt, md, csv), then ask questions in natural
language. Answers are generated **only** from your indexed content and come with
cited sources.

This is a full **Retrieval-Augmented Generation (RAG)** app:

```
Upload → extract text → chunk → embed → store in vector DB
Ask → embed question → retrieve top-k chunks → LLM answers with citations
```

## Tech stack

| Layer        | Tech                                              |
| ------------ | ------------------------------------------------- |
| Frontend     | React 18 + Vite                                   |
| Backend      | FastAPI (Python)                                  |
| Vector store | ChromaDB (persistent, on disk)                    |
| Metadata DB  | SQLite via SQLAlchemy                             |
| LLM / Embed  | OpenAI-compatible API (OpenAI, Ollama, LM Studio) |

## Project structure

```
ai-knowledge-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + CORS + routers
│   │   ├── config.py          # env-based settings
│   │   ├── database.py        # SQLAlchemy models (documents, chat_messages)
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── rag/
│   │   │   ├── chunking.py    # text extraction + chunking
│   │   │   ├── llm.py         # embeddings + chat completion
│   │   │   ├── vectorstore.py # Chroma add/query/delete
│   │   │   └── pipeline.py    # ingest + answer orchestration
│   │   └── routers/
│   │       ├── documents.py   # upload / list / delete
│   │       └── chat.py        # ask / history / clear
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    └── package.json
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then edit .env with your API key
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

**Configuring the LLM provider** (in `.env`):

- **OpenAI**: set `OPENAI_API_KEY`, leave `OPENAI_BASE_URL` empty.
- **Ollama (free/local)**: set `OPENAI_BASE_URL=http://localhost:11434/v1`,
  `OPENAI_API_KEY=ollama`, `CHAT_MODEL=llama3.1`,
  `EMBEDDING_MODEL=nomic-embed-text`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to the backend.

## How to use

1. Click **+ Add document** and upload a PDF or text file.
2. Wait for indexing (it chunks + embeds the file).
3. Ask a question in the chat. The assistant retrieves the most relevant chunks
   and answers with `[#]` citations + a sources panel.

## API reference

| Method | Endpoint                  | Description               |
| ------ | ------------------------- | ------------------------- |
| GET    | `/api/health`             | Health check              |
| GET    | `/api/documents`          | List indexed documents    |
| POST   | `/api/documents`          | Upload + index a document |
| DELETE | `/api/documents/{id}`     | Delete a document         |
| POST   | `/api/chat`               | Ask a question            |
| GET    | `/api/chat/history`       | Get chat history          |
| DELETE | `/api/chat/history`       | Clear chat history        |

## Roadmap / next steps

- Streaming responses (token-by-token)
- Per-document chat scoping / collections
- Re-ranking retrieved chunks
- Auth + multi-user workspaces
