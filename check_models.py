import google.generativeai as genai
import os

# --- I PASTED YOUR KEY FROM THE SCREENSHOT HERE ---
api_key = "AIzaSyARMh29QgLK5Ku0dmVZISErsSe-BOSs1Kc" 

try:
    genai.configure(api_key=api_key)
    print("Connecting to Google AI...")
    
    print("\nAVAILABLE MODELS FOR YOUR KEY:")
    print("-" * 30)
    count = 0
    # List all models and print the ones that support 'generateContent'
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            count += 1
            
    if count == 0:
        print("❌ No models found. Key might be restricted.")
    else:
        print("-" * 30)
        print(f"✅ Found {count} active models.")
        print("Please copy one of the names above (e.g. 'models/gemini-1.5-flash') into your app.")
        
except Exception as e:
    print("\n❌ ERROR:")
    print(e)