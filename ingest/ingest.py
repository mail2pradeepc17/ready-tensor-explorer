
---

### 5. `ingest/ingest.py`
```python
import os, json, uuid
from pathlib import Path
from unstructured.partition.auto import partition
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

DATA_DIR = Path("data/raw")
NORM_DIR = Path("data/normalized")
CHROMA_DIR = "data/chroma"

EMB = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-large"
)

def parse_file(path: Path):
    elements = partition(filename=str(path))
    sections = []
    for el in elements:
        txt = el.text.strip()
        if not txt:
            continue
        heading = getattr(el, "metadata", {}).get("category") or "Body"
        sections.append({"heading": str(heading), "text": txt})
    return {
        "id": str(uuid.uuid4()),
        "title": path.stem,
        "sections": sections
    }

def chunk_sections(sections, chunk_chars=3500, overlap=400):
    chunks = []
    for s in sections:
        text = s["text"]
        start = 0
        while start < len(text):
            end = min(start + chunk_chars, len(text))
            chunk = text[start:end]
            chunks.append({"heading": s["heading"], "text": chunk})
            start = end - overlap
            if start < 0:
                start = 0
    return chunks

def main():
    NORM_DIR.mkdir(parents=True, exist_ok=True)
    client = PersistentClient(CHROMA_DIR)
    col = client.get_or_create_collection("readytensor_pubs", embedding_function=EMB)

    for f in DATA_DIR.glob("**/*"):
        if f.is_dir():
            continue
        doc = parse_file(f)
        with open(NORM_DIR / f"{doc['id']}.json", "w", encoding="utf-8") as fp:
            json.dump(doc, fp, ensure_ascii=False, indent=2)

        chunks = chunk_sections(doc["sections"])
        ids, texts, metas = [], [], []
        for i, ch in enumerate(chunks):
            cid = f"{doc['id']}::{i}"
            ids.append(cid)
            texts.append(ch["text"])
            metas.append({
                "publication_id": doc["id"],
                "title": doc["title"],
                "section": ch["heading"]
            })
        if texts:
            col.add(ids=ids, documents=texts, metadatas=metas)

if __name__ == "__main__":
    main()