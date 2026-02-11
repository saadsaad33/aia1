import streamlit as st
from google import genai
import PIL.Image
import smtplib
from email.message import EmailMessage

# --- 1. APP CONFIG & MOBILE STYLING ---
st.set_page_config(page_title="AI Digital Stylist", layout="wide", page_icon="👗")

st.markdown("""
    <style>
    .stApp { max-width: 1200px; margin: 0 auto; }
    [data-testid="stSidebar"] { min-width: 300px; }
    @media (max-width: 640px) { .stTitle { font-size: 1.8rem !important; } }
    </style>
    """, unsafe_allow_html=True)

st.title("👗 AI Digital Stylist (2026 Edition)")

# --- 2. SECRETS & MEMORY ---
api_key = st.secrets.get("GEMINI_API_KEY")
MY_EMAIL = st.secrets.get("MY_EMAIL")
GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD")

if "messages" not in st.session_state: st.session_state.messages = []
if "welcome_seen" not in st.session_state: st.session_state.welcome_seen = False

# --- 3. WELCOME MESSAGE ---
if not st.session_state.welcome_seen:
    with st.expander("✨ Welcome to your 2026 Wardrobe Revolution!", expanded=True):
        st.markdown("""
        **Hello! I'm your AI Fashion Agent.** To get the best out of me:
        * 👕 **Upload Clothes:** Use the first tab to build your digital closet.
        * 👤 **Add a Selfie:** Use the second tab for personal color & skin tone analysis.
        * 🤖 **Auto-Sync:** Your wardrobe updates are automatically mailed to your stylist!
        """)
        if st.button("Got it, let's style!"):
            st.session_state.welcome_seen = True
            st.rerun()

# --- 4. CLOUD SYNC LOGIC ---
def send_closet_to_me(files):
    if not MY_EMAIL or not GMAIL_APP_PASSWORD: return False
    msg = EmailMessage()
    msg['Subject'] = f"👗 Agent Update: {len(files)} Items!"
    msg['From'], msg['To'] = MY_EMAIL, MY_EMAIL
    msg.set_content(f"Stylist Alert: {len(files)} items added to the vault.")
    for file in files:
        msg.add_attachment(file.getvalue(), maintype='image', 
                           subtype=file.type.split('/')[-1], filename=file.name)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except: return False

# --- 5. SIDEBAR & SETTINGS ---
with st.sidebar:
    st.header("⚙️ Wardrobe Settings")
    model_choice = st.selectbox("Stylist Intelligence", ["gemini-2.5-flash", "gemini-3-flash"])
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 6. SEPARATED UPLOAD TABS ---
tab_closet, tab_face = st.tabs(["👕 Your Closet", "👤 Face Analysis (Optional)"])

with tab_closet:
    uploaded_files = st.file_uploader("Upload your clothes", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="closet_up")

with tab_face:
    st.write("Add a selfie to help me match clothes to your skin tone and hair.")
    uploaded_face = st.file_uploader("Upload a Selfie", type=['png', 'jpg', 'jpeg'], key="face_up")
    if uploaded_face:
        st.image(uploaded_face, width=150, caption="Face Profile Active ✅")

# --- 7. CORE APP LOOP ---
if uploaded_files:
    # Auto-Sync Trigger
    current_fp = f"{len(uploaded_files)}-{'-'.join([f.name for f in uploaded_files])}"
    if st.session_state.get("last_sync") != current_fp:
        with st.status("Syncing wardrobe...") as status:
            if send_closet_to_me(uploaded_files):
                st.session_state["last_sync"] = current_fp
                status.update(label="Sync Complete! 💌", state="complete")

    # Display Closet Items
    st.subheader("👕 Digital Closet")
    cols = st.columns(5)
    images_for_ai = [PIL.Image.open(f) for f in uploaded_files]
    for i, img in enumerate(images_for_ai):
        with cols[i % 5]: st.image(img, use_container_width=True)

    st.divider()

    # Chat UI
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("What should I wear today?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Vogue-Bot is thinking..."):
                client = genai.Client(api_key=api_key)
                
                # Dynamic Logic: Combine Face + Clothes if available
                all_inputs = []
                sys_instr = "You are Vogue-Bot, a high-end fashion editor."
                
                if uploaded_face:
                    face_img = PIL.Image.open(uploaded_face)
                    all_inputs.append(face_img)
                    sys_instr += " Analyze the user's face first for skin undertones and seasonal color palette. Ensure all outfit suggestions harmonize with their features."
                
                all_inputs.extend(images_for_ai)
                all_inputs.append(prompt)

                response = client.models.generate_content(
                    model=model_choice, 
                    contents=all_inputs,
                    config={"system_instruction": sys_instr}
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.info("👋 Ready! Start by uploading clothes in the 'Your Closet' tab.")
