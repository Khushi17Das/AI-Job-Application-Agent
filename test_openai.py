import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load environment variables from .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

print(f"Checking API Key: {api_key[:8]}... (Truncated for security)")

if not api_key or api_key == "your_openai_api_key_here":
    print("❌ ERROR: Please paste your real OPENAI_API_KEY in the .env file!")
    exit(1)

try:
    # 2. Initialize client
    client = OpenAI(api_key=api_key)

    # 3. Test API connection
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": "Respond with exactly: 'OpenAI API is working successfully!'"}
        ]
    )

    print("✅ Success! Response from OpenAI:")
    print(response.choices[0].message.content)

except Exception as e:
    print(f"❌ API Test Failed: {e}")
