import streamlit as st
from google import genai
import PIL.Image
import smtplib
from email.message import EmailMessage

# --- 1. APP CONFIG ---
st.set_page_config(page_title="AI Digital Stylist", layout="wide", page_icon="👗")
st.title("👗 AI Digital Stylist (2026 Edition)")

# --- 2. API & EMAIL SECRETS ---
api_key = st.secrets.get("GEMINI_API_KEY")
MY_EMAIL = st.secrets.get("MY_EMAIL")
GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD")

# Sidebar for Settings
with st.sidebar:
    st.header("Settings")
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key", type="password")
    
    model_choice = st.selectbox(
        "Select Model",
        ["gemini-2.5-flash", "gemini-3-flash", "gemini-2.0-flash"]
    )
    
    st.divider()
    uploaded_files = st.file_uploader(
        "Upload photos of your clothes", 
        accept_multiple_files=True, 
        type=['png', 'jpg', 'jpeg']
    )

# --- 3. EMAIL FUNCTION ---
def send_closet_to_me(files):
    if not MY_EMAIL or not GMAIL_APP_PASSWORD:
        st.error("Email credentials missing in Secrets!")
        return False
    
    msg = EmailMessage()
    msg['Subject'] = "👗 New Digital Closet Upload!"
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL
    msg.set_content(f"You have received {len(files)} new clothing items to style.")

    for file in files:
        file_data = file.getvalue()
        file_name = file.name
        msg.add_attachment(
            file_data,
            maintype='image',
            subtype=file.type.split('/')[-1],
            filename=file_name
        )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# --- 4. CLOSET & AI LOGIC ---
if uploaded_files:
    # Option to send to you
    if st.sidebar.button("📤 Sync Closet with Stylist"):
        with st.spinner("Sending images to your stylist..."):
            if send_closet_to_me(uploaded_files):
                st.sidebar.success("Closet synced! 💌")

    st.subheader("👕 Your Digital Closet")
    cols = st.columns(5)
    images_for_ai = [PIL.Image.open(f) for f in uploaded_files]
    
    for i, img in enumerate(images_for_ai):
        with cols[i % 5]:
            st.image(img, use_container_width=True)

    st.divider()
    st.subheader("💬 Chat with your Stylist")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask: 'What can I wear today?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_choice,
                    contents=["Identify these clothes and suggest an outfit:", *images_for_ai, prompt]
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"API Error: {e}")
else:
    st.info("👋 Upload photos in the sidebar to begin.")
