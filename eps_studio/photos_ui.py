from pathlib import Path
from dataclasses import asdict
import io
import json
import time
import streamlit as st
from .core import ROOT, IMAGE_EXTENSIONS, TextStyle, default_font, open_image, render_certificate, frame_photo, export_certificates, export_photos
from .shared_ui import table, image_data, prepared, folder_field, style_controls, result_panel

def photos():
    st.title("صور بهوية واحدة")
    st.caption("إطارات تلقائية حسب اتجاه الصورة، ومعاينة قبل معالجة الألبوم بالكامل.")
    with st.container(border=True):
        st.subheader("01 / مصدر الصور")
        source = folder_field("مجلد الصور الأصلية","photo_source",ROOT/"test_img")
    directory = Path(source)
    if not source.strip() or not directory.is_dir():
        st.info("اختر مجلدًا يحتوي على الصور للبدء.")
        return
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    st.metric("صور في المجلد",len(files))
    if not files:
        st.info("لا توجد صور مدعومة في هذا المجلد.")
        return
    controls, preview = st.columns([1,2],gap="large")
    with controls:
        st.subheader("02 / الإطارات والجودة")
        land = st.file_uploader("إطار أفقي مخصص",type=["png","jpg","jpeg"])
        port = st.file_uploader("إطار رأسي مخصص",type=["png","jpg","jpeg"])
        clear = st.checkbox("تفريغ الخلفية المتصلة بمركز الإطار",True)
        st.caption("أوقف التفريغ لو الإطار شفاف بالفعل. راجع المعاينة لأن النتيجة تعتمد على تصميم الإطار.")
        threshold = st.slider("حساسية تفريغ الخلفية",0,100,35,disabled=not clear)
        quality = st.slider("جودة JPG",75,100,95,key="photo_quality")
        limit = st.selectbox("حجم الصور الناتجة",[0,3840,2560,1920],format_func=lambda n:"المقاس الأصلي" if not n else f"أطول ضلع {n} بكسل")
        frames = {}
        for orientation, uploaded, filename in [("landscape",land,"frame_land.png"),("portrait",port,"frame_port.png")]:
            path = ROOT/filename
            raw = uploaded.getvalue() if uploaded else path.read_bytes() if path.exists() else None
            frames[orientation] = prepared(raw,clear,threshold) if raw else None
        if any(f is None for f in frames.values()):
            st.warning("أحد الإطارين غير متاح. الصور التي تحتاجه ستظهر كأخطاء في التقرير.")
    with preview:
        st.subheader("قبل وبعد")
        selected = st.selectbox("صورة المعاينة",files,format_func=lambda p:p.name)
        try:
            photo = open_image(selected)
            frame = frames["landscape" if photo.width>photo.height else "portrait"]
            a,b = st.columns(2)
            a.image(photo,caption="الأصل",use_container_width=True)
            if frame is not None:
                b.image(frame_photo(photo,frame,limit),caption="بعد إضافة الإطار",use_container_width=True)
            else:
                b.info("أضف إطارًا مناسبًا لاتجاه الصورة.")
        except Exception as exc:
            st.error(f"تعذر عرض الصورة: {exc}")
    with st.container(border=True):
        st.subheader("03 / التصدير")
        output = folder_field("مجلد حفظ الصور","photo_output",ROOT/"Img_Out")
        st.caption("الصور الأصلية محفوظة. يتم إنشاء مجلد جديد لكل دفعة مع تقرير تفصيلي.")
        if st.button("تجهيز الصور",type="primary",use_container_width=True,disabled=not output.strip() or all(f is None for f in frames.values())):
            start = time.perf_counter()
            progress = st.progress(0,text="جارٍ تجهيز الصور…")
            folder, records = export_photos(files,frames,output,quality,limit,progress.progress)
            st.session_state.photo_result = (str(folder),records,time.perf_counter()-start)
    result_panel("photo_result")

