"""
answer.py  --  sawal lo, chunks dhoondo, Gemini se jawab likhwao.
"""

import os
import time

from google import genai
from google.genai import errors
from retrieve import retrieve

LLM_MODEL = "gemini-3.5-flash"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def ask_llm(prompt, model=None, retries=6):
  model = model or LLM_MODEL

  for i in range (retries):
    try:
      return client.models.generate_content(model=model, contents=prompt).text

    except errors.ServerError as e:
      print(f"Try {i+1} fail (server): {str(e)[:60]}")

    except errors.ClientError as e:
      if e.code !=429:
        raise
      if "PerDay" in str(e):                                  # naya
        raise RuntimeError("Rozana (per day) ki limit khatam")
      print(f"Try {i+1} fail (rate limit)")

    time.sleep(min(60, 2 ** (i + 1)))                 # 2, 4, 8, 16, 32, 60 second

  raise RuntimeError("LLM ne kai koshishon ke baad bhi jawab nahi diya")
  
  
def build_prompt(question, retrieved):
    context = "\n\n".join(
        f"[{i}] {doc}" for i, (meta, doc) in enumerate(retrieved, start=1)
    )
    return f"""Tum Zara's Boutique ke customer support assistant ho.

Qaide:
1. Sirf neeche diye gaye CONTEXT se jawab do. Apni taraf se kuch mat banao.
2. Sirf wohi batao jo customer ne poocha. Extra ya be-talluq maloomat mat do.
3. Agar customer ki cheez available nahi hai (jaise ye payment method nahi), to CONTEXT mein jo mutabadil (options) hain wo bata do.
4. Agar sawal ka kuch hissa CONTEXT se mil jaye to wo batao, aur jo hissa na mile uske liye kaho ke maloomat nahi aur seller se WhatsApp par rabta karein. Agar bilkul kuch na mile to sirf kaho ke maloomat nahi aur WhatsApp par rabta karein.
5. Customer ki zubaan mein jawab do (Roman Urdu ya English). Plain text likho, bold ya ** jaise Markdown symbols mat istemal karo.
6. Jawab chhota aur saaf rakho.

CONTEXT:
{context}

CUSTOMER KA SAWAL: {question}

JAWAB:"""


def answer(question, k=8):
    retrieved = retrieve(question, k)
    prompt = build_prompt(question, retrieved)
    reply = ask_llm(prompt)
    sources = [meta["title"] for meta, doc in retrieved]
    return reply, sources
