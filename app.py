import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Braylliant AI",
    page_icon="✨",
    layout="wide",
)

SYSTEM_INSTRUCTION = """
You are Braylliant AI, the business and general-purpose AI assistant for
BRAYLLIANT IT SOLUTIONS PRIVATE LIMITED, based in Lucknow, India.

Your role:
- Help with general questions, writing, analysis, planning and problem solving.
- Support business development for AI data services and technology services.
- Relevant services include AI data annotation (image, video, audio and text),
  computer vision data, speech and voice data collection, transcription,
  translation and localization, multilingual datasets, LLM/GenAI evaluation,
  human-in-the-loop review, quality assurance, participant recruitment and
  field data collection.
- When discussing company capabilities, distinguish Braylliant's own record
  from the experience of partner company Arjitya Solutions. Never present
  another company's projects, clients or metrics as Braylliant's own.
- Do not invent clients, projects, prices, contacts, project availability,
  certifications, capacity or performance metrics.
- Clearly distinguish verified facts, assumptions and suggestions.
- When current information is needed, say that live web research is not
  connected in Phase 1. Do not pretend to have searched the internet.
- Do not send emails, contact companies, submit forms, spend money or change
  CRM records. Ask for approval before any external or consequential action.
- Write in clear, practical, professional language. Prefer concise answers.
"""

st.markdown("""
<style>
.block-container {max-width: 1050px; padding-top: 1.8rem;}
.hero {padding: 1.2rem 1.4rem; border-radius: 16px; background: linear-gradient(120deg,#101d36,#243d62); color: white; margin-bottom: 1rem;}
.hero h1 {color: white; margin: 0;}
.hero p {color: #d8e4f5; margin: .35rem 0 0 0;}
.small-note {color: #6b7280; font-size: .85rem;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("✨ Braylliant AI")
    st.caption("Phase 1 · AI chat assistant")
    st.divider()
    st.subheader("Connection")
    model = st.text_input("Gemini model", value="gemini-3.8-flash",
                          help="If this model is unavailable to your API key, try a model currently listed in Google AI Studio.")
    st.caption("Your API key is read from Streamlit Secrets and is not displayed here.")
    st.divider()
    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat = None
        st.rerun()
    st.markdown("**Coming in later phases**")
    st.caption("Company knowledge · Web research · Client monitoring · CRM · Daily automation")
    st.divider()
    st.markdown('<div class="small-note">Do not paste passwords, bank details, confidential client data or personal data into this prototype.</div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>Braylliant AI</h1>
  <p>Your AI assistant for thinking, research preparation and business support.</p>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = None

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = None

if not api_key:
    st.warning("Setup required: add your Gemini API key in Streamlit Secrets before chatting.")
    st.markdown("""
    1. Open Google AI Studio and create an API key.
    2. In your Streamlit app, open **Settings → Secrets**.
    3. Add the following secret (replace the placeholder with your actual key):
    """)
    st.code('GEMINI_API_KEY = "paste-your-key-here"', language="toml")
    st.info("Never paste your API key into this chat, a public GitHub file, or the app's source code.")
else:
    client = genai.Client(api_key=api_key)
    if st.session_state.chat is None:
        st.session_state.chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.5,
            ),
        )

    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input("Message Braylliant AI...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Braylliant AI is thinking..."):
                try:
                    response = st.session_state.chat.send_message(prompt)
                    answer = response.text or "I couldn't produce a text response. Please try again."
                except Exception as exc:
                    answer = (
                        "I couldn't reach the AI model. Check that your API key is valid, "
                        "the selected model is available to your account, and your free-tier "
                        f"quota has not been reached.\n\nTechnical detail: `{type(exc).__name__}: {exc}`"
                    )
                st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

if not st.session_state.messages and api_key:
    st.markdown("### Try asking")
    examples = [
        "Explain how Braylliant can approach international AI data companies.",
        "Draft a professional introduction email for an AI data annotation buyer.",
        "Create a checklist for evaluating a new voice data collection project.",
    ]
    cols = st.columns(3)
    for col, example in zip(cols, examples):
        with col:
            if st.button(example, use_container_width=True):
                st.session_state.pending_prompt = example
                st.rerun()

    if "pending_prompt" in st.session_state:
        pending = st.session_state.pop("pending_prompt")
        st.session_state.messages.append({"role": "user", "content": pending})
        with st.chat_message("user"):
            st.markdown(pending)
        with st.chat_message("assistant"):
            with st.spinner("Braylliant AI is thinking..."):
                try:
                    response = st.session_state.chat.send_message(pending)
                    answer = response.text or "Please try again."
                except Exception as exc:
                    answer = f"Model request failed: `{type(exc).__name__}: {exc}`"
                st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
