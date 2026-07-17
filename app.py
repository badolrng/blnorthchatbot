import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import re

# --- Page Configuration ---
st.set_page_config(page_title="KPI Dashboard - Rangpur", page_icon="📊", layout="wide")

# --- Load Secrets & Authenticate ---
try:
    # 1. Gemini AI Setup
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    # 2. Google Drive Bot Setup
    gcp_credentials = dict(st.secrets["google_service_account"])
    credentials = service_account.Credentials.from_service_account_info(
        gcp_credentials, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Extract Folder ID from URL
    folder_url = st.secrets.get("GOOGLE_DRIVE_FOLDER_URL", "")
    match = re.search(r'folders/([a-zA-Z0-9-_]+)', folder_url)
    FOLDER_ID = match.group(1) if match else None

except Exception as e:
    st.error(f"⚠️ Security or API Error! Check Streamlit Secrets. Details: {e}")
    st.stop()

# --- AI Knowledge Base (Dictionary) ---
kpi_dictionary = """
Data Dictionary:
- National: Full Bangladesh
- Cluster: Total Regions Data (5 Clusters)
- Region: Region of the cluster
- DD or DH: Distribution House 
- DD or DH Name: Distribution House Name
- Own Team: Company Employee
- DD or DH Code: Unique Code of Distribution House
- RSO Code: Unique Code of Every Field Force
- BP Code: Brand Promoter Code
- C2C: RSO to Retailer Transaction and Amount
- GA: Gross Add / SIM Activation
- 1xt Txn Time: 1st Transaction time of each RSO
- Txn Count: Transaction Count
- C2C AMT: C2C Amount
- Is C2C TGT meet?: 25 Transaction Done in a day or not
- Daily C2C TGT: Every RSO have Daily C2C Amount Target
"""

# --- Phase 2: Automated Drive Engine ---
@st.cache_data(ttl=3600)
def fetch_data_from_drive(folder_id):
    if not folder_id:
        return None, "Folder ID is missing or incorrect."
    
    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false", 
            fields="files(id, name)"
        ).execute()
        items = results.get('files', [])
        
        if not items:
            return None, "Folder is empty. Please upload Excel files to the connected Drive folder."
        
        file_id = items[0]['id']
        file_name = items[0]['name']
        
        request = drive_service.files().get_media(fileId=file_id)
        downloaded = io.BytesIO()
        downloader = MediaIoBaseDownload(downloaded, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        downloaded.seek(0)
        
        if file_name.endswith('.csv'):
            df = pd.read_csv(downloaded)
        else:
            excel_data = pd.read_excel(downloaded, sheet_name=None)
            df = pd.concat(excel_data.values(), ignore_index=True)
            
        return df, f"Successfully auto-synced `{file_name}`"
        
    except Exception as e:
        return None, f"Drive Sync Error: {str(e)}"

# --- Main Dashboard UI ---
st.title("📊 Daily Performance Dashboard (Rangpur Region)")
st.markdown("---")

st.subheader("⚙️ Automated Google Drive Engine")
with st.spinner("🤖 Bot is scanning your Drive folder and reading all sheets..."):
    df, status_msg = fetch_data_from_drive(FOLDER_ID)

if df is not None:
    st.success(f"✅ Data Engine Active! {status_msg} (Total Rows Indexed: {len(df)})")
else:
    st.error(f"❌ Synchronization Failed: {status_msg}")

st.markdown("---")

# --- Phase 3: Smart AI Chatbox ---
user_input = st.chat_input("Ask AI (e.g., I want to see the RSO who have done 25 transaction on 12th july of rajnil06)...")

if user_input:
    st.write(f"**You:** {user_input}")
    
    if df is None:
        st.warning("⚠️ Waiting for data to sync before analyzing.")
    else:
        # We are now sending the ENTIRE dataset to Gemini (Removing empty spaces to save processing speed)
        df_clean = df.fillna("")
        full_data_csv = df_clean.to_csv(index=False)
        
        system_prompt = f"""You are an elite corporate data analyst for the Rangpur Region telecom operations. 
        A master dataset has been loaded with {len(df)} rows.
        
        The user asks: "{user_input}"
        
        Context/Dictionary:
        {kpi_dictionary}
        
        CRITICAL INSTRUCTIONS:
        1. I am providing the ENTIRE dataset below in CSV format. 
        2. DO NOT give the user instructions on how to filter data in Excel. YOU must perform the filtering mentally based on the CSV data provided below.
        3. Find the exact rows matching the user's query (e.g., specific house name, 25 transactions, specific date).
        4. Output the final result directly as a professional Markdown table containing the exact RSO Codes/Names.
        5. If there are date anomalies (like Excel serials e.g. 46204.0), understand the context and map them correctly. Ignore messy headers like 'Unnamed', focus on the row values.
        
        Entire Dataset (CSV):
        {full_data_csv}
        """
        
        try:
            with st.spinner("🧠 AI is performing a deep scan of all 4,000+ rows. This may take 3-5 seconds..."):
                response = model.generate_content(system_prompt)
                st.write(f"**AI:**\n{response.text}")
        except Exception as e:
            st.error(f"❌ AI Engine Error: {e}")
