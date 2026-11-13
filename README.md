# Braylliant AI — Phase 1 starter

A simple, web-based AI chat assistant for BRAYLLIANT IT SOLUTIONS PRIVATE LIMITED.
It uses Streamlit for the chat interface and the Google Gemini API for responses.

## What Phase 1 includes
- Chat-style web interface
- Gemini API connection
- Braylliant-specific system instructions
- Conversation history for the current browser session
- API key stored as a deployment secret, not in source code

## Important limitations
This is a Phase 1 prototype, not a finished ChatGPT/Gemini competitor.
It does not yet have live web search, long-term memory, user accounts,
automated company monitoring, CRM write access, or email sending.
Do not use it for confidential client or personal information.
Free API access has model and rate limits. Check the current terms and pricing.

## Deploy free using Streamlit Community Cloud

### Step 1 — Create the Gemini API key
1. Open https://aistudio.google.com/app/apikey
2. Sign in with your Google account.
3. Create an API key.
4. Copy it privately. Do not send it to anyone or commit it to GitHub.

### Step 2 — Create a GitHub repository
1. Open https://github.com and sign in or create an account.
2. Create a new repository named `braylliant-ai`.
3. For the simplest first setup, set it to **Private** if your account and Streamlit connection support private repositories.
4. Upload `app.py` and `requirements.txt` from this folder.
5. Do not upload a real API key or a real `secrets.toml` file.

### Step 3 — Deploy on Streamlit
1. Open https://share.streamlit.io
2. Sign in with GitHub and authorise Streamlit.
3. Choose **Create app**.
4. Select your `braylliant-ai` repository, branch `main`, and main file `app.py`.
5. Open **Advanced settings → Secrets**.
6. Paste this, replacing the placeholder with your actual key:

   GEMINI_API_KEY = "your-real-api-key"

7. Click **Deploy** and wait for the app to start.
8. Your app will receive a `*.streamlit.app` URL.

### Step 4 — Test
Ask: `Draft a professional introduction email for an AI data annotation buyer.`
Check that the response is relevant and does not claim that it performed live web research.

## Run locally (optional)
1. Install Python 3.11 or newer.
2. Open a terminal in this folder.
3. Run:
   `python -m venv .venv`
4. Activate the environment:
   Windows PowerShell: `.venv\Scripts\Activate.ps1`
5. Run:
   `pip install -r requirements.txt`
6. Create `.streamlit/secrets.toml` containing:
   `GEMINI_API_KEY = "your-real-api-key"`
7. Run:
   `streamlit run app.py`

## Model selection
The default model name is `gemini-3.8-flash`. Model availability can vary by account, region and API release.
If unavailable, check Google AI Studio's current model list and enter an available model name in the sidebar.

## Security
- Keep the repository private where practical.
- Never commit API keys.
- Do not put API keys in browser-side code.
- Add login/access controls before sharing with employees or customers.
- Review Google's current API data-use terms before entering business-sensitive information.
