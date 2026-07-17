import streamlit as st

# --- Page Configuration ---
st.set_page_config(page_title="KPI Dashboard - Rangpur", page_icon="📊", layout="wide")

# --- Main Dashboard Interface ---
st.title("📊 Daily Performance Dashboard (Rangpur Region)")
st.markdown("---")

st.success("✅ System framework is successfully deployed and running!")
st.info("📌 Waiting for Phase 2: Google Drive connection and dynamic Excel processing engine.")

# AI Chatbox Placeholder
user_input = st.chat_input("Ask AI (e.g., Show top 5 performers today)...")
if user_input:
    st.write(f"**You:** {user_input}")
    st.write("**AI:** The AI brain is currently offline. Please complete Phase 2 & 3 to activate me!")
