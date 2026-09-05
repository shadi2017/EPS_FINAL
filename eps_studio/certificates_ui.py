from pathlib import Path
from dataclasses import asdict
import io
import json
import time
import streamlit as st
from .core import ROOT, IMAGE_EXTENSIONS, TextStyle, default_font, open_image, render_certificate, frame_photo, export_certificates, export_photos
from .shared_ui import table, image_data, prepared, folder_field, style_controls, result_panel

def certificates():
    st.title("شهادات تستحق أصحابها")
    st.caption("اختر القالب والبيانات، اضبط التصميم، ثم صدّر دفعة كاملة بجودة عالية.")
    with st.container(border=True):
        st.subheader("01 / الملفات والبيانات")
        a,b = st.columns(2)
        with a:
            templates = sorted(ROOT.glob("Cert*.png"))
            choice = st.selectbox("قالب من مكتبة المشروع", [p.name for p in templates]+["رفع قالب جديد"])
            uploaded = st.file_uploader("قالب الشهادة", type=["png","jpg","jpeg","webp"])
            template_bytes = uploaded.getvalue() if uploaded else (ROOT/choice).read_bytes() if choice != "رفع قالب جديد" else None
        with b:
            data = st.file_uploader("بيانات الطلاب · Excel أو CSV", type=["xlsx","csv"])
            local_files = sorted([*ROOT.glob("*.xlsx"), *ROOT.glob("*.csv")])
            local = st.selectbox("أو ملف بيانات من المشروع", ["اختر ملفًا"]+[p.name for p in local_files])
            data_bytes = data.getvalue() if data else (ROOT/local).read_bytes() if local != "اختر ملفًا" else None
            data_name = data.name if data else local
            st.caption("الصف الأول لعناوين الأعمدة. اختر عمود الاسم بعد تحميل الملف.")
            st.download_button("تنزيل نموذج البيانات", "الاسم,التقدير\nأحمد محمد,ممتاز\nسارة علي,ممتاز\n".encode("utf-8-sig"), "students-template.csv", "text/csv")
    if template_bytes is None or data_bytes is None:
        st.info("ابدأ باختيار قالب ورفع ملف بيانات الطلاب لإظهار مساحة التصميم.")
        result_panel("cert_result")
        return
    template = image_data(template_bytes)
    df = table(data_bytes, Path(data_name).suffix)
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

