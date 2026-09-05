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

def certificates():
    st.title("شهادات تستحق أصحابها")
    st.caption("اختر القالب والبيانات، اضبط التصميم، ثم صدّر دفعة كاملة بجودة عالية.")
    with st.container(border=True):
        st.subheader("01 / الملفات والبيانات")
        a,b = st.columns(2)
        with a:
            templates = sorted(ROOT.glob("Cert*.png"))
            choice = st.selectbox("قالب من مكتبة المشروع", ["رفع قالب جديد"]+[p.name for p in templates])
            uploaded = st.file_uploader("قالب الشهادة", type=["png","jpg","jpeg","webp"])
            template_bytes = uploaded.getvalue() if uploaded else (ROOT/choice).read_bytes() if choice != "رفع قالب جديد" else None
        with b:
            data = st.file_uploader("بيانات الطلاب · Excel أو CSV", type=["xlsx","csv"])
            st.caption("الصف الأول لعناوين الأعمدة. اختر عمود الاسم بعد تحميل الملف.")
    if template_bytes is None or data is None:
        st.info("ابدأ باختيار قالب ورفع ملف بيانات الطلاب لإظهار مساحة التصميم.")
        result_panel("cert_result")
        return
    template = image_data(template_bytes)
    df = table(data.getvalue(), Path(data.name).suffix)
    if df.empty or not len(df.columns):
        st.warning("ملف البيانات لا يحتوي على سجلات. أضف بيانات ثم ارفعه مجددًا.")
        return
    name_col = st.selectbox("عمود اسم الطالب", df.columns)
    valid = df[name_col].str.strip().ne("")
    a,b,c = st.columns(3)
    a.metric("السجلات", len(df))
    b.metric("أسماء جاهزة", int(valid.sum()))
    c.metric("مقاس القالب", f"{template.width} × {template.height}")
    if not valid.all():
        st.warning(f"سيتم تخطي {int((~valid).sum())} سجل بدون اسم وتسجيله في التقرير.")
    with st.expander("مراجعة البيانات"):
        st.dataframe(df, use_container_width=True, hide_index=True)
    controls, preview = st.columns([1,2], gap="large")
    with controls:
        st.subheader("02 / التصميم")
        preset = st.file_uploader("استعادة إعدادات تصميم", type=["json"])
        if st.button("تطبيق الإعدادات", disabled=preset is None):
            try:
                values = json.loads(preset.getvalue())
                updates = {}
                for prefix in ("name", "grade", "date"):
                    entry = values.get(prefix)
                    if entry is None:
                        continue
                    for field, value in entry.items():
                        if field in {"x","y","width","size"}:
                            low, high = (10,1000) if field=="size" else (10,100) if field=="width" else (0,100)
                            if type(value) not in (int,float) or not low <= value <= high:
                                raise ValueError("قيمة إعداد خارج النطاق")
                            updates[prefix+"_"+field] = int(value)
                        elif field=="color":
                            import re
                            if not isinstance(value,str) or not re.fullmatch(r"#[0-9a-fA-F]{6}",value):
                                raise ValueError("لون غير صالح")
                            updates[prefix+"_color"] = value
                st.session_state.update(updates)
                st.success("تم استرجاع مواضع النصوص وأحجامها وألوانها.")
            except (ValueError, TypeError, AttributeError) as exc:
                st.error(f"تعذر قراءة الإعدادات: {exc}")
        custom_font = st.file_uploader("خط مخصص · اختياري", type=["ttf","otf"])
        font_source = custom_font.getvalue() if custom_font else default_font()
        name_style = style_controls("اسم الطالب", "name",50,100)
        show_grade = st.checkbox("إضافة التقدير")
        grade_col = st.selectbox("عمود التقدير", df.columns) if show_grade else None
        grade_style = style_controls("تنسيق التقدير","grade",60,60) if show_grade else None
        show_date = st.checkbox("إضافة التاريخ")
        date = st.text_input("نص التاريخ") if show_date else ""
        date_style = style_controls("تنسيق التاريخ","date",80,40) if show_date else None
        sig = st.file_uploader("توقيع بخلفية شفافة · اختياري", type=["png"])
        signature = image_data(sig.getvalue()) if sig else None
        position = (70,80,15)
        if sig:
            with st.expander("موضع التوقيع"):
                position = (st.slider("أفقي %",0,100,70), st.slider("رأسي %",0,100,80), st.slider("عرض التوقيع %",1,100,15))
        settings = {"name":asdict(name_style),"grade":asdict(grade_style) if grade_style else None,"date":asdict(date_style) if date_style else None}
        st.download_button("حفظ تنسيق النصوص", json.dumps(settings,ensure_ascii=False,indent=2),"eps-layout.json","application/json")
    def render(row):
        return render_certificate(template,row[name_col],name_style,font_source,
            grade=row[grade_col] if grade_col else "",grade_style=grade_style,
            date=date,date_style=date_style,signature=signature,signature_position=position)
    with preview:
        st.subheader("معاينة مباشرة")
        selected = st.selectbox("السجل المعروض",range(len(df)),format_func=lambda i:f"{i+1} · {df.iloc[i][name_col] or 'بدون اسم'}")
        rendered = render(df.iloc[selected])
        st.image(rendered,use_container_width=True)
        st.caption("يتقلص حجم الاسم تلقائيًا ليلائم العرض المحدد. المعاينة تستخدم نفس محرك التصدير.")
        buffer = io.BytesIO()
        rendered.save(buffer,format="PNG")
        st.download_button("تنزيل شهادة تجريبية",buffer.getvalue(),"certificate-preview.png","image/png")
    with st.container(border=True):
        st.subheader("03 / التصدير")
        output = folder_field("مجلد حفظ الشهادات","cert_output",ROOT/"Cert_Out")
        pdf = st.checkbox("إنشاء ملف PDF مجمّع",True)
        quality = st.slider("جودة JPG",75,100,95,key="cert_quality")
        st.caption("كل عملية تُحفظ في مجلد جديد، مع ترقيم الملفات لحماية الأسماء المتكررة.")
        if st.button("إصدار الشهادات",type="primary",disabled=not valid.any() or not output.strip(),use_container_width=True):
            start = time.perf_counter()
            progress = st.progress(0,text="جارٍ إصدار الشهادات…")
            folder, records = export_certificates(df,name_col,render,output,pdf,quality,progress.progress)
            st.session_state.cert_result = (str(folder),records,time.perf_counter()-start)
    result_panel("cert_result")

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

def main():
    st.set_page_config(page_title="EPS Studio",page_icon="◈",layout="wide")
    st.markdown("""<style>
    .stApp {background:#f5f7fb;color:#17324d}
    .stMainBlockContainer {max-width:1440px;padding-top:2.5rem}
    [data-testid="stSidebar"] {background:#101f32}
    [data-testid="stSidebar"] * {color:#ecf3fa}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {opacity:.65}
    h1,h2,h3,p,label,[data-testid="stCaptionContainer"] {direction:rtl;text-align:right}
    h1 {font-weight:800!important;letter-spacing:-1px;font-size:2.6rem!important}
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
