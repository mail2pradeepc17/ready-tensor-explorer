# Ready Tensor Publication Explorer

Conversational assistant to explore Ready Tensor publications using natural language.

## Features
- Summarize publications
- List models/tools used
- Show limitations/assumptions
- Retrieval-Augmented Generation (RAG) with semantic search

## Setup (Windows)

### 1. Clone the repo
```powershell
git clone https://github.com/<your-username>/ready-tensor-explorer.git
cd ready-tensor-explorer

### 2. Setup the env
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy configs\settings.example.env .env

### 3. Edit env
```powershell
# Edit .env to add your OpenAI API key

### 4. Execute commands
```powershell
python ingest\ingest.py
uvicorn server.main:app --reload --port 8000
