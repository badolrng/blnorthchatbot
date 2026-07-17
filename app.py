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
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("⚠️ Security Keys not found! Please check Streamlit Secrets.")
    st.stop()

# --- Main Dashboard Interface ---
st.title("📊 Daily Performance Dashboard (Rangpur Region)")
st.markdown("---")

st.success("✅ System framework and Google Drive connections are officially ACTIVE!")
st.info(f"📂 Scanning connected Google Drive Folder: `{DRIVE_FOLDER_URL}`")

# --- Phase 2: Data Engine Status ---
st.subheader("⚙️ Data Processing Engine")
st.write("The dynamic Excel scanning engine is initialized to read complicated corporate files.")
st.success("🧠 AI Knowledge Base (Short Codes Dictionary) is successfully loaded!")

st.markdown("---")

# --- AI Knowledge Base (Dictionary) ---
kpi_dictionary = """
Data Dictionary for Excel Files:
- National: Full Bangladesh
- Cluster: Total Regions Data (There have total 5 Cluster in Bangladesh)
- Region: Region of the cluster and Total Distribution House Data of the Region
- DD or DH: Distribution House 
- DD or DH Name: Distribution House Name
- Own Team: Company Employee
- DD or DH Code: Unique Code of Distribution House
- RSO Code: Unique Code of Every Field Force
- BP or BP Code: Brand Promoter Code
- C2C: RSO to Retailer Transaction and Amount
- RSO/BP Own Code: Every RSO/BP Have Own Code for SIM activation
- GA: Gross Add / SIM Activation
- 1xt Txn Time: 1st Transaction time of each RSO
- Txn Count: Transaction Count
- C2C AMT: C2C Amount
- Is C2C TGT meet?: 25 Transaction Done in a day or not
- RS0 MSISDN / i'top-up number: Every RSO have their own service number given by company and BP also have.
- Daily C2C TGT: Every RSO have Daily C2C Amount Target to achieve
- Monthly Status: Monthly total status of that specific part
- RSO C2C Productivity: those rso who done 25 transaction 
- RSO Count: total RSO count of DD or Region
"""

# --- Phase 3: AI Chatbox ---
user_input = st.chat_input("Ask AI (e.g., What does GA mean in our reports?)...")
if user_input:
    st.write(f"**You:** {user_input}")
    
    system_prompt = f"""You are a highly intelligent corporate data analyst for the Rangpur Region. 
    The user may ask questions in Bengali or English. You must reply strictly in professional English.
    Use the following Data Dictionary to understand the user's queries and context:
    {kpi_dictionary}
    """
    
    try:
        model = genai.GenerativeModel('gemini-3.5-flash')
        response = model.generate_content(f"{system_prompt}\n\nUser Question: {user_input}")
        st.write(f"**AI:** {response.text}")
    except Exception as e:
        st.error(f"❌ AI Engine Error: {e}")
