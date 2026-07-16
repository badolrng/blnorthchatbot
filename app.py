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

# --- স্মার্ট অটো-ক্লিনার ফাংশন ---
def smart_auto_clean(file_path):
    if file_path.endswith('.xlsb'):
        xl = pd.ExcelFile(file_path, engine='pyxlsb')
    else:
        xl = pd.ExcelFile(file_path)
        
    best_sheet = None
    best_df = None
    max_data_points = 0

    # সবগুলো শিট স্ক্যান করে সবচেয়ে বেশি ডেটা থাকা শিটটি বের করা
    for sheet in xl.sheet_names:
        if file_path.endswith('.xlsb'):
            df_raw = pd.read_excel(file_path, engine='pyxlsb', sheet_name=sheet, header=None)
        else:
            df_raw = pd.read_excel(file_path, sheet_name=sheet, header=None)
            
        # যে লাইনে সবচেয়ে বেশি ঘর পূরণ করা আছে, সেটিকে হেডার ধরা
        row_non_null_counts = df_raw.notna().sum(axis=1)
        if row_non_null_counts.max() == 0: 
            continue
            
        header_idx = row_non_null_counts.idxmax()
        
        df_cleaned = df_raw.copy()
        raw_header = df_cleaned.iloc[header_idx].fillna("Empty_Col").astype(str)
        
        # ডুপ্লিকেট নাম ফিক্স করা
        new_header = []
        counts = {}
        for col in raw_header:
            if col in counts:
                counts[col] += 1
                new_header.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 0
                new_header.append(col)
                
        df_cleaned = df_cleaned[header_idx+1:].reset_index(drop=True)
        df_cleaned.columns = new_header
        
        # সম্পূর্ণ ফাঁকা কলাম এবং সারি ডিলিট করা
        df_cleaned = df_cleaned.dropna(how='all', axis=1).dropna(how='all', axis=0)
        
        data_points = df_cleaned.shape[0] * df_cleaned.shape[1]
        if data_points > max_data_points:
            max_data_points = data_points
            best_df = df_cleaned
            best_sheet = sheet
            
    return best_sheet, best_df

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
            with st.spinner("🤖 এআই আপনার ফাইল স্ক্যান করে ডেটা গুছিয়ে নিচ্ছে (Auto-Pilot Mode)..."):
                # অটোমেটিক ডেটা ক্লিনিং 
                best_sheet, final_df = smart_auto_clean(selected_file_path)
            
            st.success(f"✅ অটো-ডিটেকশন সফল! এআই নিজে থেকে **'{best_sheet}'** শিটটিকে মূল ডেটা হিসেবে বেছে নিয়েছে এবং হেডার ফিক্স করেছে।")
            
            # ডেটা এবং চ্যাটবট পাশাপাশি দেখানোর জন্য লেআউট
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("### 📋 আপনার অটো-ক্লিনড ডেটা:")
                st.dataframe(final_df.head(50), use_container_width=True)
                st.info(f"**মোট কলাম:** {len(final_df.columns)} টি | **মোট সারি (ডেটা):** {len(final_df)} টি")
                
            with col2:
                st.write("### 🤖 এআই চ্যাট অ্যাসিস্ট্যান্ট")
                st.markdown("এখানে আপনি সাধারণ ভাষায় ডেটা নিয়ে প্রশ্ন করতে পারবেন।")
                
                # ডেমো চ্যাট ইন্টারফেস
                user_question = st.text_input("আপনার প্রশ্ন লিখুন (যেমন: টপ হাউস কোনটি?)")
                if st.button("জিজ্ঞেস করুন"):
                    if user_question:
                        st.warning("⚠️ এআই-এর 'ব্রেন' (API Key) এখনো যুক্ত করা হয়নি। যুক্ত হলে আমি এই ডেটা থেকে সরাসরি উত্তর দিতে পারব!")
                        
        except Exception as e:
            st.error(f"❌ অটো-পাইলট কাজ করতে সমস্যা হয়েছে। এরর: {e}")
