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
    
    # 🚀 THE ULTIMATE FIX: AUTO-DETECT SUPPORTED MODELS 🚀
    # Instead of guessing the model name, we dynamically check which models your API Key actually supports!
    valid_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    if not valid_models:
        st.error("⚠️ Your API Key does not have access to any working text generation models.")
        st.stop()
        
    # We prioritize the most stable, high-limit model available for your specific key
    target_model = valid_models[0] 
    for name in valid_models:
        if '1.5-flash' in name:
            target_model = name
            break
        elif '1.0-pro' in name or 'gemini-pro' in name:
            target_model = name
            
    # Load the dynamically selected model
    model = genai.GenerativeModel(target_model)
    
    # --- Drive Setup ---
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
    # Showing which model was auto-selected so you know it's working properly!
    st.success(f"✅ Data Synced! System auto-connected to highly stable engine: `{target_model}`")
else:
    st.error("❌ Sync Failed.")
    st.stop()

st.markdown("---")

user_input = st.chat_input("Ask AI (e.g., goto 15 tarikhe Rangpur region ar koto jon RSO nijer code sim korse?)...")

if user_input:
    st.write(f"**You:** {user_input}")
    
    # ==========================================
    # HYBRID ENGINE: STEP 1 (AI reads only the command)
    # ==========================================
    intent_prompt = f"""
    Analyze this user query: "{user_input}"
    Extract the search parameters.
    Return ONLY a valid JSON object with these keys:
    - "house": (string) Location or house (e.g. "Rangpur", "RAJNIL06") or "" if none.
    - "role": (string) Role (e.g. "BP", "RSO") or "" if none.
    - "date": (string) Date mentioned (e.g. "15", "12") or "" if none.
    - "min_val": (integer) Minimum numeric achievement (e.g. 1 for "sim korse", 25 for "25 transaction") or 0.
    """
    
    try:
        with st.spinner("🧠 Analyzing parameters..."):
            intent_res = model.generate_content(intent_prompt)
            intent_json = intent_res.text.strip().replace("```json", "").replace("```", "").strip()
            params = json.loads(intent_json)
            
            # ==========================================
            # HYBRID ENGINE: STEP 2 (Python locally filters the huge data)
            # ==========================================
            mask = pd.Series(True, index=df.index)
            row_strings = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
            
            if params.get('house'): 
                mask &= row_strings.str.contains(str(params['house']).lower(), regex=False)
            if params.get('role'): 
                mask &= row_strings.str.contains(str(params['role']).lower(), regex=False)
            if params.get('date'): 
                mask &= row_strings.str.contains(str(params['date']).lower(), regex=False)
                
            filtered_df = df[mask]
            
            # ==========================================
            # HYBRID ENGINE: STEP 3 (AI formats the final output for Image)
            # ==========================================
            if filtered_df.empty:
                st.warning("⚠️ No records found matching these exact criteria in the Excel file.")
            else:
                small_csv = filtered_df.head(40).to_csv(index=False)
                format_prompt = f"""
                Data Chunk (Max 40 rows):
                {small_csv}
                
                Task: Look at the data and find the names/codes of the target role ({params.get('role', 'employee')}) and their numeric achievement (like SIMs or C2C). 
                Keep only those with achievement >= {params.get('min_val', 0)}.
                Return ONLY a JSON array: [{{"name": "Extracted Name", "value": "Extracted Value"}}]
                If no rows match, return []
                """
                
                with st.spinner("🎨 Generating Professional Image Scorecard..."):
                    format_res = model.generate_content(format_prompt)
                    final_json = format_res.text.strip().replace("```json", "").replace("```", "").strip()
                    extracted_data = json.loads(final_json)
                    
                    if extracted_data:
                        report_title = f"Performance Report: {params.get('house', 'General')}".strip("- ")
                        generate_kpi_image(extracted_data, report_title)
                    else:
                        st.warning(f"Data was found for the location, but no one reached the target of {params.get('min_val', 0)}.")
                        
    except Exception as e:
        st.error(f"❌ System Error: {e}")
