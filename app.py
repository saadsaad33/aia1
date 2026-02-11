import streamlit as st
from google import genai
import PIL.Image
import os

# --- APP CONFIG ---
st.set_page_config(page_title="AI Digital Stylist", layout="wide")
st.title("👗 AI Digital Stylist (2026 Edition)")

# Sidebar for Settings
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    
    # NEW: Selection for the model to prevent 404 errors
    # In 2026, 'gemini-2.0-flash' is the most stable free-tier model.
    model_choice = st.selectbox(
        "Select Model (Try another if 404 occurs)",
        ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
    )
    
    st.info("Get your key at aistudio.google.com")
    uploaded_files = st.file_uploader(
        "Upload photos of your clothes", 
        accept_multiple_files=True, 
        type=['png', 'jpg', 'jpeg']
    )

# --- VALIDATION ---
if not api_key:
    st.warning("Please enter your API Key in the sidebar to start.")
    st.stop()

# Initialize the Client with the NEW SDK syntax
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Failed to connect to Google AI: {e}")
    st.stop()

# --- CLOSET SECTION ---
if uploaded_files:
    st.subheader("👕 Your Digital Closet")
    cols = st.columns(5)
    images_for_ai = []
    
    for i, file in enumerate(uploaded_files):
        img = PIL.Image.open(file)
        images_for_ai.append(img)
        with cols[i % 5]:
            st.image(img, use_container_width=True)

    st.divider()

    # --- CHAT SECTION ---
    st.subheader("💬 Chat with your Stylist")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask: 'What can I wear for a business meeting?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"Stylist is thinking using {model_choice}..."):
                try:
                    # Combine all images and the text prompt into one request
                    # We pass 'images_for_ai' as a list directly
                    response = client.models.generate_content(
                        model=model_choice,
                        contents=[
                            "You are a fashion expert. Based ON ONLY these images, "
                            "create a stylish outfit for the following request: ",
                            *images_for_ai, 
                            prompt
                        ]
                    )
                    
                    full_response = response.text
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    if "404" in str(e):
                        st.error(f"Model '{model_choice}' not found.")
                        st.info("Try selecting 'gemini-2.5-flash' from the sidebar.")
                    else:
                        st.error(f"API Error: {e}")
else:
    st.info("Step 1: Paste API Key. Step 2: Upload clothes in the sidebar!")