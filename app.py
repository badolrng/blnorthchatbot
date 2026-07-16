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
    st.title("📊 ডেইলি পারফরম্যান্স ড্যাশবোর্ড (Rangpur Region)")
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
        st.success(f"✅ ড্রাইভ থেকে {len(files)} টি ফাইল সিঙ্ক হয়েছে।")
        
        # ফাইল সিলেক্ট করার অপশন
        file_names = [os.path.basename(f) for f in files]
        selected_file_name = st.selectbox("📁 চেক করার জন্য যেকোনো একটি ফাইল নির্বাচন করুন:", file_names)
        
        selected_file_path = [f for f in files if os.path.basename(f) == selected_file_name][0]
        
        try:
            # ফাইলের সব শিট পড়ার লজিক
            if selected_file_path.endswith('.xlsb'):
                excel_data = pd.read_excel(selected_file_path, engine='pyxlsb', sheet_name=None)
            else:
                excel_data = pd.read_excel(selected_file_path, sheet_name=None)
            
            sheet_names = list(excel_data.keys())
            st.info(f"📑 এই ফোল্ডারে **{len(sheet_names)}** টি শিট পাওয়া গেছে।")
            
            # শিট সিলেক্ট করার ড্রপডাউন
            selected_sheet = st.selectbox("আপনি কোন শিটটি দেখতে চান?", sheet_names)
            
            # কলামের নাম ঠিক করার জন্য উপরের ফাঁকা লাইন বাদ দেওয়ার অপশন
            st.markdown("---")
            st.write("### ⚙️ কলাম সেটিং (Header Fixer)")
            header_row = st.number_input("উপর থেকে কত নম্বর লাইনটি আপনার মূল কলামের হেডার? (সাধারণত corporate রিপোর্টে ১, ২ বা ৩ নম্বর লাইনে থাকে। নাম্বার বাড়িয়ে-কমিয়ে চেক করুন)", min_value=0, max_value=20, value=0)
            
            # ফাইনাল ডেটা লোড
            if selected_file_path.endswith('.xlsb'):
                df = pd.read_excel(selected_file_path, engine='pyxlsb', sheet_name=selected_sheet, header=header_row)
            else:
                df = pd.read_excel(selected_file_path, sheet_name=selected_sheet, header=header_row)
            
            st.write("### 📋 ডেটা প্রিভিউ:")
            st.dataframe(df.head(10))
            
            st.write("### 🔍 কলামগুলোর বর্তমান নাম:")
            st.success(", ".join(str(col) for col in df.columns.tolist()))
            
        except Exception as e:
            st.error(f"ফাইল পড়ার সময় এরর হয়েছে: {e}")
