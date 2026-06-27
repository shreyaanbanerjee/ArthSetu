# ArthSetu

Deterministic multi-agent financial literacy platform with FastAPI, Twilio WhatsApp, Telegram, and a Next.js PWA.

## Assumptions

- WhatsApp uses Twilio Sandbox or an approved Twilio WhatsApp sender.
- NPCI, UDIR, and RBI Sachet are explicit simulation/report-packet adapters unless official credentials are provided.
- Bhashini is optional and falls back to local speech transcription when possible.
- Groq and Gemini keys are optional for booting; Groq enables richer classification and synthesis.

## Backend Setup

```powershell
cd "D:\arthsetu project\arthsetu"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add:

```env
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

Run the API:

```powershell
uvicorn main:app --reload --port 8000
```

Test:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/chat -ContentType "application/json" -Body '{"user_id":"demo-user","message":"I got a KYC OTP link. Is it safe?"}'
```

## Twilio WhatsApp

Set the Twilio WhatsApp Sandbox inbound webhook to:

```text
https://YOUR_PUBLIC_URL/api/v1/webhook/whatsapp/twilio
```

For local testing, use ngrok or a similar tunnel:

```powershell
ngrok http 8000
```

## Frontend Setup

```powershell
cd "D:\arthsetu project\arthsetu\frontend"
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Docker

```powershell
cd "D:\arthsetu project\arthsetu"
Copy-Item .env.example .env
docker compose up --build
```

Ollama should run separately if you want local Bodhak/LlamaGuard models.
