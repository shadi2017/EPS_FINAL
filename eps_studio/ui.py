import streamlit as st
from .certificates_ui import certificates
from .photos_ui import photos

def main():
    st.set_page_config(page_title="EPS Studio",page_icon="◈",layout="wide")
    st.markdown("""<style>
    .stApp {background:#f5f7fb;color:#17324d;font-family:"Segoe UI",Tahoma,Arial,sans-serif}
    h1,h2,h3,p,label,button,input,select {font-family:"Segoe UI",Tahoma,Arial,sans-serif!important}
    .stMainBlockContainer {max-width:1440px;padding-top:2.5rem}
    [data-testid="stSidebar"] {background:#101f32}
    [data-testid="stSidebar"] * {color:#ecf3fa}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {opacity:.65}
    h1,h2,h3,p,label,[data-testid="stCaptionContainer"] {direction:rtl;text-align:right}
    h1 {font-weight:800!important;letter-spacing:-1px;font-size:2.6rem!important}
    [data-testid="stSidebar"] h1 {font-size:1.65rem!important;direction:ltr;letter-spacing:0;text-align:left;white-space:nowrap}
    [data-testid="stVerticalBlockBorderWrapper"] {background:white;border-radius:16px}
    [data-testid="stMetric"] {background:#eaf0f7;padding:16px;border-radius:12px;text-align:right}
    .stButton button,.stDownloadButton button {border-radius:9px;min-height:42px}
    [data-testid="stImage"] img {border-radius:10px}
    </style>""",unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("# ◈ EPS STUDIO")
        st.caption("مساحة الإنتاج الإبداعي")
        st.divider()
        mode = st.radio("مساحة العمل",["إصدار الشهادات","تجهيز الصور"],label_visibility="collapsed")
        st.divider()
        st.markdown("### من الفكرة إلى التصدير")
        st.write("01  اختر الملفات")
        st.write("02  راجع المعاينة")
        st.write("03  صدّر النتائج")
        st.divider()
        st.caption("معالجة محلية · ملفاتك على جهازك")
    if st.session_state.pop("picker_error",None):
        st.warning("تعذر فتح نافذة الاختيار. يمكنك كتابة مسار المجلد مباشرة.")
    try:
        certificates() if mode=="إصدار الشهادات" else photos()
    except Exception as exc:
        st.error(f"تعذر إكمال الخطوة: {exc}")
        st.info("راجع الملف أو مسار الحفظ وحاول مرة أخرى.")
