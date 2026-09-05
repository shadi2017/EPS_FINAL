"""Shared controls for the two production workspaces."""
from pathlib import Path
import streamlit as st
from .core import TextStyle, open_image, read_table, prepare_frame

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
        st.button("Browse", key=key+"_pick", on_click=pick_folder, args=(key,), width="stretch")
    return value

def style_controls(title, prefix, y, size):
    with st.expander(title, expanded=prefix=="name"):
        x = st.slider("Horizontal position (%)", 0, 100, 50, key=prefix+"_x")
        y = st.slider("Vertical position (%)", 0, 100, y, key=prefix+"_y")
        size = st.number_input("Font size", 10, 1000, size, key=prefix+"_size")
        color = st.color_picker("Text color", "#17324d", key=prefix+"_color")
        width = st.slider("Maximum text width (%)", 10, 100, 85, key=prefix+"_width")
    return TextStyle(x,y,size,color,width)

def result_panel(key):
    result = st.session_state.get(key)
    if not result:
        return
    folder, records, duration = result
    success = sum(r["status"]=="success" for r in records)
    st.divider()
    st.subheader("Latest export")
    a,b,c = st.columns(3)
    a.metric("Completed", success)
    b.metric("Needs attention", len(records)-success)
    c.metric("Elapsed time", f"{duration:.1f} sec")
    if success == len(records):
        st.success("Export completed successfully.")
    else:
        st.warning("Batch finished. Review the items that need attention below.")
    st.code(str(folder), language=None)
    st.dataframe(records, width="stretch", hide_index=True)
    report = Path(folder)/"report.csv"
    if report.exists():
        st.download_button("Download report", report.read_bytes(), "report.csv", "text/csv", key=key+"_report")

