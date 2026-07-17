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
    
    # Explicitly using gemini-2.5-flash which has high rate limits (1500/day) and is fully supported
    model = genai.GenerativeModel('gemini-2.5-flash')
    
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
        
    bg_color = "#0B192C"
    header_color = "#FF6500"
    text_color = "#FFFFFF"
    
    fig, ax = plt.subplots(figsize=(8, max(4, len(data_list) * 0.6 + 2)))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.axis('off')
    
    plt.text(0.5, 0.95, title_text.upper(), fontsize=16, color=header_color, 
             fontweight='bold', ha='center', va='center', transform=ax.transAxes)
    plt.text(0.5, 0.90, "CARE | CONNECT | CONVERT", fontsize=10, color="#AAAAAA", 
             ha='center', va='center', transform=ax.transAxes)
    
    y_pos = 0.80
    plt.text(0.1, y_pos, "NAME / ID", fontsize=12, color=header_color, fontweight='bold', transform=ax.transAxes)
    plt.text(0.8, y_pos, "ACHIEVEMENT", fontsize=12, color=header_color, fontweight='bold', ha='center', transform=ax.transAxes)
    
    plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color=header_color, lw=2, transform=ax.transAxes)
    
    y_pos -= 0.1
    for item in data_list:
        # Looking for 'name' or 'rso' dynamically
        rso_name = str(item.get("name", item.get("rso", "Unknown")))
        value = str(item.get("value", "0"))
        
        plt.text(0.1, y_pos, rso_name[:25], fontsize=12, color=text_color, transform=ax.transAxes)
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

user_input = st.chat_input("Ask AI (e.g., koto jon BP koresilo?)...")

if user_input:
    st.write(f"**You:** {user_input}")
    
    # Updated: Now catches 2-letter keywords like 'BP', 'GA', etc.
    english_keywords = re.findall(r'[a-zA-Z0-9]{2,}', user_input.lower())
    
    row_strings = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
    filtered_df = pd.DataFrame()
    
    if english_keywords:
        for kw in english_keywords:
            matched = df[row_strings.str.contains(kw, regex=False)]
            filtered_df = pd.concat([filtered_df, matched])
            
    if filtered_df.empty:
        filtered_df = df.head(1000) # Increased search range
    else:
        filtered_df = filtered_df.drop_duplicates()
        
    data_text = filtered_df.to_csv(index=False)
    
    system_prompt = f"""You are an elite corporate data analyst. 
    Read the following messy CSV data perfectly.
    
    User Request (Bengali/English): "{user_input}"
    
    CSV Data Chunk:
    {data_text}
    
    CRITICAL INSTRUCTION:
    1. Understand the user's exact criteria. If they ask about BP, filter for BP codes/names and their achievements. 
    2. Output YOUR ENTIRE RESPONSE as a STRICT, VALID JSON array of objects. 
    3. NO extra text, NO markdown, NO explanations. 
    4. Format strictly like this:
    [
      {{"name": "BP_NAME_OR_CODE", "value": "ACHIEVEMENT_NUMBER"}}
    ]
    If no data matches perfectly, output an empty array: []
    """
    
    try:
        with st.spinner("🧠 AI is analyzing the exact records and generating your custom Image Scorecard..."):
            response = model.generate_content(system_prompt)
            raw_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            
            try:
                extracted_data = json.loads(raw_json)
                
                if extracted_data and len(extracted_data) > 0:
                    st.success("✅ Exact data found! Generating specific Image Format...")
                    generate_kpi_image(extracted_data, "Custom Performance Report")
                else:
                    st.warning("The AI scanned the area perfectly, but no data matched your exact criteria.")
            except json.JSONDecodeError:
                st.error("AI found the data but formatting failed. Raw Output:")
                st.write(raw_json)
                
    except Exception as e:
        st.error(f"❌ AI API Error: {e}")
