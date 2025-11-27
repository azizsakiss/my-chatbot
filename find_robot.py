import google.generativeai as genai

# --- YOUR WORKING KEY ---
my_key = "AIzaSyD43QL6CUhE5oGXjLFMYaJjFbyqA_KFafY"
genai.configure(api_key=my_key)

print("Searching for available robots...")

try:
    # List all models available to you
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ FOUND: {m.name}")
            
            # Try to test it immediately
            try:
                test_model = genai.GenerativeModel(m.name)
                test_model.generate_content("Hi")
                print(f"   └── WORKED! Use this name: '{m.name}'")
            except:
                print("   └── (This one failed)")

except Exception as e:
    print("Error:", e)