import streamlit as st
import requests
import time
from datetime import datetime

API_BASE = "https://debategpt-backend.onrender.com"


# -------------------------------
# STATE INIT
# -------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "post_text" not in st.session_state:
    st.session_state.post_text = ""
if "trigger_test_prompt" not in st.session_state:
    st.session_state.trigger_test_prompt = False
if "model_download_requested" not in st.session_state:
    st.session_state.model_download_requested = False

# -------------------------------
# RESPONSE STYLES
# -------------------------------
response_styles = {
    "Factual rebuttal": "📊 Provide a factual, evidence-based response.",
    "Satirical mockery": "🎭 Respond with satire and witty mockery.",
    "Expose fallacies": "🧠 Identify and explain logical fallacies in the post.",
    "Friendly correction": "🤝 Respond kindly and gently correct the misinformation.",
    "Trump-style response": "🇺🇸 Respond in the style of Donald Trump — dramatic, boastful, and combative.",
    "Short & provocative punchline": "🔥 Reply with a short, bold, provocative one-liner that cuts to the core.",
    "Elon Musk style": "🚀 Respond in the voice of Elon Musk — techno-visionary with hints of trolling and X-brand humor.",
    "Dry wit": "☕ Use understated, dry humor with a sarcastic British tone.",
    "Screaming Karen mode": "📢 Respond like a loud, overreacting Karen demanding a manager.",
    "Confucius Says": "🧘 Respond as if you're Confucius giving sage advice — start the reply with 'Confucius says...'"
}

def extract_tone_emoji(tone_name):
    for key, description in response_styles.items():
        if key == tone_name:
            return description.split()[0]
    return "🎤"

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="DebateGPT", layout="wide")

# -------------------------------
# SIDEBAR SETTINGS
# -------------------------------
st.sidebar.title("🛠️ Configuration")

try:
    model_response = requests.get(f"{API_BASE}/models").json()
    models = model_response.get("models", [])
except:
    st.sidebar.error("❌ Cannot fetch models from backend.")
    models = []

selected_model = st.sidebar.selectbox("Choose a model:", options=models)
custom_model = st.sidebar.text_input("Or enter custom model:", value=selected_model)
model = custom_model.strip()

style_choice = st.sidebar.radio("Tone", list(response_styles.keys()), index=0)
length_map = {"Short": 150, "Medium": 300, "Long": 600}
response_length = st.sidebar.radio("Response Length", list(length_map.keys()), index=1)
debug_mode = st.sidebar.checkbox("Enable debug mode", value=True)

# -------------------------------
# MAIN CHAT UI
# -------------------------------
tab_chat, tab_history = st.tabs(["💬 Chat", "🕘 History"])
with tab_chat:
    st.title("🗣️ DebateGPT")
    default_test_prompt = "The Earth is flat and climate change is a hoax."
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.post_text = st.text_area("📢 Paste Social Media Post:", value=st.session_state.post_text, height=200)
    with col2:
        if st.button("🧪 Test Prompt"):
            st.session_state.post_text = default_test_prompt
            st.session_state.trigger_test_prompt = True
            st.rerun()

    if st.session_state.trigger_test_prompt:
        generate_now = True
        st.session_state.trigger_test_prompt = False
    else:
        generate_now = st.button("💥 Generate Response")

    if generate_now:
        post_text = st.session_state.post_text.strip()
        if not post_text:
            st.warning("Please paste a post or use the test prompt.")
            st.stop()

        try:
            check = requests.get(f"{API_BASE}/models/{model}").json()
            if not check["exists"]:
                st.warning(f"Model `{model}` not found. Click below to download.")
                if st.button("⬇️ Download Model"):
                    with st.spinner("📥 Downloading..."):
                        pull_result = requests.post(f"{API_BASE}/models/{model}/pull").json()
                        if pull_result.get("success"):
                            st.success(f"✅ Model `{model}` downloaded.")
                            st.rerun()
                        else:
                            st.error("❌ Download failed.")
                            st.stop()
                else:
                    st.stop()
        except Exception as e:
            st.error(f"❌ Error checking or downloading model: {e}")
            st.stop()

        length_hint = "Keep it brief and concise." if response_length == "Short" else "Feel free to elaborate with more detail."
        user_prompt = f"Original Post:\n\"{post_text}\"\n\nRespond below:"
        system_prompt = f"You are DebateGPT. {response_styles[style_choice]} {length_hint}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"num_predict": length_map[response_length]}
        }

        st.markdown("🛰️ Sending request to FastAPI backend...")
        with st.spinner("⏳ Generating response..."):
            try:
                start = time.time()
                response = requests.post(f"{API_BASE}/chat", json=payload)
                elapsed = time.time() - start
                content = response.json()['message']['content']

                st.subheader("🤖 AI Response")
                st.write(content)

                st.session_state.history.append({
                    "post": post_text,
                    "tone": style_choice,
                    "model": model,
                    "verbosity": response_length,
                    "response": content,
                    "time": f"{elapsed:.2f} sec",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.history = st.session_state.history[-25:]

                if debug_mode:
                    st.markdown("---")
                    st.subheader("🛠️ Debug Info")
                    st.markdown(f"**Model used:** `{model}`")
                    st.markdown(f"**Elapsed time:** `{elapsed:.2f} sec`")
                    st.code(f"{system_prompt}\n\n{user_prompt}", language="markdown")
            except Exception as e:
                st.error(f"❌ Failed to generate response: {e}")

# -------------------------------
# HISTORY TAB
# -------------------------------
with tab_history:
    st.title("📜 Response History")
    if not st.session_state.history:
        st.info("No responses yet. Generate one in the Chat tab.")
    else:
        for i, entry in enumerate(reversed(st.session_state.history), 1):
            emoji = extract_tone_emoji(entry.get("tone", ""))
            label = f"{i}. {emoji} {entry['tone']} | 🧬 {entry['model']} | 🔊 {entry['verbosity']} | 🕒 {entry['timestamp']}"
            with st.expander(label):
                st.markdown(f"**📝 Original Post:**\n> {entry['post']}")
                st.markdown("**💡 AI Response:**")
                st.write(entry['response'])
