import streamlit as st
import gdown
import pandas as pd
import os
import glob

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Banglalink KPI Dashboard", page_icon="📊", layout="wide")
SECRET_PIN = "2026"  

def check_password():
    def password_entered():
        if st.session_state["password"] == SECRET_PIN:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔒 Banglalink KPI Dashboard - Login</h2>", unsafe_allow_html=True)
        st.text_input("আপনার সিক্রেট পিন কোড দিন:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center;'>🔒 Banglalink KPI Dashboard - Login</h2>", unsafe_allow_html=True)
        st.text_input("আপনার সিক্রেট পিন কোড দিন:", type="password", on_change=password_entered, key="password")
        st.error("❌ পিন কোড ভুল হয়েছে! আবার চেষ্টা করুন।")
        return False
    return True

if check_password():
    st.title("📊 ডিস্ট্রিবিউশন হাউস KPI ড্যাশবোর্ড (Rangpur Region)")
    st.markdown("---")
    
    FOLDER_URL = "https://drive.google.com/drive/folders/1LG3iyP3LUAnMXwlsh06yscJFABd-5s_n?usp=sharing"
    
    @st.cache_data(ttl=3600)
    def load_drive_files():
        folder_name = "drive_data"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        try:
            gdown.download_folder(FOLDER_URL, output=folder_name, quiet=True, use_cookies=False)
            return glob.glob(f"{folder_name}/*")
        except Exception as e:
            return str(e)

    files = load_drive_files()
    
    if isinstance(files, str):
        st.error(f"❌ ড্রাইভ কানেকশনে সমস্যা: {files}")
    elif len(files) == 0:
        st.warning("⚠️ গুগল ড্রাইভ ফোল্ডারটি খালি!")
    else:
        file_names = [os.path.basename(f) for f in files]
        selected_file_name = st.selectbox("📁 কাজ করার জন্য এক্সেল রিপোর্ট নির্বাচন করুন:", file_names)
        selected_file_path = [f for f in files if os.path.basename(f) == selected_file_name][0]
        
        try:
            with st.spinner("ফাইলের শিটগুলোর নাম স্ক্যান করা হচ্ছে..."):
                if selected_file_path.endswith('.xlsb'):
                    xl = pd.ExcelFile(selected_file_path, engine='pyxlsb')
                else:
                    xl = pd.ExcelFile(selected_file_path)
                sheet_names = xl.sheet_names
            
            st.success(f"✅ ফাইলে **{len(sheet_names)}** টি শিট পাওয়া গেছে!")
            
            selected_sheet = st.selectbox("আপনি কোন শিটের ডেটা দেখতে চান? নির্বাচন করুন:", sheet_names)
            
            st.markdown("---")
            st.write(f"### ⚙️ {selected_sheet} - হেডার ও ডেটা ফিক্সার")
            
            header_row = st.number_input(
                "উপর থেকে কত নম্বর লাইনে আপনার মূল কলামের নামগুলো আছে? (0, 1, 2 বা 3 লিখে পরিবর্তন করে দেখুন)", 
                min_value=0, max_value=20, value=0
            )
            
            with st.spinner(f"{selected_sheet} শিটের ডেটা লোড হচ্ছে..."):
                if selected_file_path.endswith('.xlsb'):
                    df = pd.read_excel(selected_file_path, engine='pyxlsb', sheet_name=selected_sheet, header=None)
                else:
                    df = pd.read_excel(selected_file_path, sheet_name=selected_sheet, header=None)
                
                df_cleaned = df.copy()
                
                # --- ম্যাজিক ট্রিক: ডুপ্লিকেট কলাম এবং ফাঁকা কলাম ফিক্স করা ---
                raw_header = df_cleaned.iloc[header_row].fillna("Empty_Column").astype(str)
                
                new_header = []
                counts = {}
                for col in raw_header:
                    if col in counts:
                        counts[col] += 1
                        new_header.append(f"{col}_{counts[col]}")
                    else:
                        counts[col] = 0
                        new_header.append(col)
                        
                df_cleaned = df_cleaned[header_row+1:]
                df_cleaned.columns = new_header
                df_cleaned = df_cleaned.reset_index(drop=True)
                
                st.write("### 📋 সম্পূর্ণ ডেটা টেবিল:")
                st.dataframe(df_cleaned, use_container_width=True)
                
                st.write("### 🔍 এই শিটের কলামগুলোর নাম:")
                st.info(", ".join(df_cleaned.columns.tolist()))
                
        except Exception as e:
            st.error(f"❌ ফাইলটি পড়তে সমস্যা হয়েছে। এরর ডিটেলস: {e}")
