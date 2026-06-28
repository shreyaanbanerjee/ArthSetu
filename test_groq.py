import json
from config import GROQ_API_KEY
from groq import Groq
client = Groq(api_key=GROQ_API_KEY)
try:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Return {\"test\": 123}"}],
        temperature=0.1,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    print("SUCCESS", response.choices[0].message.content)
except Exception as e:
    print("ERROR:", repr(e))
