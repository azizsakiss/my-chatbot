import streamlit as st
import google.generativeai as genai
import numpy as np
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Store Support", page_icon="🛍️")

# 👇👇👇 CONFIGURATION 👇👇👇
DOLIBARR_API_KEY = "kZbDKDivuFZQAAz"
DOLIBARR_API_URL = "http://localhost/dolibarr/htdocs/api/index.php" 
# 👆👆👆👆👆👆👆👆👆👆👆👆

# --- 2. KNOWLEDGE BASE ---
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = [
        {"id": 1, "content": "We ship all domestic orders via FedEx. Delivery takes 3-5 business days."},
        {"id": 2, "content": "Returns are accepted within 30 days of purchase if they are unused."},
        {"id": 3, "content": "We accept Visa, Mastercard, PayPal, and Apple Pay."},
        {"id": 4, "content": "Support email: help@mystore.com. Phone: 1-800-555-0199."},
        {"id": 5, "content": "Our store is open Mon-Fri from 9 AM to 5 PM EST."}
    ]

# --- 3. HELPER: AI EXTRACTOR ---
def extract_product_name_with_ai(user_query):
    try:
        try:
            my_key = st.secrets["GEMINI_KEY"]
        except:
            my_key = "AIzaSy..." 
            
        genai.configure(api_key=my_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        prompt = f"""
        Extract the CORE product name or ID from the user's sentence.
        Rules:
        1. Remove adjectives like "cool", "nice", "my", "the", "this", "on stock".
        2. Return ONLY the product name.
        User sentence: "{user_query}"
        """
        response = model.generate_content(prompt)
        clean_name = response.text.strip()
        st.toast(f"🤖 Extracted: '{clean_name}'")
        return clean_name
    except:
        return user_query 

# --- 4. DOLIBARR TOOL (Safe Search) ---
def check_dolibarr_stock(product_keyword):
    headers = {"DOLAPIKEY": DOLIBARR_API_KEY}
    clean_keyword = product_keyword.replace('"', '').replace("'", "").strip()
    
    # 👇 SAFE FILTER: Simple Label search to avoid Error 400
    sql = f"t.label:like:'%{clean_keyword}%'"
    params = {"sqlfilters": sql, "limit": 5}
    
    try:
        response = requests.get(f"{DOLIBARR_API_URL}/products", headers=headers, params=params)
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list) and len(products) > 0:
                result_text = "Found in Dolibarr:\n"
                for p in products:
                    result_text += f"- {p['label']} (Ref: {p['ref']}) | Stock: {p['stock_reel']} | Price: {p['price']}\n"
                return result_text
            else:
                return f"I searched for '{clean_keyword}' and found 0 results."
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- 5. VECTORIZATION (CLOUD VERSION) ---
def get_best_match(query):
    try:
        try:
            my_key = st.secrets["GEMINI_KEY"]
        except:
            my_key = "AIzaSy..."
        
        genai.configure(api_key=my_key)
        
        # Use Google for math instead of local CPU (Prevents crashing)
        docs = [d['content'] for d in st.session_state.knowledge_base]
        doc_vectors = genai.embed_content(
            model="models/text-embedding-004",
            content=docs,
            task_type="retrieval_document"
        )['embedding']

        query_vector = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )['embedding']

        # Dot product similarity
        scores = []
        for doc_vec in doc_vectors:
            score = np.dot(query_vector, doc_vec)
            scores.append(score)
            
        best_idx = np.argmax(scores)
        return docs[best_idx], scores[best_idx]
        
    except Exception as e:
        # Fallback if embeddings fail
        return st.session_state.knowledge_base[0]['content'], 0.0

# --- 6. GENERATION ---
def generate_answer(query):
    try:
        try:
            my_key = st.secrets["GEMINI_KEY"]
        except:
            my_key = "AIzaSy..." 
        
        genai.configure(api_key=my_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        # Routing
        if any(k in query.lower() for k in ["stock", "price", "how many", "available", "cost", "find", "check"]):
            product_keyword = extract_product_name_with_ai(query)
            erp_data = check_dolibarr_stock(product_keyword)
            
            prompt = f"""
            You are a warehouse assistant.
            User asked: "{query}"
            Product searched: "{product_keyword}"
            DATA FROM ERP: {erp_data}
            Answer politely.
            """
        else:
            best_text, score = get_best_match(query)
            # Threshold for cloud embeddings
            if score > 0.6:
                prompt = f"Context: {best_text}\nQuestion: {query}\nAnswer politely."
            else:
                prompt = f"Chat History: ...\nUser said: {query}\nReply politely."

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Error: {str(e)}"

# --- 7. UI ---
st.title("🏭 Ultimate AI Agent")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I can check stock. Try 'Check stock for Jacket'."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask me..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking..."):
            response = generate_answer(prompt)
            st.write(response)
            
    st.session_state.messages.append({"role": "assistant", "content": response})