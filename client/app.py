# client/app.py
import streamlit as st
import requests

API = "http://localhost:8000"

st.set_page_config(page_title="Ready Tensor Publication Explorer", page_icon="📚")
st.title("Ready Tensor Publication Explorer")

# Sidebar: choose publication
pubs = requests.get(f"{API}/publications").json()["items"]
pub_map = {p["title"]: p["id"] for p in pubs}
choice = st.sidebar.selectbox("Focus on a publication (optional):", ["All"] + list(pub_map.keys()))
pub_id = None if choice == "All" else pub_map[choice]

# Chat
if "history" not in st.session_state:
    st.session_state.history = []

for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.markdown(msg)

q = st.chat_input("Ask about a publication (e.g., 'What’s this about?', 'What models were used?')")
if q:
    st.session_state.history.append(("user", q))
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            res = requests.post(f"{API}/chat", json={"query": q, "publication_id": pub_id}).json()
            st.markdown(res["answer"])
            st.caption("Sources: " + ", ".join({f"{s['title']} – {s['section']}" for s in res["sources"]}))
    st.rerun()
