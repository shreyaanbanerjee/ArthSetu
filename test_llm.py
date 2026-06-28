import json
from config import GROQ_API_KEY, SUTRADHAR_MODEL
from agents.sutradhar import SYSTEM_PROMPT
from groq import Groq

client = Groq(api_key=GROQ_API_KEY)
try:
    response = client.chat.completions.create(
        model=SUTRADHAR_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Return JSON with key synthesis only."}
        ],
        temperature=0.3,
        max_tokens=1000,
        response_format={"type": "json_object"},
    )
    print("SUCCESS")
    print(response.choices[0].message.content)
except Exception as e:
    import traceback
    traceback.print_exc()
