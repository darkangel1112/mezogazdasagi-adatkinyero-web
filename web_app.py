"""
Mezőgazdasági Adatkinyerő v7.5 - Production Ready (FINAL)
Egységes kérelmek PDF-ből történő adatkinyerése és elemzése
Tömeges feldolgozás támogatással
"""

import streamlit as st
import pandas as pd
import json
import tempfile
import os
import zipfile
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from streamlit_lottie import st_lottie

# Saját modulok
from dataprocess import fovetes_parser, masodvetes_parser, osszesitok_parser, adatfeldolgozas_parser
from dataexport import excel_exporter, markdown_exporter, json_transformer
from resultmerge import merge_processed_results


MERGED_RESULT_KEY = "__merged_result__"
SECONDARY_COLUMNS = [
    "Blokk", "Tábla", "Sorszám", "Típus", "Megnevezés", "Anyag", "Növény kód", "Terület"
]


def _secondary_dataframe(rows):
    columns = list(SECONDARY_COLUMNS)
    if rows and len(rows[0]) == len(columns) + 1:
        columns.append("Kérelmező")
    return pd.DataFrame(rows, columns=columns)


def _result_label(result_key):
    result = st.session_state.processed_results[result_key]
    if result.get("is_merged"):
        return "Összefűzött"
    if result.get("success"):
        applicant = result.get("analysis_data", {}).get("applicant_info", {}) or {}
        return applicant.get("name") or result.get("filename", result_key)
    return f"❌ {result.get('filename', result_key)}"


def _applicant_identifier(applicant_info):
    """A helyi kinyerő mak_id kulcsát és a régi support_id kulcsot is kezeli."""
    return applicant_info.get("mak_id") or applicant_info.get("support_id") or "N/A"


def _merge_checkbox_key(result_key):
    return f"merge_checkbox_{result_key}"


def _prepare_uploaded_files():
    """Az új kérelem(ek) feldolgozása előtt érvényteleníti a régi összefűzést."""
    upload_key = f"uploader_{st.session_state.get('uploader_key', 0)}"
    if not st.session_state.get(upload_key):
        return

    st.session_state.processed_results.pop(MERGED_RESULT_KEY, None)
    if st.session_state.get("selected_result") == MERGED_RESULT_KEY:
        st.session_state.pop("selected_result", None)


@st.dialog("Kérelmek összefűzése", width="large")
def _show_merge_dialog():
    results = st.session_state.processed_results
    candidates = [
        key for key, result in results.items()
        if result.get("success") and not result.get("is_merged")
    ]
    st.write("Jelöld ki azokat a kérelmeket, amelyek ugyanahhoz az üzemhez tartoznak.")
    selected_keys = []
    for key in candidates:
        label = _result_label(key)
        filename = results[key].get("filename", key)
        if filename != label:
            label = f"{label} — {filename}"
        if st.checkbox(label, key=_merge_checkbox_key(key)):
            selected_keys.append(key)

    submitted = st.button(
        "Összefűzés",
        type="primary",
        use_container_width=True,
        disabled=len(selected_keys) < 2,
    )
    if not submitted:
        return

    try:
        merged_result = merge_processed_results([results[key] for key in selected_keys])
    except Exception as exc:
        st.error(f"Az összefűzés nem sikerült: {exc}")
        return

    results[MERGED_RESULT_KEY] = merged_result
    st.session_state.selected_result = MERGED_RESULT_KEY
    st.rerun()


# ============================================================================
# LOTTIE ANIMÁCIÓ BETÖLTÉS
# ============================================================================

@st.cache_data
def load_lottie_url(url: str):
    """Lottie animáció betöltése URL-ről"""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


# ============================================================================
# PDF GENERÁLÁS - TELJES ADATTARTALOM (JAVÍTOTT)
# ============================================================================

