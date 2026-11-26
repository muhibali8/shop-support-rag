# Shop Support RAG

A customer-support chatbot for small online sellers. Customers ask questions in **Roman Urdu or English**, and the bot answers **only from the seller's own shop information**, with the sources it used. If the answer is not in the data, it says so and points the customer to WhatsApp instead of guessing.

Built and tested first on a fictional shop ("Zara's Boutique"). To use it for another seller, only the data file changes.

**Live demo:** LIVE_LINK_YAHAN

## How it works

```
data/zaras_boutique.md
        |  chunk by headings (37 chunks)
        v
   embeddings  (intfloat/multilingual-e5-base)
        v
   ChromaDB  (vector search)
        |  customer question -> top 5 chunks
        v
   prompt + chunks  ->  Gemini  ->  answer + sources
```

1. **Ingest** (`src/ingest.py`): the shop's Markdown file is split by headings into small chunks. Each chunk keeps its heading path (for example `Delivery > Delivery Charges`) so it makes sense on its own.
2. **Retrieve** (`src/retrieve.py`): the question is embedded and the 5 closest chunks are fetched from ChromaDB.
3. **Answer** (`src/answer.py`): the chunks and the question go into a strict prompt (answer only from the context, stay on the question, offer alternatives, say "no information" when missing). Gemini writes the reply.
4. **UI** (`app.py`): a Streamlit page that shows the answer and the sources.

No model is trained. The embedding model only finds relevant text, and the LLM writes the answer from that text.

## Results

Evaluated on 30 hand-written questions (Roman Urdu and English), including 3 questions whose answers are **not** in the data. Answers were graded by hand.

**Retrieval** (27 answerable questions, did the right chunk come back?)

| Metric | Score |
|---|---|
| Hit@1 | 22 / 27 (81%) |
| Hit@3 | 26 / 27 (96%) |
| Hit@5 | 27 / 27 (100%) |

**Answer quality** (first prompt, all 30 questions)

| Outcome | Count |
|---|---|
| Fully correct | 26 |
| Correct with minor issues (extra info, missing alternatives, partial info) | 4 |
| Wrong | 0 |
| Unanswerable questions handled safely (no made-up answer) | 3 / 3 |

**Prompt v2** was written to fix the minor issues. On an 8-question subset it improved 3 answers (less off-topic detail, alternatives offered, partial information handled) with no regressions, and the unanswerable questions still declined correctly.

| Question | Before | After |
|---|---|---|
| How many days does delivery take to Lahore? | Added unrelated dispatch time | Only the delivery time |
| Do you accept credit cards? | "No" only | "No", plus the payment options that are accepted |
| Kya Eid ki sale mein abaya 50% off hogi? | "No information" | Says Eid sales exist, 50% is not confirmed, contact WhatsApp |

**Honest caveats**
- The retrieval settings (chunk splits, embedding model, `k`) were tuned while looking at these same questions, so the retrieval numbers are optimistic. A fresh held-out question set is still to be written.
- Prompt v2 was checked on 8 questions, not all 30, and LLM output varies between runs.
- Grading was done by hand, not by an automatic judge.

## Project structure

```
app.py                      Streamlit UI
src/
  ingest.py                 build chunks, embeddings, ChromaDB
  retrieve.py               question -> top-k chunks
  answer.py                 prompt + Gemini call (with retries)
data/zaras_boutique.md      sample shop information
eval/
  test_questions.json       30 test questions with expected answers
  run_eval.py               run all questions, save answers (resumable)
  answers_v1.json           answers with the first prompt
  answers_v2_subset.json    before/after for prompt v2
requirements.txt
```

## Run it locally

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"        # Windows: set GEMINI_API_KEY=your-key
python src/ingest.py                    # builds chroma_db (once)
streamlit run app.py
```

Run the evaluation (uses Gemini quota, so it saves after every answer and can resume):

```bash
python eval/run_eval.py
```

On Streamlit Cloud the key goes into the app's Secrets, and `app.py` builds `chroma_db` on first start.

## Known limitations

- **Latency:** retrieval takes about 0.2 s, but the Gemini call takes roughly 6 s on average and can be slower when the model is under heavy demand (503 errors). The app retries and then shows a friendly message.
- **Free tier:** the Gemini free tier has a daily request limit.
- **Small data:** the sample shop has 37 chunks. Behaviour on a large catalogue is untested.
- **Retrieval noise:** with `k=5`, a few unrelated chunks come back with the correct one. The prompt tells the model to ignore them, which works on the test set but is not guaranteed.

## Roadmap

- Fresh held-out question set for an unbiased score
- Reranking and query translation (Roman Urdu to English) for retrieval
- Faster responses (streaming, lower model "thinking" time)
- Test on a real seller's data
- Tests and a FastAPI endpoint
