import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

EMB = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai.api_key,
    model_name="text-embedding-3-large"
)

client = PersistentClient("data/chroma")
col = client.get_or_create_collection("readytensor_pubs", embedding_function=EMB)
app = FastAPI(title="Ready Tensor Publication Explorer")

def classify_intent(q: str) -> str:
    ql = q.lower()
    if any(k in ql for k in ["what is this", "summary", "about"]):
        return "summary"
    if any(k in ql for k in ["model", "tool", "framework"]):
        return "methods_tools"
    if any(k in ql for k in ["limitation", "assumption"]):
        return "limitations_assumptions"
    return "generic_qa"

def retrieve(query: str, k: int = 6, publication_id: Optional[str] = None):
    where = {"publication_id": publication_id} if publication_id else None
    res = col.query(query_texts=[query], n_results=k, where=where)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    return [{"text": d, "meta": m} for d, m in zip(docs, metas)]

SYSTEM_PROMPT = """You are Ready Tensor Publication Explorer.
Answer concisely using ONLY the provided context.
If unsure, say you don't have that detail.
Include inline citations like [Title – Section].
"""

def synthesize_answer(question: str, intent: str, contexts: List[dict]) -> str:
    context_str = ""
    for c in contexts:
        title = c["meta"].get("title", "Publication")
        section = c["meta"].get("section", "Body")
        context_str += f"\n[Source: {title} – {section}]\n{c['text']}\n"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\nIntent: {intent}"},
        {"role": "user", "content": f"Question: {question}\nContext:\n{context_str}"}
    ]
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
        max_tokens=400
    )
    return resp.choices[0].message["content"].strip()

class ChatRequest(BaseModel):
    query: str
    publication_id: Optional[str] = None
    top_k: int = 6

class ChatResponse(BaseModel):
    intent: str
    answer: str
    sources: List[dict]

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    intent = classify_intent(req.query)
    ctx = retrieve(req.query, k=req.top_k, publication_id=req.publication_id)
    answer = synthesize_answer(req.query, intent, ctx)
    sources = [{"title": c["meta"]["title"], "section": c["meta"]["section"]} for c in ctx]
    return ChatResponse(intent=intent, answer=answer, sources=sources)

@app.get("/publications")
def list_publications():
    import json, glob
    items = []
    for p in glob.glob("data/normalized/*.json"):
        with open(p, encoding="utf-8") as fp:
            j = json.load(fp)
            items.append({"id": j["id"], "title": j["title"]})
    return {"items": items}