def generate_pdf_report(analysis_data, fovetes_df, masodvetes_list, summary_dict, applicant_name):
    """
    PDF riport generálása - TELJES adattartalom táblázatokkal
    1. oldal: Fedlap (Portrait)
    További oldalak: Adatok (Landscape) táblázatos formában
    """
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    # JAVÍTOTT Font betöltés - ROBUSZTUS DUPLA REGISZTRÁCIÓ
    font_path = os.path.join("assets", "Roboto-Regular.ttf")
    use_custom_font = False
    
    if os.path.exists(font_path):
        try:
            # KRITIKUS: Mindkét stílus regisztrációja KÖTELEZŐ!
            pdf.add_font('Roboto', '', font_path, uni=True)    # Regular
            pdf.add_font('Roboto', 'B', font_path, uni=True)   # Bold (ugyanaz!)
            use_custom_font = True
        except Exception as e:
            st.warning(f"Font betöltési hiba: {e}. Arial fontot használunk.")
            use_custom_font = False
    else:
        st.warning("⚠️ Roboto font nem található. Arial fontot használunk.")
        use_custom_font = False
    
    # ===== 1. FEDLAP (Portrait) =====
    _add_cover_page(pdf, analysis_data.get('applicant_info', {}), applicant_name, use_custom_font)
    
    # ===== 2. ÖSSZEFOGLALÓ TÁBLÁZAT (Landscape) =====
    summary_df = analysis_data.get('summary_df', pd.DataFrame())
    if not summary_df.empty:
        _add_dataframe_table(pdf, summary_df, "Osszesito Tablazat", use_custom_font)
    
    # ===== 3. FŐVETÉS TÁBLÁZAT (Landscape) =====
    if not fovetes_df.empty:
        _add_dataframe_table(pdf, fovetes_df, "Fovetes Adatok", use_custom_font)
    
    # ===== 4. MÁSODVETÉS TÁBLÁZAT (Landscape) =====
    if masodvetes_list:
        masodvetes_df = _secondary_dataframe(masodvetes_list)
        _add_dataframe_table(pdf, masodvetes_df, "Masodvetes/Agrotechnikai Adatok", use_custom_font)
    
    # ===== 5. TÁMOGATÁSI JOGCÍMEK (Landscape) =====
    jogcim_data = summary_dict.get('jogcim', [])
    if jogcim_data:
        jogcim_df = pd.DataFrame(jogcim_data, columns=['Jogcim', 'Terulet (ha)'])
        _add_dataframe_table(pdf, jogcim_df, "Tamogatasi Jogcimek", use_custom_font)
    
    # ===== 6. HASZNOSÍTÁS (Landscape) =====
    hasznositas_data = summary_dict.get('hasznositas', [])
    if hasznositas_data:
        hasznositas_df = pd.DataFrame(hasznositas_data, columns=['Kod', 'Megnevezes', 'Terulet (ha)'])
        _add_dataframe_table(pdf, hasznositas_df, "Hasznositasi Adatok", use_custom_font)
        
        pdf.set_font('Roboto' if use_custom_font else 'Arial', 'B', 9)
        pdf.cell(0, 8, f"Osszesen: {summary_dict.get('hasznositas_total', 0):.4f} ha", ln=True)
    
    # ===== 7. BLOKKHASZNÁLAT (Landscape) =====
    blokk_data = summary_dict.get('blokkok', [])
    if blokk_data:
        blokk_df = pd.DataFrame(blokk_data, columns=['Blokk azonosito', 'Terulet (ha)'])
        _add_dataframe_table(pdf, blokk_df, "Blokkhasználat", use_custom_font)
        
        pdf.set_font('Roboto' if use_custom_font else 'Arial', 'B', 9)
        pdf.cell(0, 8, f"Osszesen: {summary_dict.get('blokkok_total', 0):.4f} ha", ln=True)
    
    # ===== 8. STATISZTIKÁK (Portrait) =====
    _add_statistics_page(pdf, analysis_data.get('extra_stats', {}), fovetes_df, use_custom_font)
    
    # JAVÍTOTT OUTPUT - BYTES KONVERZIÓ!
    pdf_output = pdf.output(dest='S')
    
    # Típusbiztos konverzió
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    return bytes(pdf_output)  # KRITIKUS: bytearray → bytes konverzió!


