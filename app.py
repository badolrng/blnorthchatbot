import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import re
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(page_title="KPI Dashboard - Rangpur", page_icon="📊", layout="wide")

# --- Automated Drive Engine ---
@st.cache_data(ttl=3600)
def fetch_data_from_drive(folder_url, gcp_credentials_info):
    try:
        match = re.search(r'folders/([a-zA-Z0-9-_]+)', folder_url)
        folder_id = match.group(1) if match else None
        
        if not folder_id:
            return None, "Folder ID is missing."
            
        credentials = service_account.Credentials.from_service_account_info(
            gcp_credentials_info, 
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        
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

# --- Local English NLP Engine (Zero API) ---
def local_english_brain(user_text):
    text = user_text.lower()
    params = {"location": "", "role": "", "date": "", "min_val": 0}
    
    # 1. Detect Role (BP or RSO)
    if re.search(r'\bbp\b', text): params["role"] = "bp"
    elif re.search(r'\brso\b', text): params["role"] = "rso"
        
    # 2. Detect Standard English Date (e.g., "15th july", "july 15", "12 jul")
    date_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b', text)
    if not date_match:
        # Reverse format: "July 15"
        date_match = re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})\b', text)
        if date_match:
            params["date"] = f"{date_match.group(2)}-{date_match.group(1)[:3]}"
    else:
        params["date"] = f"{date_match.group(1)}-{date_match.group(2)[:3]}"
        
    # Fallback for just numbers preceded by "on" (e.g., "on 15")
    if not params["date"]:
        fallback_date = re.search(r'\bon\s+(\d{1,2})\b', text)
        if fallback_date: params["date"] = fallback_date.group(1)

    # 3. Detect Minimum Target (e.g., "1 sim", "25 transactions")
    val_match = re.search(r'\b(\d+)\s*(sims?|transactions?|txns?|activations?)\b', text)
    if val_match:
        params["min_val"] = int(val_match.group(1))

    # 4. Detect Location/House Name (Extracting uppercase words or non-stop words)
    stop_words = ["show", "me", "the", "who", "did", "on", "in", "of", "how", "many", "region", "house", "for", "with", "minimum", "and", "or", "to", "a"]
    words = re.findall(r'\b[a-z0-9]+\b', text)
    for w in words:
        if len(w) >= 4 and w not in stop_words and not w.isdigit():
            if w not in ['sims', 'transactions', 'activations']:
                params["location"] = w
                break
                
    return params

# --- Custom Image Report Generator ---
def generate_kpi_image(data_list, title_text):
    if not data_list:
        st.warning("⚠️ No records found matching these exact criteria.")
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
    
    # Exact formatting logic
    plt.text(0.5, 0.90, "CARE | CONNECT | CONVERT", fontsize=10, color="#AAAAAA", 
             ha='center', va='center', transform=ax.transAxes)
    
    y_pos = 0.80
    plt.text(0.1, y_pos, "NAME / ID", fontsize=12, color=header_color, fontweight='bold', transform=ax.transAxes)
    plt.text(0.8, y_pos, "ACHIEVEMENT", fontsize=12, color=header_color, fontweight='bold', ha='center', transform=ax.transAxes)
    
    plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color=header_color, lw=2, transform=ax.transAxes)
    
    y_pos -= 0.1
    for item in data_list:
        rso_name = str(item["name"])[:25]
        value = str(item["value"])
        
        plt.text(0.1, y_pos, rso_name, fontsize=12, color=text_color, transform=ax.transAxes)
        plt.text(0.8, y_pos, value, fontsize=14, color="#00FF00", fontweight='bold', ha='center', transform=ax.transAxes)
        plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color="#1E3E62", lw=1, transform=ax.transAxes)
        y_pos -= 0.08
        
    plt.tight_layout()
    st.pyplot(fig)

# --- Main Dashboard UI ---
st.title("🚀 Local English Chatbot (Limitless Engine)")
st.markdown("---")

try:
    folder_url = st.secrets.get("GOOGLE_DRIVE_FOLDER_URL", "")
    gcp_creds = dict(st.secrets["google_service_account"])
except:
    st.error("Secrets configuration missing!")
    st.stop()

with st.spinner("Syncing Database..."):
    df, file_name = fetch_data_from_drive(folder_url, gcp_creds)

if df is not None:
    st.success(f"✅ Data Synced! Your 100% Local English System is Active. (Zero API Limits)")
else:
    st.error("❌ Sync Failed.")
    st.stop()

st.markdown("---")

user_input = st.chat_input("Ask System (e.g., Show me the RSO of RAJNIL06 who did 25 transactions on 12th July)...")

if user_input:
    st.write(f"**You:** {user_input}")
    
    with st.spinner("🧠 Local Engine is analyzing your English command..."):
        # 1. Parse command locally
        params = local_english_brain(user_input)
        
        # 2. Filter Database
        mask = pd.Series(True, index=df.index)
        row_strings = df.astype(str).apply(lambda x: ' '.join(x).lower(), axis=1)
        
        if params.get('location'): 
            mask &= row_strings.str.contains(str(params['location']).lower(), regex=False)
        if params.get('role'): 
            mask &= row_strings.str.contains(str(params['role']).lower(), regex=False)
        if params.get('date'): 
            mask &= row_strings.str.contains(str(params['date']).lower(), regex=False)
            
        filtered_df = df[mask]
        
        # 3. Extract logic
        extracted_data = []
        if not filtered_df.empty:
            for index, row in filtered_df.iterrows():
                achievement_val = 0
                rso_name = "Unknown"
                
                for col in df.columns:
                    val_str = str(row[col]).lower()
                    if "code" in col.lower() or "name" in col.lower() or "rso" in col.lower() or "bp" in col.lower():
                        if rso_name == "Unknown": rso_name = str(row[col])
                    else:
                        try:
                            num = float(row[col])
                            if num >= params['min_val']:
                                achievement_val = num
                        except:
                            pass
                
                if achievement_val >= params['min_val']:
                    val_display = f"{int(achievement_val)}" if achievement_val.is_integer() else f"{achievement_val:.2f}"
                    extracted_data.append({"name": rso_name, "value": val_display})
        
        # 4. Generate Output
        if extracted_data:
            report_title = f"Report: {params.get('location', 'Overview').upper()}"
            st.success(f"🎯 Command Decoded: Location=[{params['location'].upper()}], Role=[{params['role'].upper()}], Date=[{params['date']}], Min Target=[{params['min_val']}]")
            generate_kpi_image(extracted_data[:30], report_title)
        else:
            st.warning("⚠️ Data found, but no one reached your requested target.")
