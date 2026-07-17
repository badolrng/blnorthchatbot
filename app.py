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

# --- Automated Drive Engine (File Fetcher Only) ---
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
            
        # Smart Header Finder (Removes "Unnamed" rows)
        for i in range(5):
            if df.iloc[i].astype(str).str.contains('Name|ID|RSO|Code|BP|House', case=False).any():
                df.columns = df.iloc[i]
                df = df[i+1:].reset_index(drop=True)
                break
                
        df = df.fillna("")
        df.columns = df.columns.astype(str).str.strip()
        return df, file_name
    except Exception as e:
        return None, str(e)

# --- Visual Image Generator ---
def generate_kpi_image(filtered_df, name_col, target_col, title_text):
    if filtered_df.empty:
        st.warning("No data matches your exact filters.")
        return
        
    bg_color = "#0B192C"
    header_color = "#FF6500"
    text_color = "#FFFFFF"
    
    # Limit to top 30 rows for visual clarity in image
    plot_df = filtered_df.head(30)
    
    fig, ax = plt.subplots(figsize=(8, max(4, len(plot_df) * 0.6 + 2)))
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
    for index, row in plot_df.iterrows():
        rso_name = str(row[name_col])[:30]
        try:
            # Format number cleanly
            val = float(row[target_col])
            value = f"{int(val)}" if val.is_integer() else f"{val:.2f}"
        except:
            value = str(row[target_col])
        
        plt.text(0.1, y_pos, rso_name, fontsize=12, color=text_color, transform=ax.transAxes)
        plt.text(0.8, y_pos, value, fontsize=14, color="#00FF00", fontweight='bold', ha='center', transform=ax.transAxes)
        plt.plot([0.05, 0.95], [y_pos-0.03, y_pos-0.03], color="#1E3E62", lw=1, transform=ax.transAxes)
        y_pos -= 0.08
        
    plt.tight_layout()
    st.pyplot(fig)
    if len(filtered_df) > 30:
        st.info(f"Showing top 30 results out of {len(filtered_df)} total matches in the image.")

# --- Main Dashboard UI ---
st.title("🚀 Limitless Master Dashboard")
st.markdown("---")

try:
    folder_url = st.secrets.get("GOOGLE_DRIVE_FOLDER_URL", "")
    gcp_creds = dict(st.secrets["google_service_account"])
except:
    st.error("Secrets configuration missing!")
    st.stop()

with st.spinner("Syncing Master Database..."):
    df, file_name = fetch_data_from_drive(folder_url, gcp_creds)

if df is not None:
    st.success(f"✅ Database Synced! Total Rows: {len(df)}. System is running 100% Locally with Zero Limits.")
else:
    st.error("❌ Sync Failed.")
    st.stop()

st.markdown("### 🎛️ Control Panel")
st.write("Extract specific data instantly without typing complex commands.")

# Limitless Native Python Filters
col1, col2 = st.columns(2)

with col1:
    search_keyword = st.text_input("1. Search House/Region/Role (e.g., RAJNIL06, Rangpur, BP)")
    target_column = st.selectbox("2. Select Date/Target Column", options=df.columns)

with col2:
    name_column = st.selectbox("3. Select Name/ID Column (Who to show)", options=df.columns)
    min_target = st.number_input("4. Minimum Achievement Required", value=1, min_value=0)

if st.button("Generate Image Report", type="primary"):
    with st.spinner("Processing Data Locally..."):
        # Filter 1: By Keyword (House/Role)
        if search_keyword:
            # Search across the entire row for the keyword
            mask = df.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False, na=False)).any(axis=1)
            filtered_df = df[mask]
        else:
            filtered_df = df.copy()
            
        # Filter 2: By Minimum Target Value
        # Convert target column to numeric, coercing errors to NaN
        filtered_df['Numeric_Target'] = pd.to_numeric(filtered_df[target_column], errors='coerce')
        filtered_df = filtered_df[filtered_df['Numeric_Target'] >= min_target]
        
        # Sort highest to lowest
        filtered_df = filtered_df.sort_values(by='Numeric_Target', ascending=False)

        # Generate Custom Image
        report_title = f"Report: {search_keyword.upper() if search_keyword else 'Overview'}"
        generate_kpi_image(filtered_df, name_column, target_column, report_title)
