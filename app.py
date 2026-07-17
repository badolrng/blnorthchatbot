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
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
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
    st.error(f"⚠️ Security or API Error! Check Streamlit Secrets. Details: {e}")
    st.stop()

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
            
        # Clean up column names to avoid hidden spaces
        df.columns = df.columns.astype(str).str.strip()
        
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

# --- Phase 3: Smart AI Pandas Engine ---
user_input = st.chat_input("Ask AI (e.g., I want to see the RSO who have done 25 transaction on 12th july of rajnil06)...")

if user_input:
    st.write(f"**You:** {user_input}")
    
    if df is None:
        st.warning("⚠️ Waiting for data to sync before analyzing.")
    else:
        columns_list = list(df.columns)
        # Providing a 5-row sample to the AI so it visually sees the exact data types and formats (costs very few tokens)
        data_sample = df.head(5).to_csv(index=False)
        
        system_prompt = f"""You are an elite Python Data Analyst for the telecommunications sector.
        A Pandas DataFrame named `df` is loaded in memory.
        
        Exact Columns available: {columns_list}
        
        Data Sample (First 5 Rows):
        {data_sample}
        
        User asks: "{user_input}"
        
        Task:
        Write EXACTLY ONE line of Python code using Pandas to filter `df` based on the user's question.
        Save the filtered dataframe to a variable named `result_df`.
        
        CRITICAL RULES:
        1. Look at the Data Sample to see exactly how DATES are formatted (e.g., 'YYYY-MM-DD HH:MM:SS', 'YYYY-MM-DD', or Excel serial floats like '46204.0'). If the user asks for '12th July' but the sample shows dates as '2026-07-12', your regex MUST search for '2026-07-12' or '2026-07-12.*'.
        2. String search: `df['Column Name'].astype(str).str.contains('SearchTerm', case=False, regex=True, na=False)`
        3. NUMERIC COMPARISON (CRUCIAL): Always convert to numeric first: `pd.to_numeric(df['Txn Count'], errors='coerce') >= 25`
        4. Combine multiple conditions with `&` and wrap each in `()`.
        5. Do NOT write ```python or any markdown formatting. ONLY output the raw Python code.
        6. Do NOT explain the code.
        """
        
        try:
            with st.spinner("🧠 AI is analyzing data formats and writing the extraction algorithm..."):
                response = model.generate_content(system_prompt)
                ai_code = response.text.strip().replace("```python", "").replace("```", "").strip()
                
                local_vars = {'df': df, 'pd': pd}
                try:
                    exec(ai_code, globals(), local_vars)
                    result_df = local_vars.get('result_df', pd.DataFrame())
                    
                    st.success("✅ Data extracted successfully!")
                    with st.expander("Show AI Logic (Python Code)"):
                        st.code(ai_code, language="python")
                    
                    if not result_df.empty:
                        st.dataframe(result_df) 
                    else:
                        st.warning("No data found matching your exact criteria. The AI applied the logic correctly, but no rows matched all conditions.")
                        
                except Exception as exec_error:
                    st.error(f"⚠️ Code Execution Error: The AI logic encountered an issue. Details: {exec_error}")
                    with st.expander("Show Problematic AI Logic"):
                        st.code(ai_code, language="python")
                    
        except Exception as e:
            st.error(f"❌ AI API Error: {e}")
