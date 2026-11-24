"""
run_eval.py  --  test_questions.json ke sawal answer() se chalao,
jawab file mein save karo (resumable).

Chalane ka tareeqa (project folder ke andar se):
    python eval/run_eval.py
"""

import json
import os
import sys
import time

sys.path.insert(0, "src")
from answer import answer, LLM_MODEL

TESTS_FILE = "eval/test_questions.json"
OUT_FILE = "eval/answers_final.json"

with open(TESTS_FILE, encoding="utf-8") as f:
    tests = json.load(f)

print(f"{len(tests)} sawal load hue")


if os.path.exists(OUT_FILE):
    with open(OUT_FILE, encoding="utf-8") as f:
        results = json.load(f)
else:
    results = []

print(len(results))


def save_results():
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

done = {r["id"] for r in results}

for t in tests:
    if t["id"] in done:
        continue                            # unhein chhor do
    try:
        reply, sources = answer(t["question"])
    except RuntimeError:
        print(f"Sawal #{t['id']} par ruk gaya, thori der baad yahi script dobara chalao")
        break
    results.append({
        "id": t["id"], "lang": t["lang"], "question": t["question"],
        "expected": t["expected_answer"], "answer": reply,
        "sources": sources, "answerable": t["answerable"], "model": LLM_MODEL
    })
    save_results()
    print(f"#{t['id']} ho gaya ({len(results)}/{len(tests)})")
    time.sleep(10)                          # quota ke liye thora rukna

print(len(results), "jawab save ho gaye")