import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import re
import json
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(page_title="KPI Dashboard - Rangpur", page_icon="📊", layout="wide")

# --- Load Secrets & Authenticate ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    # Using the most powerful reasoning model
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    gcp_credentials = dict(st.secrets["google_service_account"])
    credentials = service_account.Credentials.from_service_account_info(
        gcp_credentials, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    
    folder_url = st.secrets.get("GOOGLE_DRIVE_FOLDER_URL", "")
    match = re.search(r'folders/([a-zA-Z0-9-_]+)', folder_url)
    FOLDER_ID = match.group(1) if match else None

except Exception as e:
    st.error(f"⚠️ API Error! Check Streamlit Secrets. Details: {e}")
    st.stop()

# --- Automated Drive Engine ---
@st.cache_data(ttl=3600)
def fetch_data_from_drive(folder_id):
    if not folder_id:
        return None, "Folder ID is missing."
    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false", 
            fields="files(id, name)"
        ).execute()
        items = results.get('files', [])
        
        if not items:
            return None, "Folder is empty."
        
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
            
        # Human-Brain Cleaning: Convert everything to string and replace NaN for perfect AI reading
        df = df.fillna("")
        df.columns = df.columns.astype(str).str.strip()
        return df, file_name
    except Exception as e:
        return None, str(e)

# --- Visual Image Generator (Infographic Engine) ---
def generate_kpi_image(data_list, title_text):
    if not data_list:
        st.warning("No data found to generate an image.")
        return
        
    # Corporate Telecom Theme Colors (Orange, Dark Navy, White)
    bg_color = "#0B192C"
    header_color = "#FF6500"
    text_color = "#FFFFFF"
    
    fig, ax = plt.subplots(figsize=(8, max(4, len(data_list) * 0.6 + 2)))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.axis('off')
    
    # Title
    plt.text(0.5, 0.95, title_text.upper(), fontsize=16, color=header_color, 
             fontweight='bold', ha='center', va='center', transform=ax.transAxes)
    plt.text(0.5, 0.90, "CARE | CONNECT | CONVERT", fontsize=10, color="#AAAAAA", 
             ha='center', va='center', transform=ax.transAxes)
    
    # Table Headers
    y_pos = 0.80
    plt.text(0.1, y_pos, "RSO / FIELD FORCE", fontsize=12, color=header_color, fontweight='bold', transform=ax.transAxes)
    plt.text(0.8, y_pos, "TRANSACTIONS", fontsize=12, color=header_color, fontweight='bold', ha='center', transform=ax.transAxes)
    
    plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color=header_color, lw=2, transform=ax.transAxes)
    
    # Data Rows
    y_pos -= 0.1
    for item in data_list:
        rso_name = str(item.get("rso", "Unknown"))
        value = str(item.get("value", "0"))
        
        plt.text(0.1, y_pos, rso_name, fontsize=12, color=text_color, transform=ax.transAxes)
        plt.text(0.8, y_pos, value, fontsize=14, color="#00FF00", fontweight='bold', ha='center', transform=ax.transAxes)
        plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color="#1E3E62", lw=1, transform=ax.transAxes)
        y_pos -= 0.08
        
    plt.tight_layout()
    st.pyplot(fig)

# --- Main Dashboard UI ---
st.title("📊 Master AI Data Engine")
st.markdown("---")

with st.spinner("🤖 System syncing with Google Drive..."):
    df, file_name = fetch_data_from_drive(FOLDER_ID)

if df is not None:
    st.success("✅ Data Synced Successfully! The AI is ready for your commands.")
else:
    st.error("❌ Sync Failed.")
    st.stop()

st.markdown("---")

user_input = st.chat_input("Ask AI (e.g., I want to see the RSO of rajnil06 who did 25 transaction on 12th july)...")

if user_input:
    st.write(f"**You:** {user_input}")
    
    # STEP 1: Fuzzy search to reduce 4000 rows to a small, readable chunk for the AI
    search_keywords = ['rajnil', 'jul', '12', '25', 'c2c', 'ga'] # Basic generic filters
    
    # Convert whole row to a single searchable text string
    row_strings = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    
    # Find rows that might contain the user's requested house or date (loose human-like filtering)
    # We ask AI to generate the specific search keyword first to be smart
    keyword_prompt = f"Extract ONLY the distribution house name (if any) from this query: '{user_input}'. Output only the word, nothing else. If none, output 'NONE'."
    house_keyword = model.generate_content(keyword_prompt).text.strip().lower()
    
    if house_keyword != 'none' and house_keyword != '':
        filtered_df = df[row_strings.str.contains(house_keyword, regex=False)]
    else:
        filtered_df = df.head(200) # Fallback to top rows
        
    # We take the relevant chunk of data as pure text (The way humans read)
    data_text = filtered_df.to_csv(index=False)
    
    # STEP 2: The "Human Brain" Prompt
    system_prompt = f"""You are a highly intelligent corporate data analyst. 
    Read the following messy CSV data text like a human reading a piece of paper.
    
    User Request: "{user_input}"
    
    CSV Data Chunk (Filtered for relevance):
    {data_text}
    
    CRITICAL INSTRUCTION:
    Find the exact rows matching the user's request. Pay close attention to dates (they might be written as 12-Jul, 12/07, or Excel numbers) and transaction columns.
    You MUST output YOUR ENTIRE RESPONSE as a strict, valid JSON array of objects. 
    DO NOT output any extra text, markdown, or explanations. 
    Format:
    [
      {{"rso": "RSO_NAME_OR_CODE_HERE", "value": "TRANSACTION_NUMBER_HERE"}}
    ]
    If no data matches, output an empty array: []
    """
    
    try:
        with st.spinner("🧠 AI is reading the data directly and generating your image..."):
            response = model.generate_content(system_prompt)
            raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            
            try:
                extracted_data = json.loads(raw_json)
                
                if extracted_data and len(extracted_data) > 0:
                    st.success("✅ Exact data found! Generating specific Image Format...")
                    # STEP 3: Generate the Image Scorecard
                    generate_kpi_image(extracted_data, f"Performance Report: {house_keyword.upper()}")
                else:
                    st.warning("The AI read the specific area but found no RSOs meeting this exact criteria on that date.")
            except json.JSONDecodeError:
                st.error("The AI found the data but failed to format it as an image. Here is the raw text:")
                st.write(raw_json)
                
    except Exception as e:
        st.error(f"❌ AI Brain Error: {e}")
