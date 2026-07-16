import streamlit as st
import gdown
import pandas as pd
import os
import glob

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Banglalink KPI Dashboard", page_icon="📊", layout="wide")

# --- সিকিউরিটি পিন সিস্টেম ---
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
    # --- মূল ড্যাশবোর্ড ইন্টারফেস ---
    st.title("📊 ডেইলি পারফরম্যান্স ড্যাশবোর্ড (Rangpur Region)")
    st.markdown("---")
    
    # আপনার গুগল ড্রাইভ ফোল্ডার লিংক
    FOLDER_URL = "https://drive.google.com/drive/folders/1LG3iyP3LUAnMXwlsh06yscJFABd-5s_n?usp=sharing"
    
    # স্মার্ট ক্যাশিং সিস্টেম (যেন বারবার ড্রাইভ থেকে ডাউনলোড না করে এবং স্পিড ফাস্ট থাকে)
    @st.cache_data(ttl=3600)
    def load_drive_files():
        folder_name = "drive_data"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        try:
            # ড্রাইভ থেকে ফোল্ডার ডাউনলোড
            gdown.download_folder(FOLDER_URL, output=folder_name, quiet=True, use_cookies=False)
            all_files = glob.glob(f"{folder_name}/*")
            return all_files
        except Exception as e:
            return str(e)

    st.info("🔄 গুগল ড্রাইভ থেকে ডেটা সিঙ্ক হচ্ছে... (প্রথমবার ৫-১০ সেকেন্ড সময় লাগতে পারে)")
    
    # ডেটা কানেকশন চেক
    files = load_drive_files()
    
    if isinstance(files, str):
        st.error(f"❌ ড্রাইভ কানেকশনে কোনো সমস্যা হয়েছে। এরর মেসেজ: {files}")
    elif len(files) == 0:
        st.warning("⚠️ আপনার গুগল ড্রাইভ ফোল্ডারটি খালি! দয়া করে কিছু এক্সেল রিপোর্ট আপলোড করুন।")
    else:
        st.success(f"✅ কানেকশন ১০০% সফল! গুগল ড্রাইভ থেকে {len(files)} টি রিপোর্ট ফাইল পাওয়া গেছে:")
        
        # ফোল্ডারের ফাইলের নামগুলো দেখাচ্ছে
        for f in files:
            file_name = os.path.basename(f)
            st.write(f"📄 **{file_name}**")
            
        st.markdown("---")
        st.success("🎉 পার্ট ২ কমপ্লিট! এখন শুধু গ্রস অ্যাক্টিভেশন এবং C2C ডেটা অ্যানালাইসিসের পালা।")
