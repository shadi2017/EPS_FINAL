"""Application shell and shared visual theme."""
import streamlit as st
from .certificates_ui import certificates
from .photos_ui import photos


def main():
    st.set_page_config(page_title="EPS Studio", page_icon="◈", layout="wide")
    st.markdown('''<style>
    .stApp {background:#f3f5fa;color:#202c43;font-family:"Segoe UI",Arial,sans-serif}
    h1,h2,h3,p,label,button,input,select {font-family:"Segoe UI",Arial,sans-serif!important}
    h1,h2,h3,p,label,[data-testid="stCaptionContainer"] {direction:ltr;text-align:left}
    .stMainBlockContainer {max-width:1500px;padding:2.5rem 3rem 3rem}
    h1 {font-weight:750!important;letter-spacing:-1.2px;font-size:2.5rem!important;padding-bottom:.35rem!important}
    h3 {font-size:1.1rem!important;font-weight:650!important;letter-spacing:-.2px}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:#627087!important;font-size:.9rem;line-height:1.6}
    [data-testid="stSidebar"] {background:#111c31;border-right:1px solid #24324a}
    [data-testid="stSidebar"] h1 {font-size:1.55rem!important;letter-spacing:1px;color:#f4f7ff;white-space:nowrap}
    [data-testid="stSidebar"] p,[data-testid="stSidebar"] label {color:#c6d1e4}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#a7b6cf!important}
    [data-testid="stSidebar"] hr {border-color:#29364d}
    [data-testid="stSidebar"] [role="radiogroup"] {gap:8px}
    [data-testid="stSidebar"] [role="radiogroup"] label {padding:12px 14px;border-radius:10px;border:1px solid transparent;width:100%;transition:background .15s}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#253555;border-color:#415986}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#1d2b44}
    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {background:#fff;border-radius:16px;border-color:#e1e6f0!important}
    [data-testid="stVerticalBlockBorderWrapper"] {box-shadow:0 3px 16px #1b2b4710}
    .st-key-cert_source,.st-key-photo_source_panel,.st-key-cert_controls,.st-key-photo_controls,.st-key-cert_preview,.st-key-photo_preview,.st-key-cert_export,.st-key-photo_export {background:#fff;border:1px solid #e1e6f0!important;border-radius:16px;box-shadow:0 3px 16px #1b2b4708}
    [data-testid="stMetric"] {background:#fff;border:1px solid #e1e6f0;border-left:3px solid #5865df;padding:16px 20px;border-radius:12px;text-align:left}
    [data-testid="stMetricValue"] {font-size:1.8rem;font-weight:650}
    .stButton button,.stDownloadButton button {border-radius:9px;min-height:42px;font-weight:600;border-color:#dce3ef}
    .stButton button[kind="primary"] {background:#5361d8;border-color:#5361d8;box-shadow:0 3px 8px #5361d826}
    .stButton button[kind="primary"]:hover {background:#424fc0;border-color:#424fc0}
    [data-testid="stImage"] {background:#edf0f6;padding:10px;border-radius:12px}
    [data-testid="stImage"] img {border-radius:7px;max-height:510px;object-fit:contain}
    [data-testid="stFileUploaderDropzone"] {background:#f7f9fc;border:1px dashed #cbd5e5;border-radius:10px}
    [data-testid="stTextInput"] input {direction:ltr}
    .studio-eyebrow {color:#6878a1;font-size:.72rem;font-weight:700;letter-spacing:2px;margin-bottom:8px}
    .studio-status {margin-top:24px;background:#17283d;border:1px solid #254354;border-radius:10px;padding:12px 14px;color:#9cdec9;font-size:12px;line-height:1.8}
    @media(max-width:800px) {.stMainBlockContainer {padding:1.5rem 1rem} h1 {font-size:2rem!important} [data-testid="stHorizontalBlock"] {flex-wrap:wrap;gap:1rem} [data-testid="stColumn"] {width:100%!important;flex:1 1 100%!important;min-width:0!important}}
    </style>''', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("# ◈ EPS STUDIO")
        st.caption("Your creative production workspace")
        st.divider()
        st.caption("WORKSPACES")
        mode = st.radio("Workspace", ["Certificates", "Photo framing"], label_visibility="collapsed")
        st.divider()
        st.caption("YOUR WORKFLOW")
        st.write("01  Set up your files")
        st.write("02  Refine the preview")
        st.write("03  Export your batch")
        st.markdown('<div class="studio-status">● &nbsp; LOCAL WORKSPACE<br>Your files stay on this device.</div>', unsafe_allow_html=True)
    st.markdown('<div class="studio-eyebrow">EPS STUDIO / PRODUCTION WORKSPACE</div>', unsafe_allow_html=True)
    if st.session_state.pop("picker_error", None):
        st.warning("The folder picker could not open. Enter the folder path directly instead.")
    try:
        certificates() if mode == "Certificates" else photos()
    except Exception as exc:
        st.error(f"Could not complete this step: {exc}")
        st.info("Check your file or output folder and try again.")
