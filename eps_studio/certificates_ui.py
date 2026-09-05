from pathlib import Path
from dataclasses import asdict
import io
import json
import time
import streamlit as st
from .core import ROOT, default_font, render_certificate, export_certificates
from .shared_ui import table, image_data, folder_field, style_controls, result_panel

def certificates():
    st.title("Certificate Studio")
    st.caption("Create polished certificates. Set up your files, refine the layout, and export your batch.")
    with st.container(border=True, key="cert_source"):
        st.subheader("01  /  Source files")
        a,b = st.columns(2)
        with a:
            templates = sorted(ROOT.glob("Cert*.png"))
            choice = st.selectbox("Template library", [p.name for p in templates]+["Upload a new template"])
            uploaded = st.file_uploader("Upload template", type=["png","jpg","jpeg","webp"])
            template_bytes = uploaded.getvalue() if uploaded else (ROOT/choice).read_bytes() if choice != "Upload a new template" else None
        with b:
            data = st.file_uploader("Upload student data · Excel or CSV", type=["xlsx","csv"])
            local_files = sorted([*ROOT.glob("*.xlsx"), *ROOT.glob("*.csv")])
            local = st.selectbox("Or select a project data file", ["Select a file"]+[p.name for p in local_files])
            data_bytes = data.getvalue() if data else (ROOT/local).read_bytes() if local != "Select a file" else None
            data_name = data.name if data else local
            st.caption("Use column headers in the first row. Select the name column after loading your file.")
            st.download_button("Download sample CSV", "Name,Grade\nAlex Morgan,Excellent\nSarah Wilson,Excellent\n".encode("utf-8-sig"), "students-template.csv", "text/csv")
    if template_bytes is None or data_bytes is None:
        st.info("Choose a template and a data file to unlock the design workspace.")
        result_panel("cert_result")
        return
    template = image_data(template_bytes)
    df = table(data_bytes, Path(data_name).suffix)
    if df.empty or not len(df.columns):
        st.warning("This file has no records. Add your data and upload it again.")
        return
    name_col = st.selectbox("Student name column", df.columns)
    valid = df[name_col].str.strip().ne("")
    a,b,c = st.columns(3)
    a.metric("Total records", len(df))
    b.metric("Ready to export", int(valid.sum()))
    c.metric("Template size", f"{template.width} × {template.height}")
    if not valid.all():
        st.warning(f"{int((~valid).sum())} records have no name. They will be skipped and included in the report.")
    with st.expander("Review source data"):
        st.dataframe(df, width="stretch", hide_index=True)
    controls, preview = st.columns([1,1.8], gap="large")
    with controls:
        with st.container(border=True, height=680, key="cert_controls"):
            st.subheader("02  /  Layout settings")
            with st.expander("Custom font & saved layout"):
                preset = st.file_uploader("Upload saved layout", type=["json"])
                if st.button("Apply layout", disabled=preset is None):
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
                                        raise ValueError("Layout value is outside the allowed range")
                                    updates[prefix+"_"+field] = int(value)
                                elif field=="color":
                                    import re
                                    if not isinstance(value,str) or not re.fullmatch(r"#[0-9a-fA-F]{6}",value):
                                        raise ValueError("Invalid color value")
                                    updates[prefix+"_color"] = value
                        st.session_state.update(updates)
                        st.success("Text positions, sizes, and colors restored.")
                    except (ValueError, TypeError, AttributeError) as exc:
                        st.error(f"Could not read layout: {exc}")
                custom_font = st.file_uploader("Custom font · optional", type=["ttf","otf"])
                font_source = custom_font.getvalue() if custom_font else default_font()
            name_style = style_controls("Student name", "name",60,80)
            show_grade = st.checkbox("Include grade")
            grade_col = st.selectbox("Grade column", df.columns) if show_grade else None
            grade_style = style_controls("Grade styling","grade",60,60) if show_grade else None
            show_date = st.checkbox("Include date")
            date = st.text_input("Date text") if show_date else ""
            date_style = style_controls("Date styling","date",80,40) if show_date else None
            sig = st.file_uploader("Transparent signature · optional", type=["png"])
            signature = image_data(sig.getvalue()) if sig else None
            position = (70,80,15)
            if sig:
                with st.expander("Signature placement"):
                    position = (st.slider("Horizontal (%)",0,100,70), st.slider("Vertical (%)",0,100,80), st.slider("Signature width (%)",1,100,15))
            settings = {"name":asdict(name_style),"grade":asdict(grade_style) if grade_style else None,"date":asdict(date_style) if date_style else None}
            st.download_button("Save text layout", json.dumps(settings,ensure_ascii=False,indent=2),"eps-layout.json","application/json")
    def render(row):
        return render_certificate(template,row[name_col],name_style,font_source,
            grade=row[grade_col] if grade_col else "",grade_style=grade_style,
            date=date,date_style=date_style,signature=signature,signature_position=position)
    with preview:
        with st.container(border=True, key="cert_preview"):
            st.subheader("Live preview")
            selected = st.selectbox("Preview record",range(len(df)),format_func=lambda i:f"{i+1} · {df.iloc[i][name_col] or 'Unnamed record'}")
            rendered = render(df.iloc[selected])
            st.image(rendered,width="stretch")
            st.caption("Long names shrink to fit your chosen width. Your export matches this preview.")
            buffer = io.BytesIO()
            rendered.save(buffer,format="PNG")
            st.download_button("Download preview",buffer.getvalue(),"certificate-preview.png","image/png")
    with st.container(border=True, key="cert_export"):
        st.subheader("03  /  Export batch")
        output = folder_field("Certificate output folder","cert_output",ROOT/"Cert_Out")
        pdf = st.checkbox("Include a combined PDF",True)
        quality = st.slider("JPEG quality",75,100,95,key="cert_quality")
        st.caption("Each batch gets a new folder. Numbered filenames keep duplicate names safe.")
        if st.button("Export certificates",type="primary",disabled=not valid.any() or not output.strip(),width="stretch"):
            start = time.perf_counter()
            progress = st.progress(0,text="Exporting certificates…")
            folder, records = export_certificates(df,name_col,render,output,pdf,quality,progress.progress)
            st.session_state.cert_result = (str(folder),records,time.perf_counter()-start)
    result_panel("cert_result")

