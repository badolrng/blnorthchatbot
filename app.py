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
    
    # আপনার গুগল ড্রাইভ ফোল্ডার লিংক
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

    @st.cache_data(ttl=3600)
    def load_data(files):
        df_list = []
        for f in files:
            if f.endswith('.xlsb'):
                df = pd.read_excel(f, engine='pyxlsb')
                df_list.append(df)
            elif f.endswith('.xlsx') or f.endswith('.xls'):
                df = pd.read_excel(f)
                df_list.append(df)
        if df_list:
            return pd.concat(df_list, ignore_index=True)
        return pd.DataFrame()

    files = load_drive_files()
    
    if isinstance(files, str):
        st.error(f"❌ ড্রাইভ কানেকশনে সমস্যা: {files}")
    elif len(files) == 0:
        st.warning("⚠️ গুগল ড্রাইভ ফোল্ডারটি খালি!")
    else:
        st.success(f"✅ ড্রাইভ থেকে {len(files)} টি ফাইল সিঙ্ক হয়েছে।")
        
        with st.spinner("ডেটা প্রসেস করা হচ্ছে (কয়েক সেকেন্ড সময় লাগতে পারে)..."):
            df = load_data(files)
            
        if not df.empty:
            st.write("### 📋 আপনার এক্সেল রিপোর্টের প্রিভিউ (প্রথম ৫টি সারি):")
            st.dataframe(df.head())
            
            st.write("### 🔍 রিপোর্টের কলামগুলোর নাম:")
            st.info(", ".join(df.columns.tolist()))
            
            st.markdown("---")
            st.success("🎉 অসাধারণ! ডেটা সফলভাবে পড়া গেছে। এখন আমরা এই কলামগুলোর ওপর ভিত্তি করে গ্রাফ এবং এআই (AI) চ্যাটবট যুক্ত করব।")
        else:
            st.error("ফাইলগুলো থেকে কোনো ডেটা পড়া যায়নি।")
