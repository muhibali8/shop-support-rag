"""
retrieve.py  --  sawal do, sab se milte julte chunks wapas lo.
"""

import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION = "shop_chunks"
EMBED_MODEL = "intfloat/multilingual-e5-base"

model = SentenceTransformer(EMBED_MODEL)
client = chromadb.PersistentClient(path=DB_DIR)
col = client.get_collection(COLLECTION)

def retrieve(question, k=5):
    q = model.encode(["query: " + question], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=q, n_results=k)
    return list(zip(res["metadatas"][0], res["documents"][0]))