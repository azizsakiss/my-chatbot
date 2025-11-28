import streamlit as st
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Store Support", page_icon="🛍️")

# 👇👇👇 CONFIGURATION 👇👇👇
DOLIBARR_API_KEY = "kZbDKDivuFZQAAz"
# Try removing 'index.php' if your server uses clean URLs, but keep it for now.
DOLIBARR_API_URL = "http://localhost/dolibarr/htdocs/api/index.php" 
# 👆👆👆👆👆👆👆👆👆👆👆👆

@st.cache_resource
def load_models():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedding_model = load_models()

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
            my_key = "AIzaSy..." # Fallback key if needed
            
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
        st.toast(f"🤖 AI extracted: '{clean_name}'")
        return clean_name
    except:
        return user_query

# --- 4. DOLIBARR TOOL (Deep Debug) ---
def check_dolibarr_stock(product_keyword):
    headers = {"DOLAPIKEY": DOLIBARR_API_KEY}
    clean_keyword = product_keyword.replace('"', '').replace("'", "").strip()
    
    # URL Construct
    url = f"{DOLIBARR_API_URL}/products"
    
    # Params
    sql = f"(t.ref:like:'%{clean_keyword}%') OR (t.label:like:'%{clean_keyword}%')"
    params = {
        "sqlfilters": sql,
        "limit": 5
    }
    
    # DEBUG: Show connection details on screen
    st.info(f"📡 **CONNECTING...**")
    st.write(f"**URL:** `{url}`")
    st.write(f"**Key:** `{DOLIBARR_API_KEY[:5]}...`")
    st.write(f"**Filter:** `{sql}`")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # DEBUG: Show Status Code
        st.write(f"**Status Code:** `{response.status_code}`")
        
        if response.status_code == 200:
            try:
                products = response.json()
                # DEBUG: Show Raw JSON
                st.expander("View Raw JSON Data").json(products)
                
                if isinstance(products, list) and len(products) > 0:
                    result_text = "Found in Dolibarr:\n"
                    for p in products:
                        result_text += f"- {p['label']} (Ref: {p['ref']}) | Stock: {p['stock_reel']}\n"
                    return result_text
                else:
                    return f"Search successful (200 OK), but list was empty for '{clean_keyword}'."
            except Exception as json_err:
                return f"❌ JSON Error: Could not read response. {str(json_err)}"
                
        elif response.status_code == 404:
             return f"❌ Error 404: The URL is wrong. Verify 'api/index.php'"
        else:
            return f"❌ API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        # THIS IS THE MOST IMPORTANT PART
        return f"🔥 CRITICAL CONNECTION ERROR: {type(e).__name__} - {str(e)}"

# --- 5. GENERATION ---
def generate_answer(query):
    try:
        try:
            my_key = st.secrets["GEMINI_KEY"]
        except:
            my_key = "AIzaSy..." 
        
        genai.configure(api_key=my_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        if any(k in query.lower() for k in ["stock", "price", "check"]):
            product_keyword = extract_product_name_with_ai(query)
            erp_data = check_dolibarr_stock(product_keyword)
            
            # Show the raw error result in a big red box
            if "❌" in erp_data or "🔥" in erp_data:
                st.error(erp_data)

            prompt = f"""
            User asked: "{query}"
            DATA FROM ERP: {erp_data}
            Answer politely.
            """
        else:
            best_text, _ = get_best_match(query)
            prompt = f"Context: {best_text}\nQuestion: {query}\nAnswer politely."

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Error: {str(e)}"

# --- 6. UI ---
st.title("🛍️ Store Support ")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! how can I help you today."}]

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