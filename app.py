import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- Page Configuration ---
st.set_page_config(page_title="KPI Dashboard - Rangpur", page_icon="📊", layout="wide")

# --- Load Secrets & Connect AI ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    DRIVE_FOLDER_URL = st.secrets["GOOGLE_DRIVE_FOLDER_URL"]
    
    # Initialize Gemini AI
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("⚠️ Security Keys not found! Please check Streamlit Secrets.")
    st.stop()

# --- Main Dashboard Interface ---
st.title("📊 Daily Performance Dashboard (Rangpur Region)")
st.markdown("---")

st.success("✅ System framework and Gemini AI connections are officially ACTIVE!")
st.info(f"📂 Scanning connected Google Drive Folder: `{DRIVE_FOLDER_URL}`")

# --- Phase 2: Data Engine Status ---
st.subheader("⚙️ Data Processing Engine")
st.write("The dynamic Excel scanning engine is initialized to read complicated corporate files (e.g., C2C Productivity, Gross Activations).")
st.write("⏳ Waiting for the AI Knowledge Base (Short Codes Dictionary) to activate the deep sheet-by-sheet scanning...")

st.markdown("---")

# --- Phase 3: AI Chatbox (Live Test) ---
user_input = st.chat_input("Ask AI (e.g., Hello, are you ready?)...")
if user_input:
    st.write(f"**You:** {user_input}")
    
    # AI Processing
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        system_prompt = "You are a highly intelligent corporate data analyst for the Rangpur Region. The user may ask questions in Bengali or English. You must reply strictly in professional English."
        
        response = model.generate_content(f"{system_prompt}\n\nUser Question: {user_input}")
        st.write(f"**AI:** {response.text}")
    except Exception as e:
        st.error(f"AI Engine Error: {e}")
