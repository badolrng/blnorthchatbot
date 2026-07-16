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
        
        with st.spinner("ফাইলের সবগুলো শিট এবং ডেটা স্ক্যান করা হচ্ছে..."):
            try:
                # ম্যাজিক ট্রিক: header=None দেওয়ার কারণে কোনো ডেটা বা ডেট হারাবে না
                if selected_file_path.endswith('.xlsb'):
                    excel_data = pd.read_excel(selected_file_path, engine='pyxlsb', sheet_name=None, header=None)
                else:
                    excel_data = pd.read_excel(selected_file_path, sheet_name=None, header=None)
                
                sheet_names = list(excel_data.keys())
                st.success(f"✅ ফাইলে **{len(sheet_names)}** টি শিট পাওয়া গেছে! নিচে ট্যাবগুলোতে ক্লিক করে দেখুন:")
                
                # সবগুলো শিটকে আলাদা ট্যাবে দেখানো হচ্ছে
                tabs = st.tabs(sheet_names)
                
                for i, tab in enumerate(tabs):
                    with tab:
                        sheet_name = sheet_names[i]
                        df = excel_data[sheet_name]
                        
                        st.write(f"### 📑 {sheet_name} - ডেটা প্রিভিউ")
                        st.info("💡 এক্সেল রিপোর্টের উপরের দিকের ফাঁকা জায়গা বা কোম্পানির টাইটেলগুলো স্কিপ করে আসল কলাম বের করতে নিচের নম্বরটি পরিবর্তন করুন।")
                        
                        header_row = st.number_input(
                            f"এই শিটের মূল কলামগুলো (Header) কত নম্বর লাইনে আছে?", 
                            min_value=0, max_value=20, value=0, key=f"header_{sheet_name}"
                        )
                        
                        # আপনার পছন্দমতো লাইন থেকে ডেটা ক্লিন করা
                        df_cleaned = df.copy()
                        new_header = df_cleaned.iloc[header_row] 
                        df_cleaned = df_cleaned[header_row+1:] 
                        df_cleaned.columns = new_header
                        
                        # ফাইলের সমস্ত ডেটা স্ক্রিনে দেখানো
                        st.dataframe(df_cleaned, use_container_width=True)
                        
            except Exception as e:
                st.error(f"ফাইল রিড করতে সমস্যা হয়েছে: {e}")
