import sys

import streamlit as st

sys.path.insert(0, "src")

try:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not os.path.exists("chroma_db"):
    with st.spinner("Pehli baar setup ho raha hai, 1-2 minute lagenge..."):
        import ingest
        ingest.main()
        
from answer import answer

st.title("Zara's Boutique Support")

question = st.text_input("Apna sawal likhein")

if st.button("Poochho") and question:
    with st.spinner("Jawab dhoondh raha hoon..."):
        try:
            reply, sources = answer(question)
        except RuntimeError:
            st.error("Abhi jawab nahi de sakta, thori der baad dobara koshish karein.")
            st.stop()
    st.write(reply)
    with st.expander("Sources dekhein"):
        for s in sources:
            st.write("- " + s)
