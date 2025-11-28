import streamlit as st
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests

st.set_page_config(page_title="Store Support", page_icon="🛍️")

# --- CONFIGURATION ---
DOLIBARR_API_KEY = "kZbDKDivuFZQAAz"
DOLIBARR_API_URL = "http://localhost/dolibarr/htdocs/api/index.php" 

@st.cache_resource
def load_models():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedding_model = load_models()

# --- HELPER: AI EXTRACTOR ---
def extract_product_name_with_ai(user_query):
    try:
        try:
            my_key = st.secrets["GEMINI_KEY"]
        except:
            # Paste your NEW working key here if testing locally
            my_key = "PASTE_YOUR_NEW_KEY_HERE" 
            
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

# --- DOLIBARR TOOL (Diagnostic) ---
def check_dolibarr_stock(product_keyword):
    headers = {"DOLAPIKEY": DOLIBARR_API_KEY}
    clean_keyword = product_keyword.replace('"', '').replace("'", "").strip()
    
    # 👇 SIMPLIFIED SEARCH (Less likely to cause Error 400)
    # We search ONLY the Label (Name) first.
    sql = f"(t.label:like:'%{clean_keyword}%')"
    
    params = {
        "sqlfilters": sql,
        "limit": 10
    }
    
    try:
        response = requests.get(f"{DOLIBARR_API_URL}/products", headers=headers, params=params)
        
        # 👇 DEBUG: Show the EXACT Link that failed
        if response.status_code != 200:
            st.error(f"⚠️ Technical Error: {response.status_code}")
            st.code(f"Failed URL: {response.url}") # This will show us the bad link
            
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list) and len(products) > 0:
                result_text = "Found in Dolibarr:\n"
                for p in products:
                    result_text += f"- {p['label']} (Ref: {p['ref']}) | Stock: {p['stock_reel']}\n"
                return result_text
            else:
                return f"I searched Dolibarr for '{clean_keyword}' but found 0 results."
        else:
            return f"Error {response.status_code}: Dolibarr rejected the request."
            
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- MAIN LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello!"}]

# (Vectorization logic skipped for brevity, using direct routing for testing)

st.title("🛍️ Store Support")

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask me..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Checking..."):
            
            # Direct Test Logic
            if "stock" in prompt.lower() or "check" in prompt.lower():
                keyword = extract_product_name_with_ai(prompt)
                data = check_dolibarr_stock(keyword)
                
                # Gemini generates the final answer
                try:
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    final_answer = model.generate_content(f"User asked: {prompt}. Data: {data}. Answer politely.").text
                    st.write(final_answer)
                    response = final_answer
                except:
                    st.write(data)
                    response = data
            else:
                # Simple Chit Chat
                try:
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    response = model.generate_content(f"Reply to this chat: {prompt}").text
                    st.write(response)
                except:
                    st.write("I'm having trouble thinking right now.")
                    response = "Error."

    st.session_state.messages.append({"role": "assistant", "content": response})