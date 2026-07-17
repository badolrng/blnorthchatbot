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

# --- Smart Excel Date Converter ---
def convert_excel_dates(val):
    try:
        f = float(val)
        # Excel serial dates for years ~2020-2030 are in the 44000-48000 range
        if 44000 < f < 48000: 
            dt = pd.to_datetime('1899-12-30') + pd.to_timedelta(f, unit='D')
            return dt.strftime("%d-%b").lower() # e.g., '12-jul'
    except:
        pass
    
    if pd.api.types.is_datetime64_any_dtype(type(val)) or isinstance(val, pd.Timestamp):
        return val.strftime("%d-%b").lower()
        
    return str(val).lower().strip()

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
            
        # Promote Header if messy
        for i in range(5):
            if df.iloc[i].astype(str).str.contains('Name|ID|RSO|Code|BP|House', case=False).any():
                df.columns = df.iloc[i]
                df = df[i+1:].reset_index(drop=True)
                break
        
        # Apply universal date converter to columns and all cells
        df.columns = [convert_excel_dates(c) for c in df.columns]
        for col in df.columns:
            df[col] = df[col].apply(convert_excel_dates)
            
        return df, file_name
    except Exception as e:
        return None, str(e)

# --- Local English NLP Engine ---
def local_english_brain(user_text):
    text = user_text.lower()
    params = {"location": "", "role": "", "date": "", "min_val": 0}
    
    # 1. Detect Role
    if re.search(r'\bbp\b', text): params["role"] = "bp"
    elif re.search(r'\brso\b', text): params["role"] = "rso"
        
    # 2. Detect Date (e.g., 12th july -> 12-jul)
    date_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b', text)
    if date_match:
        params["date"] = f"{date_match.group(1)}-{date_match.group(2)[:3]}"
    else:
        date_match = re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})\b', text)
        if date_match:
            params["date"] = f"{date_match.group(2)}-{date_match.group(1)[:3]}"

    # 3. Detect Min Value
    val_match = re.search(r'\b(\d+)\s*(sims?|transactions?|txns?|activations?|sales?)\b', text)
    if val_match:
        params["min_val"] = int(val_match.group(1))

    # 4. Detect Location
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    stop_words = ["show", "me", "the", "who", "did", "on", "in", "of", "how", "many", "region", "house", "for", "with", "minimum", "and", "or", "to", "a", "transactions", "transaction", "sims", "sim", "activations", "activation"] + months
    
    words = re.findall(r'\b[a-z0-9]+\b', text)
    for w in words:
        if len(w) >= 4 and w not in stop_words and not w.isdigit():
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
             
    plt.text(0.5, 0.90, "CARE | CONNECT | CONVERT", fontsize=10, color="#AAAAAA", 
             ha='center', va='center', transform=ax.transAxes)
    
    y_pos = 0.80
    plt.text(0.1, y_pos, "NAME / ID", fontsize=12, color=header_color, fontweight='bold', transform=ax.transAxes)
    plt.text(0.8, y_pos, "ACHIEVEMENT", fontsize=12, color=header_color, fontweight='bold', ha='center', transform=ax.transAxes)
    
    plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color=header_color, lw=2, transform=ax.transAxes)
    
    y_pos -= 0.1
    for item in data_list:
        rso_name = str(item["name"])[:25].upper()
        value = str(item["value"])
        
        plt.text(0.1, y_pos, rso_name, fontsize=12, color=text_color, transform=ax.transAxes)
        plt.text(0.8, y_pos, value, fontsize=14, color="#00FF00", fontweight='bold', ha='center', transform=ax.transAxes)
        plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color="#1E3E62", lw=1, transform=ax.transAxes)
        y_pos -= 0.08
        
    plt.tight_layout()
    st.pyplot(fig)

# --- Main Dashboard UI ---
st.title("🚀 Local English Chatbot (Zero Limits)")
st.markdown("---")

try:
    folder_url = st.secrets.get("GOOGLE_DRIVE_FOLDER_URL", "")
    gcp_creds = dict(st.secrets["google_service_account"])
except:
    st.error("Secrets configuration missing!")
    st.stop()

with st.spinner("Syncing & Translating Dates..."):
    df, file_name = fetch_data_from_drive(folder_url, gcp_creds)

if df is not None:
    st.success(f"✅ Data Synced! Your 100% Local English System is Active.")
else:
    st.error("❌ Sync Failed.")
    st.stop()

st.markdown("---")

user_input = st.chat_input("Ask System (e.g., Show me the RSO of RAJNIL06 who did 25 transactions on 12th July)...")

if user_input:
    st.write(f"**You:** {user_input}")
    
    with st.spinner("🧠 Local Engine is analyzing..."):
        params = local_english_brain(user_input)
        
        extracted_data = []
        
        if df is not None and not df.empty:
            for index, row in df.iterrows():
                row_str = " ".join(row.astype(str)).lower()
                
                # 1. Check Location & Role matches
                loc_match = params['location'] in row_str if params['location'] else True
                role_match = params['role'] in row_str if params['role'] else True
                
                if loc_match and role_match:
                    # Find name
                    rso_name = "Unknown"
                    for col in df.columns:
                        if any(k in str(col).lower() for k in ['name', 'id', 'rso', 'code', 'bp']):
                            rso_name = str(row[col])
                            break
                    if rso_name == "Unknown":
                        rso_name = str(row.iloc[0]) # Fallback to first column
                        
                    # Find achievement
                    achievement_val = -1
                    
                    # A. If dates are Columns (Wide Format)
                    if params['date'] and any(params['date'] in str(c) for c in df.columns):
                        for col in df.columns:
                            if params['date'] in str(col):
                                try:
                                    achievement_val = float(row[col])
                                except:
                                    pass
                    # B. If dates are in Rows (Long Format) or No Date provided
                    else:
                        if params['date'] and params['date'] not in row_str:
                            continue 
                            
                        for col in df.columns:
                            if not any(k in str(col).lower() for k in ['name', 'id', 'rso', 'code', 'bp', 'house', 'date']):
                                try:
                                    num = float(row[col])
                                    if num >= params['min_val']:
                                        achievement_val = num
                                except:
                                    pass
                    
                    if achievement_val >= params['min_val']:
                        val_display = f"{int(achievement_val)}" if achievement_val.is_integer() else f"{achievement_val:.2f}"
                        extracted_data.append({"name": rso_name, "value": val_display})
        
        # Output
        if extracted_data:
            report_title = f"Report: {params.get('location', 'Overview').upper()}"
            st.success(f"🎯 Command Decoded: Location=[{params['location'].upper()}], Role=[{params['role'].upper()}], Date=[{params['date']}], Min Target=[{params['min_val']}]")
            generate_kpi_image(extracted_data[:30], report_title) 
        else:
            st.warning(f"⚠️ Checked filters: Location=[{params['location'].upper()}], Date=[{params['date']}]. No one reached the target of {params['min_val']}.")
