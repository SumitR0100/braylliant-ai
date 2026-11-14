import time

import streamlit as st
from google import genai
from google.genai import types


# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="Braylliant AI",
    page_icon="✨",
    layout="wide",
)


# ------------------------------------------------------------
# Braylliant AI instructions
# ------------------------------------------------------------
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
- Live web research is not connected in this Phase 1 app. Do not pretend to
  have searched the internet or verified current opportunities.
- Do not send emails, contact companies, submit forms, spend money or change
  CRM records. Ask for approval before any external or consequential action.
- Write in clear, practical, professional language. Prefer concise answers.
"""


# ------------------------------------------------------------
# Gemini request function
# ------------------------------------------------------------
def get_gemini_response(messages, model_name):
    """Send the conversation to Gemini using a fresh client per request."""
    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it under Streamlit app Settings > Secrets."
        )

    client = genai.Client(api_key=api_key)

    conversation = []
    for item in messages:
        role = "model" if item["role"] == "assistant" else "user"
        conversation.append(
            {
                "role": role,
                "parts": [{"text": item["content"]}],
            }
        )

    # Retry temporary overload / rate-limit responses a few times.
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=conversation,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.5,
                ),
            )

            answer = response.text
            if not answer:
                raise RuntimeError(
                    "Gemini returned an empty response. Please try a different prompt."
                )
            return answer

        except Exception as exc:
            error_text = str(exc).lower()
            temporary_error = (
                "503" in error_text
                or "unavailable" in error_text
                or "429" in error_text
                or "resource_exhausted" in error_text
                or "high demand" in error_text
            )

            if temporary_error and attempt < 2:
                time.sleep(2 ** attempt)
                continue

            if "503" in error_text or "high demand" in error_text:
                raise RuntimeError(
                    "Google's Gemini service is temporarily overloaded (503). "
                    "Wait a few minutes and try again, or select another available "
                    "Flash model in the sidebar."
                ) from exc

            if "429" in error_text or "resource_exhausted" in error_text:
                raise RuntimeError(
                    "The Gemini API rate limit or quota has been reached. "
                    "Check your Google AI Studio usage and limits."
                ) from exc

            raise


# ------------------------------------------------------------
# Styling
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1050px;
        padding-top: 1.8rem;
    }
    .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 16px;
        background: linear-gradient(120deg, #101d36, #243d62);
        color: white;
        margin-bottom: 1rem;
    }
    .hero h1 {
        color: white;
        margin: 0;
    }
    .hero p {
        color: #d8e4f5;
        margin: .35rem 0 0 0;
    }
    .small-note {
        color: #6b7280;
        font-size: .85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.title("✨ Braylliant AI")
    st.caption("Phase 1 · AI chat assistant")
    st.divider()

    st.subheader("Connection")
    model = st.text_input(
        "Gemini model",
        value="gemini-3.5-flash-lite",
        help=(
            "Default is Gemini 3.5 Flash-Lite. You can enter another model ID "
            "that is available to your Google AI Studio API key."
        ),
    ).strip()

    st.caption(
        "Your API key is read from Streamlit Secrets and is not displayed here."
    )
    st.divider()

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    st.markdown("**Coming in later phases**")
    st.caption(
        "Company knowledge · Web research · Client monitoring · CRM · Daily automation"
    )
    st.divider()

    st.markdown(
        '<div class="small-note">Do not paste passwords, bank details, '
        'confidential client data or personal data into this prototype.</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# Main page
# ------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>Braylliant AI</h1>
      <p>Your AI assistant for thinking, research preparation and business support.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# API key check
# ------------------------------------------------------------
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    api_key = None

if not api_key:
    st.warning(
        "Setup required: add your Gemini API key in Streamlit app Settings > Secrets."
    )
    st.code('GEMINI_API_KEY = "paste-your-key-here"', language="toml")
    st.info(
        "Never paste your API key into this chat, a public GitHub file, "
        "or the app source code."
    )


# ------------------------------------------------------------
# Display previous messages
# ------------------------------------------------------------
for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])


# ------------------------------------------------------------
# Suggested prompts (only before the first message)
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Chat input and response
# ------------------------------------------------------------
prompt = st.chat_input("Message Braylliant AI...") if api_key else None

if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Braylliant AI is thinking..."):
            try:
                answer = get_gemini_response(
                    st.session_state.messages,
                    model,
                )
            except Exception as exc:
                answer = f"**AI request failed:** {exc}"

            st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
