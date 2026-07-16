import streamlit as st

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Banglalink KPI Dashboard", page_icon="📊", layout="wide")

# --- সিকিউরিটি পিন সিস্টেম ---
SECRET_PIN = "2026"  # আপনার টিমের জন্য এটি হলো লগইন পিন

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
    st.success("✅ লগইন সফল হয়েছে! সিস্টেমের বেসিক স্ট্রাকচার রেডি।")
    st.info("📌 পরবর্তীতে এখানে আপনার গুগল ড্রাইভের ডেটা থেকে গ্রস অ্যাক্টিভেশন এবং CARE | CONNECT | CONVERT অ্যানালাইসিসের মূল চার্টগুলো আসবে।")
