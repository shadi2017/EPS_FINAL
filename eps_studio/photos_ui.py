from pathlib import Path
import time
import streamlit as st
from .core import ROOT, IMAGE_EXTENSIONS, open_image, frame_photo, export_photos
from .shared_ui import prepared, folder_field, result_panel

def photos():
    st.title("Photo Studio")
    st.caption("Give every photo a consistent finish with automatic frames and a side-by-side preview.")
    with st.container(border=True, key="photo_source_panel"):
        st.subheader("01  /  Photo source")
        source = folder_field("Source folder","photo_source",ROOT/"test_img")
    directory = Path(source)
    if not source.strip() or not directory.is_dir():
        st.info("Choose a folder containing photos to get started.")
        return
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    st.metric("Photos found",len(files))
    if not files:
        st.info("No supported photos were found in this folder.")
        return
    controls, preview = st.columns([1,1.8],gap="large")
    with controls:
        with st.container(border=True, height=680, key="photo_controls"):
            st.subheader("02  /  Frame settings")
            land = st.file_uploader("Landscape frame · optional",type=["png","jpg","jpeg"])
            port = st.file_uploader("Portrait frame · optional",type=["png","jpg","jpeg"])
            clear = st.checkbox("Remove the center background",True)
            st.caption("Turn this off for transparent frames. Check the preview before exporting.")
            threshold = st.slider("Background tolerance",0,100,35,disabled=not clear)
            quality = st.slider("JPEG quality",75,100,95,key="photo_quality")
            limit = st.selectbox("Output size",[0,3840,2560,1920],format_func=lambda n:"Original resolution" if not n else f"Longest edge: {n}px")
            frames = {}
            for orientation, uploaded, filename in [("landscape",land,"frame_land.png"),("portrait",port,"frame_port.png")]:
                path = ROOT/filename
                raw = uploaded.getvalue() if uploaded else path.read_bytes() if path.exists() else None
                frames[orientation] = prepared(raw,clear,threshold) if raw else None
            if any(f is None for f in frames.values()):
                st.warning("One frame is missing. Photos that need it will be flagged in the report.")
    with preview:
        with st.container(border=True, key="photo_preview"):
            st.subheader("Before & after")
            selected = st.selectbox("Preview photo",files,format_func=lambda p:p.name)
            try:
                photo = open_image(selected)
                frame = frames["landscape" if photo.width>photo.height else "portrait"]
                a,b = st.columns(2)
                a.image(photo,caption="Original",width="stretch")
                if frame is not None:
                    b.image(frame_photo(photo,frame,limit),caption="Framed",width="stretch")
                else:
                    b.info("Add a frame that matches this photo orientation.")
            except Exception as exc:
                st.error(f"Could not preview photo: {exc}")
    with st.container(border=True, key="photo_export"):
        st.subheader("03  /  Export batch")
        output = folder_field("Photo output folder","photo_output",ROOT/"Img_Out")
        st.caption("Originals stay intact. Each export creates a new folder and a detailed report.")
        if st.button("Export photos",type="primary",width="stretch",disabled=not output.strip() or all(f is None for f in frames.values())):
            start = time.perf_counter()
            progress = st.progress(0,text="Processing photos…")
            folder, records = export_photos(files,frames,output,quality,limit,progress.progress)
            st.session_state.photo_result = (str(folder),records,time.perf_counter()-start)
    result_panel("photo_result")

