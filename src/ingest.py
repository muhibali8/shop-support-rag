"""
ingest.py  --  shop ka data parho, chunks banao, embeddings banao, Chroma mein rakho.

Ye script sirf EK BAAR chalti hai (ya jab shop ka data badle).
Chalane ka tareeqa (project folder ke andar se):
    python src/ingest.py
"""

import re
from pathlib import Path

DATA_FILE = Path("data/zaras_boutique.md")
DB_DIR = "chroma_db"              # vector DB yahan save hoga
COLLECTION = "shop_chunks"
# Multilingual model: English + Urdu + Roman Urdu ke liye behtar
EMBED_MODEL = "intfloat/multilingual-e5-base"


def chunk_markdown(text: str) -> list[dict]:
    """
    Markdown ko headings ke hisaab se chunks mein todta hai.
    Har chunk ke shuru mein uska 'raasta' (jaise 'Products and Prices > Cotton Kurti Basic')
    lagate hain, taake chunk akela bhi samajh aa jaye.
    """
    chunks = []
    h2 = ""          # '## ' wali heading (bara section)
    h3 = ""          # '### ' wali heading (product wagera)
    buffer = []      # current chunk ki lines

    def flush():
        """Jama ki hui lines ko ek chunk bana kar list mein daal do."""
        body = "\n".join(buffer).strip()
        if body:
            title = " > ".join(t for t in (h2, h3) if t) or "About the shop"
            chunks.append({"title": title, "text": f"{title}\n{body}"})
        buffer.clear()

    for line in text.splitlines():
        if line.startswith("# "):            # sab se upar ka title, chhod do
            continue
        if line.startswith("## "):           # naya bara section
            flush()
            h2, h3 = line[3:].strip(), ""
        elif line.startswith("### "):        # naya product/sub-section
            flush()
            h3 = line[4:].strip()
        else:
            buffer.append(line)
    flush()

    # FAQ section mein har sawal ko alag chunk bana do
    final = []
    for c in chunks:
        if c["title"].startswith("Frequently Asked Questions"):
            final.extend(split_faq(c["title"], c["text"]))
        else:
            final.append(c)
    return final


def split_faq(title: str, text: str) -> list[dict]:
    """FAQ mein '**Sawal?**' ke baad jawab hota hai. Har pair ek chunk."""
    pairs = re.findall(r"\*\*(.+?)\*\*\s*\n(.+?)(?=\n\*\*|\Z)", text, flags=re.S)
    return [
        {"title": f"{title} > {q}", "text": f"{title}\nQ: {q}\nA: {a.strip()}"}
        for q, a in pairs
    ]


def main():
    # Bhari libraries yahan import karte hain taake chunking bina install ke bhi test ho sake
    import chromadb
    from sentence_transformers import SentenceTransformer

    text = DATA_FILE.read_text(encoding="utf-8")
    chunks = chunk_markdown(text)
    print(f"Total chunks: {len(chunks)}")

    # 1) Har chunk ko numbers (embedding) mein badlo
    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(["passage: " + c["text"] for c in chunks], normalize_embeddings=True, show_progress_bar=True)

    # 2) Chroma mein save karo (purana collection hata kar naya banate hain)
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.create_collection(COLLECTION)
    col.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        documents=[c["text"] for c in chunks],
        metadatas=[{"title": c["title"]} for c in chunks],
        embeddings=embeddings.tolist(),
    )
    print(f"Done. {len(chunks)} chunks '{DB_DIR}' mein save ho gaye.")


if __name__ == "__main__":
    main()
