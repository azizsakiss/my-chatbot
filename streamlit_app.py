import streamlit as st
import time
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="Chatbot", page_icon="🧠")

# --- 1. LOAD RETRIEVAL MODEL ---
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedding_model = load_embedding_model()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am a Chatbot. Ask me anything about the store!"}
    ]

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = [
        {"id": 1, "topic": "Shipping", "content": "We ship all domestic orders via FedEx. Delivery takes 3-5 business days."},
        {"id": 2, "topic": "Returns", "content": "You can return items within 30 days of purchase if they are unused."},
        {"id": 3, "topic": "Payment", "content": "We accept Visa, Mastercard, PayPal, and Apple Pay."},
        {"id": 4, "topic": "Contact", "content": "Email us at support@mystore.com."},
        {"id": 5, "topic": "Hours", "content": "We are open Mon-Fri from 9 AM to 5 PM EST."}
    ]

# --- 2. VECTORIZATION ---
def update_embeddings():
    corpus = [doc['content'] for doc in st.session_state.knowledge_base]
    embeddings = embedding_model.encode(corpus)
    return embeddings, corpus

if "doc_embeddings" not in st.session_state:
    embeddings, corpus = update_embeddings()
    st.session_state.doc_embeddings = embeddings
    st.session_state.corpus = corpus

# --- 3. GENERATION (The LLM Engine) ---
def generate_with_gemini(context, query):
    try:
        # --- HARDCODED KEY FIX ---
        # We are putting the key directly here to bypass sidebar issues
        my_key = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=my_key)
        
        model = genai.GenerativeModel('models/gemini-2.5-flash') 
        
        prompt = f"""
        You are a helpful customer support agent.
        Use the following Context to answer the User's Question.
        If the answer is not in the Context, say "I don't know".
        
        Context:
        {context}
        
        User's Question:
        {query}
        
        Answer (be polite and concise):
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

# --- MAIN LOGIC ---
def run_rag_pipeline(query):
    # STEP A: RETRIEVAL
    query_embedding = embedding_model.encode([query])
    similarities = cosine_similarity(query_embedding, st.session_state.doc_embeddings)
    best_idx = np.argmax(similarities)
    best_score = similarities[0][best_idx]
    
    if best_score < 0.3:
        return "I'm sorry, I don't have information on that in my database."
    
    found_doc = st.session_state.corpus[best_idx]
    
    # STEP B: GENERATION (Always runs now)
    return generate_with_gemini(found_doc, query)


# --- UI: Sidebar ---
with st.sidebar:
    st.header("🧠 Teach the Bot")
    with st.form("train_form"):
        new_topic = st.text_input("Topic")
        new_content = st.text_area("Fact")
        if st.form_submit_button("Add to Brain"):
            st.session_state.knowledge_base.append({"id": len(st.session_state.knowledge_base), "topic": new_topic, "content": new_content})
            embeddings, corpus = update_embeddings()
            st.session_state.doc_embeddings = embeddings
            st.session_state.corpus = corpus
            st.success("Memory Updated!")

# --- UI: Chat Interface ---
st.title("🧠 Full RAG Chatbot")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_rag_pipeline(prompt)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})