import google.generativeai as genai

# --- PASTE YOUR NEW KEY HERE ---
my_new_key = "AIzaSyD43QL6CUhE5oGXjLFMYaJjFbyqA_KFafY" # <--- Paste the new key inside these quotes

print(f"Testing Key: {my_new_key[:10]}...")

try:
    genai.configure(api_key=my_new_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    response = model.generate_content("Are you working?")
    print("\n✅ SUCCESS! The key is valid.")
    print(f"AI Response: {response.text}")
except Exception as e:
    print("\n❌ FAILURE. The key is still wrong.")
    print(f"Error details: {e}")