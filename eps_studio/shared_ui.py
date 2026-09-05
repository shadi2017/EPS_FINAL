"""Arabic-first workspace for two independent production workflows."""
from pathlib import Path
from dataclasses import asdict
import io
import json
import time
import streamlit as st
from .core import (ROOT, IMAGE_EXTENSIONS, TextStyle, default_font, open_image,
                   read_table, render_certificate, prepare_frame, frame_photo,
                   export_certificates, export_photos)

@st.cache_data(show_spinner=False, max_entries=8)
def table(data, suffix):
    return read_table(data, suffix)

@st.cache_data(show_spinner=False, max_entries=8)
def image_data(data):
    return open_image(data)

@st.cache_data(show_spinner=False, max_entries=8)
def prepared(data, clear, threshold):
    return prepare_frame(data, clear, threshold)

def pick_folder(key):
    import tkinter as tk
    from tkinter import filedialog
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(title="EPS Studio")
        if selected:
            st.session_state[key] = selected
    except Exception as exc:
        st.session_state["picker_error"] = str(exc)
    finally:
        if root is not None:
            root.destroy()

def folder_field(label, key, default):
    a, b = st.columns([5,1], vertical_alignment="bottom")
    with a:
        value = st.text_input(label, value=str(default), key=key)
    with b:
        st.button("اختيار", key=key+"_pick", on_click=pick_folder, args=(key,), use_container_width=True)
    return value

def style_controls(title, prefix, y, size):
    with st.expander(title, expanded=prefix=="name"):
        x = st.slider("الموضع الأفقي %", 0, 100, 50, key=prefix+"_x")
        y = st.slider("الموضع الرأسي %", 0, 100, y, key=prefix+"_y")
        size = st.number_input("حجم الخط", 10, 1000, size, key=prefix+"_size")
        color = st.color_picker("لون النص", "#17324d", key=prefix+"_color")
        width = st.slider("أقصى عرض للنص %", 10, 100, 85, key=prefix+"_width")
    return TextStyle(x,y,size,color,width)

def result_panel(key):
    result = st.session_state.get(key)
    if not result:
        return
    folder, records, duration = result
    success = sum(r["status"]=="success" for r in records)
    st.divider()
    st.subheader("نتيجة آخر عملية")
    a,b,c = st.columns(3)
    a.metric("تم بنجاح", success)
    b.metric("تحتاج مراجعة", len(records)-success)
    c.metric("الوقت المستغرق", f"{duration:.1f} ثانية")
    if success == len(records):
        st.success("اكتمل التصدير بنجاح.")
    else:
        st.warning("انتهت العملية. راجع تفاصيل العناصر التي لم تكتمل أدناه.")
    st.code(str(folder), language=None)
    st.dataframe(records, use_container_width=True, hide_index=True)
    report = Path(folder)/"report.csv"
    if report.exists():
        st.download_button("تنزيل تقرير النتائج", report.read_bytes(), "report.csv", "text/csv", key=key+"_report")