def _add_cover_page(pdf, applicant_info, applicant_name, use_custom):
    """Fedlap - Portrait"""
    pdf.add_page()
    
    if os.path.exists('assets/logo.png'):
        try:
            pdf.image('assets/logo.png', x=85, y=20, w=40)
            pdf.ln(50)
        except:
            pdf.ln(10)
    else:
        pdf.ln(10)
    
    pdf.set_font('Roboto' if use_custom else 'Arial', 'B', 20)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(0, 15, 'Egysеges Kerelem Elemzes', align='C', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    pdf.set_font('Roboto' if use_custom else 'Arial', '', 12)
    pdf.cell(60, 8, 'Nev:', border=0)
    pdf.cell(0, 8, applicant_info.get('name', 'N/A'), border=0, ln=True)
    pdf.cell(60, 8, 'Azonosito:', border=0)
    pdf.cell(0, 8, _applicant_identifier(applicant_info), border=0, ln=True)
    pdf.ln(10)
    
    pdf.set_font('Roboto' if use_custom else 'Arial', '', 9)
    pdf.cell(0, 8, f'Generalva: {datetime.now().strftime("%Y.%m.%d %H:%M")}', align='C', ln=True)


def _add_dataframe_table(pdf, df, title, use_custom):
    """Univerzális DataFrame → PDF táblázat konvertáló"""
    pdf.add_page(orientation='L')
    
    pdf.set_font('Roboto' if use_custom else 'Arial', 'B', 12)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(3)
    
    page_width = 297 - 20
    num_cols = len(df.columns)
    # A fix, egyenlő szélességű oszlopoknál a hosszabb szövegek egymásra
    # csúsztak, különösen az összefűzött fővetés táblában, ahol a kérelmező
    # neve is megjelenik. A szélességet az oszlop szerepéhez igazítjuk.
    if num_cols:
        weights = [_pdf_column_weight(col) for col in df.columns]
        total_weight = sum(weights)
        col_widths = [page_width * weight / total_weight for weight in weights]
    else:
        col_widths = []
    
    if num_cols > 10:
        font_size = 7
    elif num_cols > 6:
        font_size = 8
    else:
        font_size = 9
    
    # FEJLÉC
    pdf.set_font('Roboto' if use_custom else 'Arial', 'B', font_size)
    pdf.set_fill_color(221, 235, 247)
    
    for col, col_width in zip(df.columns, col_widths):
        col_text = _fit_pdf_cell_text(pdf, str(col), col_width)
        pdf.cell(col_width, 7, col_text, border=1, fill=True)
    pdf.ln()
    
    # ADATSOROK
    pdf.set_font('Roboto' if use_custom else 'Arial', '', font_size)
    
    row_height = 6
    # A PDF automatikus oldaltörése ennél korábban is bekövetkezhet, ezért
    # kézzel, biztonságosan a lap alja előtt kezdjük a következő oldalt.
    max_rows_per_page = 24
    
    for idx, (_, row) in enumerate(df.iterrows()):
        if idx > 0 and idx % max_rows_per_page == 0:
            pdf.add_page(orientation='L')
            
            pdf.set_font('Roboto' if use_custom else 'Arial', 'B', font_size)
            pdf.set_fill_color(221, 235, 247)
            for col, col_width in zip(df.columns, col_widths):
                col_text = _fit_pdf_cell_text(pdf, str(col), col_width)
                pdf.cell(col_width, 7, col_text, border=1, fill=True)
            pdf.ln()
            pdf.set_font('Roboto' if use_custom else 'Arial', '', font_size)
        
        for col, col_width in zip(df.columns, col_widths):
            cell_value = str(row[col]) if pd.notna(row[col]) else ''
            cell_value = _fit_pdf_cell_text(pdf, cell_value, col_width)
            pdf.cell(col_width, row_height, cell_value, border=1)
        pdf.ln()


def _pdf_column_weight(column_name):
    """PDF oszlopszélesség súly az oszlop neve alapján."""
    name = str(column_name).strip().casefold()
    if 'kérelmező' in name or 'kerelmezo' in name:
        return 1.55
    if name in {'név', 'nev', 'hasznosítási kód megnevezése'}:
        return 1.45
    if 'település' in name or 'telepules' in name:
        return 1.15
    if 'vármegye' in name or 'varmegye' in name:
        return 1.05
    if 'blokk' in name:
        return 1.0
    if 'dátum' in name or 'datum' in name or 'telepítés' in name or 'telepites' in name:
        return 1.0
    if 'méret' in name or 'terület' in name or 'terulet' in name or '(ha)' in name:
        return 0.95
    if 'kód' in name or 'kod' in name:
        return 0.78
    if name in {'tábla', 'tabla', 'sorszám', 'sorszam'}:
        return 0.68
    if 'öko' in name or 'nitrát' in name or 'nitrat' in name:
        return 0.7
    return 0.9


def _fit_pdf_cell_text(pdf, text, width, padding=1.2):
    """A cella szövegét a tényleges betűszélesség alapján rövidíti."""
    value = str(text)
    available_width = max(0, width - padding * 2)
    if pdf.get_string_width(value) <= available_width:
        return value

    ellipsis = '...'
    if pdf.get_string_width(ellipsis) > available_width:
        return ''
    while value and pdf.get_string_width(value + ellipsis) > available_width:
        value = value[:-1]
    return value.rstrip() + ellipsis


def _add_statistics_page(pdf, extra_stats, fovetes_df, use_custom):
    """Statisztikák oldal"""
    pdf.add_page()
    
    pdf.set_font('Roboto' if use_custom else 'Arial', 'B', 14)
    pdf.cell(0, 10, 'Kiegeszito Statisztikak', ln=True)
    pdf.ln(5)
    
    pdf.set_font('Roboto' if use_custom else 'Arial', '', 11)
    pdf.cell(0, 8, f"Tablak szama: {len(fovetes_df)}", ln=True)
    pdf.cell(0, 8, f"Nitraterzeкeny terulet: {extra_stats.get('nitrate_sum', 0):.2f} ha", ln=True)
    pdf.cell(0, 8, f"Top 5 tabla: {extra_stats.get('top_5_plots_sum', 0):.2f} ha", ln=True)
    pdf.ln(5)
    
    pdf.set_font('Roboto' if use_custom else 'Arial', 'B', 11)
    pdf.cell(0, 8, 'Agrotechnikai muveletek:', ln=True)
    pdf.set_font('Roboto' if use_custom else 'Arial', '', 10)
    for tech in extra_stats.get('agrotechnics', [])[:10]:
        pdf.cell(10, 6, '-', border=0)
        pdf.cell(0, 6, tech[:100], border=0, ln=True)
    
    pdf.ln(5)
    
    pdf.set_font('Roboto' if use_custom else 'Arial', 'B', 11)
    pdf.cell(0, 8, 'Tamogatasi igenyek:', ln=True)
    pdf.set_font('Roboto' if use_custom else 'Arial', '', 10)
    for req in extra_stats.get('support_requests', [])[:10]:
        pdf.cell(10, 6, '+', border=0)
        pdf.cell(0, 6, req[:100], border=0, ln=True)


# ============================================================================
# FELDOLGOZÓ FÜGGVÉNYEK
# ============================================================================

def process_single_pdf(pdf_path, filename):
    """Egyetlen PDF feldolgozása"""
    try:
        fovetes_df = fovetes_parser.extract_fovetes_data(pdf_path)
        masodvetes_list = masodvetes_parser.extract_masodvetes_data(pdf_path)
        summary_dict = osszesitok_parser.extract_summary_data(pdf_path)
        
        processed_data = {
            "Fővetés": fovetes_df,
            "Másodvetés": masodvetes_list,
            "Hasznosítás": summary_dict.get('hasznositas', []),
            "Jogcímek": summary_dict.get('jogcim', []),
            "Blokkok": summary_dict.get('blokkok', [])
        }
        
        analysis_data = adatfeldolgozas_parser.create_analysis_report(processed_data, pdf_path)
        
        # Add tables_count to extra_stats
        if 'extra_stats' not in analysis_data:
            analysis_data['extra_stats'] = {}
        analysis_data['extra_stats']['tables_count'] = len(fovetes_df)
        
        return {
            "success": True,
            "filename": filename,
            "fovetes_df": fovetes_df,
            "masodvetes_list": masodvetes_list,
            "summary_dict": summary_dict,
            "analysis_data": analysis_data,
            "processed_data": processed_data
        }
    except Exception as e:
        return {"success": False, "filename": filename, "error": str(e)}


def generate_zip_export(results_dict):
    """ZIP készítése az egyedi exportokból és az összefűzött Excel/PDF-ből."""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for key, result in results_dict.items():
            if not result.get('success', False):
                continue
            
            is_merged = result.get('is_merged', False)
            result_filename = result.get('filename', key)
            base_filename = result_filename.rsplit('.', 1)[0] if '.' in result_filename else result_filename
            applicant_name = result.get('analysis_data', {}).get('applicant_info', {}).get('name', 'Ismeretlen')
            
            # EXCEL
            excel_tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_excel:
                    excel_tmp_path = tmp_excel.name
                
                data_to_export = {
                    "Fővetés": result['fovetes_df'],
                    "Másodvetés": result['masodvetes_list'],
                    "Jogcímek": result['summary_dict'].get('jogcim', []),
                    "Hasznosítás": result['summary_dict'].get('hasznositas', []),
                    "Hasznosítás_total": result['summary_dict'].get('hasznositas_total', 0.0),
                    "Blokkok": result['summary_dict'].get('blokkok', []),
                    "Blokkok_total": result['summary_dict'].get('blokkok_total', 0.0),
                    "Adatfeldolgozás": result['analysis_data']
                }
                
                excel_exporter.export_to_excel(
                    processed_data={result['filename']: data_to_export},
                    output_option="SEPARATE",
                    file_list=[result['filename']],
                    gui_queue=None,
                    output_path=excel_tmp_path
                )
                
                with open(excel_tmp_path, 'rb') as f:
                    zip_file.writestr(f"{base_filename}.xlsx", f.read())
            except Exception as e:
                st.warning(f"Excel hiba ({base_filename}): {e}")
            finally:
                if excel_tmp_path and os.path.exists(excel_tmp_path):
                    os.unlink(excel_tmp_path)
            
            # PDF
            try:
                pdf_bytes = generate_pdf_report(
                    result['analysis_data'], result['fovetes_df'],
                    result['masodvetes_list'], result['summary_dict'], applicant_name
                )
                zip_file.writestr(f"{base_filename}.pdf", pdf_bytes)
            except Exception as e:
                st.warning(f"PDF hiba ({base_filename}): {e}")
            
            if not is_merged:
                # Markdown és JSON az egyedi kérelmekhez érhető el.
                markdown_content = ""
                try:
                    markdown_content = markdown_exporter.generate_markdown_report(
                        result['analysis_data'], result['fovetes_df'],
                        result['masodvetes_list'], result['summary_dict'], applicant_name
                    )
                    zip_file.writestr(f"{base_filename}.md", markdown_content.encode('utf-8'))
                except Exception as e:
                    st.warning(f"Markdown hiba ({base_filename}): {e}")

                try:
                    json_data = json_transformer.generate_ek_json_response(
                        result['analysis_data'], result['fovetes_df'],
                        result['masodvetes_list'], result['summary_dict']
                    )
                    json_data["markdown"] = markdown_content
                    zip_file.writestr(
                        f"{base_filename}.json",
                        json.dumps(json_data, indent=4, ensure_ascii=False).encode('utf-8'),
                    )
                except Exception as e:
                    st.warning(f"JSON hiba ({base_filename}): {e}")
    
    zip_buffer.seek(0)
    return zip_buffer


# ============================================================================
# STREAMLIT ALKALMAZÁS
# ============================================================================

st.set_page_config(
    page_title="Mezőgazdasági Adatkinyerő v7.5",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'processed_results' not in st.session_state:
    st.session_state.processed_results = {}

# Hard Reset: Dynamic uploader key
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# CSS
st.markdown("""
    <style>
    .main-header { 
        font-size: 2.5rem; 
        font-weight: 700; 
        color: #2E7D32; 
        margin-bottom: 0.5rem; 
    }
    .sub-header { 
        font-size: 1.1rem; 
        color: #666; 
    }
    
    [data-testid="stFileUploader"] {
        border: 2px dashed #2E7D32;
        border-radius: 10px;
        padding: 20px;
        background-color: rgba(46, 125, 50, 0.05);
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #1B5E20;
        background-color: rgba(46, 125, 50, 0.1);
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.2);
        transform: scale(1.01);
    }
    
    div[data-baseweb="select"] > div {
        background-color: #2b313e !important;
        color: white !important;
        border: 1px solid #4CAF50 !important;
    }
    
    /* Selectbox - disable search typing */
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        cursor: pointer !important;
    }
    
    div[data-baseweb="menu"] {
        background-color: #2b313e !important;
    }
    
    div[aria-selected="true"], 
    li[aria-selected="true"],
    div[role="option"]:hover {
        background-color: #4CAF50 !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* Keep dialog windows centered in the visible screen while the page is scrolled. */
    [data-testid="stDialog"] > div {
        align-items: center !important;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

open_merge_dialog = False
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    
    st.markdown("## 🌾 Adatkinyerő v7.5")
    st.markdown("---")
    
    if st.session_state.processed_results:
        st.markdown("### 📦 Tömeges Export")
        
        zip_buffer = generate_zip_export(st.session_state.processed_results)
        
        has_merged_result = any(
            result.get("success") and result.get("is_merged")
            for result in st.session_state.processed_results.values()
        )
        zip_label = (
            "🗜️ ZIP Letöltése (egyedi + összefűzött)"
            if has_merged_result else "🗜️ ZIP Letöltése (egyedi kérelmek)"
        )
        st.download_button(
            label=zip_label,
            data=zip_buffer,
            file_name=f"Mezogazdasagi_Elemzesek_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )
        
        st.markdown("---")
        st.markdown("### 📁 Fájl Kiválasztása")
        
        file_keys = list(st.session_state.processed_results.keys())
        
        if file_keys:
            successful_count = sum(
                1 for key in file_keys
                if st.session_state.processed_results[key].get("success")
                and not st.session_state.processed_results[key].get("is_merged")
            )
            if successful_count >= 2:
                if st.button("🔗 Kérelmek összefűzése (Béta)", use_container_width=True):
                    for result_key in file_keys:
                        st.session_state.pop(_merge_checkbox_key(result_key), None)
                    open_merge_dialog = True

            selected_file = st.selectbox(
                "Válassz egy kérelmet:",
                options=file_keys,
                format_func=_result_label,
                label_visibility="collapsed",
                help="Válasszon a feldolgozott kérelmek közül (nem kereshető)",
                key="selected_result",
            )
        else:
            selected_file = None
        
        st.markdown("---")
        
        if st.button("🗑️ Összes Törlése (Hard Reset)", use_container_width=True):
            for result_key in st.session_state.processed_results:
                st.session_state.pop(_merge_checkbox_key(result_key), None)
            st.session_state.processed_results = {}
            st.session_state.uploader_key += 1  # Reset file uploader
            st.rerun()
    else:
        st.info("📤 Töltsön fel PDF fájlokat!")

if open_merge_dialog:
    _show_merge_dialog()

# ============================================================================
# HEADER
# ============================================================================

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<div class="main-header">🌾 Mezőgazdasági Adatkinyerő</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Egységes Kérelmek Automatikus Elemzése - v7.5 FINAL</div>', unsafe_allow_html=True)
with col2:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=100)

st.markdown("---")

# ============================================================================
# FÁJL FELTÖLTÉS - ST.FORM HASZNÁLATÁVAL (STABILITÁS!)
# ============================================================================

st.subheader("📄 PDF Fájlok Feltöltése")

lottie_url = "https://assets5.lottiefiles.com/packages/lf20_vktpl5cy.json"
lottie_animation = load_lottie_url(lottie_url)

if lottie_animation:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st_lottie(lottie_animation, height=150, key="upload_animation")

st.info("💡 **Tipp:** Több fájl feltöltéséhez jelölje ki őket egyszerre a mappájában (Ctrl+klikk vagy Shift+klikk), és húzza be őket egy csoportban!")

# JAVÍTÁS: ST.FORM HASZNÁLATA A STABILITÁSÉRT!
with st.form("upload_form", clear_on_submit=False):
    uploaded_files = st.file_uploader(
        "Húzza ide a PDF fájlokat vagy kattintson a tallózáshoz",
        type=['pdf'],
        accept_multiple_files=True,
        help="Egyszerre több fájl is feltölthető tömeges feldolgozáshoz",
        key=f"uploader_{st.session_state.uploader_key}"  # Dynamic key for hard reset
    )
    
    submitted = st.form_submit_button(
        "🌾 Elemzés Indítása",
        type="primary",
        use_container_width=True,
        on_click=_prepare_uploaded_files,
    )

st.warning("⚠️ **Adatvédelem:** A feltöltött fájlok nem kerülnek mentésre a szerveren. Az oldal bezárásával az adatok elvesznek.")
st.warning("⚠️**Figyelem:** A program a regex illesztés miatt tévedhet, minden alkalommal ellenőrizze az eredményeket!")
st.warning("⚠️ **Az összefűzés funkció, jelenleg Béta üzemmódban van, fejlesztés alatt áll, az eredményeket mindenképpen ellenőrizni kell!**")

# ============================================================================
# FELDOLGOZÁS - CSAK HA A FORM EL LETT KÜLDVE!
# ============================================================================

if submitted and uploaded_files:
    st.session_state.processed_results.pop(MERGED_RESULT_KEY, None)

    with st.status("📊 Fájlok elemzése folyamatban...", expanded=True) as status:
        progress_bar = st.progress(0)
        
        for idx, uploaded_file in enumerate(uploaded_files):
            st.write(f"⏳ Feldolgozás: **{uploaded_file.name}** ({idx+1}/{len(uploaded_files)})")
            progress_bar.progress((idx) / len(uploaded_files))
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_pdf_path = tmp_file.name
            
            try:
                result = process_single_pdf(tmp_pdf_path, uploaded_file.name)
                st.session_state.processed_results[uploaded_file.name] = result
                
                if result['success']:
                    st.success(f"✅ {uploaded_file.name}")
                else:
                    st.error(f"❌ {uploaded_file.name}: {result.get('error', 'Ismeretlen hiba')}")
            finally:
                os.unlink(tmp_pdf_path)
        
        progress_bar.progress(1.0)
        status.update(label="✅ Feldolgozás befejezve!", state="complete", expanded=False)
    
    st.balloons()
    st.rerun()

# ============================================================================
# EREDMÉNYEK
# ============================================================================

if st.session_state.processed_results and 'selected_file' in locals() and selected_file:
    result = st.session_state.processed_results[selected_file]
    
    if result.get('success'):
        st.markdown("---")
        st.header(f"📊 Elemzés: {result['analysis_data'].get('applicant_info', {}).get('name', result['filename'])}")
        
        analysis_data = result['analysis_data']
        fovetes_df = result['fovetes_df']
        masodvetes_list = result['masodvetes_list']
        summary_dict = result['summary_dict']
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Összefoglaló", "🌾 Fővetés", "🌱 Másodvetés",
            "📊 Összesítők", "💾 Export"
        ])
        
        with tab1:
            applicant = analysis_data.get('applicant_info', {})
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Név:** {applicant.get('name', 'N/A')}")
            with col2:
                st.info(f"**Azonosító:** {_applicant_identifier(applicant)}")
            
            st.markdown("---")
            st.subheader("Összesítő Táblázat")
            summary_df = analysis_data.get('summary_df', pd.DataFrame())
            if not summary_df.empty:
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("Kulcsmutatók")
            extra_stats = analysis_data.get('extra_stats', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌊 Nitrát", f"{extra_stats.get('nitrate_sum', 0):.2f} ha")
            with col2:
                st.metric("🏆 Top 5", f"{extra_stats.get('top_5_plots_sum', 0):.2f} ha")
            with col3:
                st.metric("📊 Táblák", len(fovetes_df))
        
        with tab2:
            if not fovetes_df.empty:
                st.dataframe(fovetes_df, use_container_width=True, hide_index=True)
                st.caption(f"Összesen {len(fovetes_df)} tábla")
            else:
                st.info("Nincs adat")
        
        with tab3:
            if masodvetes_list:
                masodvetes_df = _secondary_dataframe(masodvetes_list)
                st.dataframe(masodvetes_df, use_container_width=True, hide_index=True)
                st.caption(f"Összesen {len(masodvetes_list)} bejegyzés")
            else:
                st.info("Nincs adat")
        
        with tab4:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Jogcímek**")
                jogcim = summary_dict.get('jogcim', [])
                if jogcim:
                    st.dataframe(pd.DataFrame(jogcim, columns=['Jogcím', 'Terület']),
                               use_container_width=True, hide_index=True)
            with col2:
                st.markdown("**Hasznosítás**")
                haszn = summary_dict.get('hasznositas', [])
                if haszn:
                    st.dataframe(pd.DataFrame(haszn, columns=['Kód', 'Megnevezés', 'Terület']),
                               use_container_width=True, hide_index=True)
            with col3:
                st.markdown("**Blokkok**")
                blokk = summary_dict.get('blokkok', [])
                if blokk:
                    st.dataframe(pd.DataFrame(blokk, columns=['Blokk', 'Terület']),
                               use_container_width=True, hide_index=True)
        
        with tab5:
            is_merged = result.get("is_merged", False)
            export_columns = st.columns(2 if is_merged else 4)
            
            # Fájlnév a bemeneti PDF-ből
            base_filename = result['filename'].rsplit('.', 1)[0] if '.' in result['filename'] else result['filename']
            
            with export_columns[0]:
                st.markdown("### 📊 Excel Export")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    excel_tmp = tmp.name
                
                try:
                    data_to_export = {
                        "Fővetés": fovetes_df,
                        "Másodvetés": masodvetes_list,
                        "Jogcímek": summary_dict.get('jogcim', []),
                        "Hasznosítás": summary_dict.get('hasznositas', []),
                        "Hasznosítás_total": summary_dict.get('hasznositas_total', 0.0),
                        "Blokkok": summary_dict.get('blokkok', []),
                        "Blokkok_total": summary_dict.get('blokkok_total', 0.0),
                        "Adatfeldolgozás": analysis_data
                    }
                    
                    excel_exporter.export_to_excel(
                        processed_data={result['filename']: data_to_export},
                        output_option="SEPARATE",
                        file_list=[result['filename']],
                        gui_queue=None,
                        output_path=excel_tmp
                    )
                    
                    with open(excel_tmp, 'rb') as f:
                        st.download_button(
                            "⬇️ Excel Letöltés",
                            data=f.read(),
                            file_name=f"{base_filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    os.unlink(excel_tmp)
                except Exception as e:
                    st.error(f"Hiba: {e}")
            
            with export_columns[1]:
                st.markdown("### 📄 PDF Riport")
                try:
                    pdf_bytes = generate_pdf_report(
                        analysis_data, fovetes_df, masodvetes_list,
                        summary_dict, applicant.get('name', 'adat')
                    )
                    st.download_button(
                        "⬇️ PDF Letöltés",
                        data=pdf_bytes,
                        file_name=f"{base_filename}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF hiba: {e}")
            
            if not is_merged:
                with export_columns[2]:
                    st.markdown("### 📝 Markdown Export")
                    markdown_content = ""
                    try:
                        markdown_content = markdown_exporter.generate_markdown_report(
                            analysis_data, fovetes_df, masodvetes_list,
                            summary_dict, applicant.get('name', 'adat')
                        )
                        st.download_button(
                            "⬇️ Markdown Letöltés",
                            data=markdown_content.encode('utf-8'),
                            file_name=f"{base_filename}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Markdown hiba: {e}")

                with export_columns[3]:
                    st.markdown("### 🧬 JSON API Export")
                    try:
                        json_data = json_transformer.generate_ek_json_response(
                            analysis_data, fovetes_df, masodvetes_list, summary_dict
                        )
                        json_data["markdown"] = markdown_content
                        st.download_button(
                            "⬇️ JSON Letöltés",
                            data=json.dumps(json_data, indent=4, ensure_ascii=False),
                            file_name=f"{base_filename}.json",
                            mime="application/json",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"JSON hiba: {e}")
    else:
        st.error(f"❌ Hiba: {result.get('error', 'Ismeretlen hiba')}")

else:
    if not st.session_state.processed_results:
        st.info("""
        ### 📖 Gyors Útmutató
        
        1. **PDF Feltöltés** - Válasszon ki egy vagy több PDF-et
        2. **Feldolgozás** - Kattintson az "Elemzés Indítása" gombra
        3. **Navigáció** - Válasszon a bal oldali menüben
        4. **Export** - Excel vagy PDF letöltése (ZIP-ben is)
        
        **Funkciók:**
        - ✅ Tömeges feldolgozás
        - ✅ Teljes adattartalom PDF-ben
        - ✅ Magyar karakterek
        - ✅ Biztonságos (nincs szerveroldali tárolás)
        """)

st.markdown("---")
st.caption("🌾 Mezőgazdasági Adatkinyerő v8.0 FINAL | Production Ready | © 2025")
