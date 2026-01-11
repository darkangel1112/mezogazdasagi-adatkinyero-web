from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Response
from fastapi.responses import FileResponse
import os
import tempfile
import zipfile
from io import BytesIO
import pandas as pd
from unidecode import unidecode

import traceback
import sys

# Saját modulok importálása
from src.dataprocess import fovetes_parser, masodvetes_parser, osszesitok_parser, adatfeldolgozas_parser
from src.dataexport import excel_exporter, markdown_exporter

# Az app.py-ban lévő PDF generáló logika másolata (hogy ne függjön st-től)
from fpdf import FPDF

# Egyszerű API KEY - Élesben érdemes környezeti változóba tenni
API_KEY = os.getenv("API_KEY", "mezo-secret-2024")

app = FastAPI(title="Mezőgazdasági Adatkinyerő API", version="1.0.0")

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Érvénytelen API kulcs")
    return True

@app.get("/")
async def root():
    return {"message": "Mezőgazdasági Adatkinyerő API fut", "status": "online"}

@app.post("/analyze")
async def analyze_pdf(
    file: UploadFile = File(...), 
    x_api_key: str = Header(None)
):
    print(f"DEBUG: Bejövő kérés: {file.filename}", flush=True)
    verify_api_key(x_api_key)
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Csak PDF fájlok fogadhatók")

    # Ideiglenes fájlba mentés a feldolgozáshoz
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    print(f"DEBUG: Temp fájl mentve: {tmp_path}", flush=True)

    try:
        # PÉLDÁNYOSÍTOTT FELDOLGOZÁS (mint az app.py-ban)
        # 1. Nyers adatok kinyerése
        print("DEBUG: Fővetés adatok kinyerése...", flush=True)
        fovetes_df = fovetes_parser.extract_fovetes_data(tmp_path)
        print(f"DEBUG: Fővetés kész. Adatsorok: {len(fovetes_df)}", flush=True)
        
        print("DEBUG: Másodvetés adatok kinyerése...", flush=True)
        masodvetes_list = masodvetes_parser.extract_masodvetes_data(tmp_path)
        print(f"DEBUG: Másodvetés kész. Adatsorok: {len(masodvetes_list)}", flush=True)
        
        print("DEBUG: Összesítők kinyerése...", flush=True)
        summary_dict = osszesitok_parser.extract_summary_data(tmp_path)
        print("DEBUG: Összesítők kész.", flush=True)
        
        processed_data = {
            "Fővetés": fovetes_df,
            "Másodvetés": masodvetes_list,
            "Hasznosítás": summary_dict.get('hasznositas', []),
            "Jogcímek": summary_dict.get('jogcim', []),
            "Blokkok": summary_dict.get('blokkok', [])
        }
        
        # 2. Elemzés és összesítés (közös logika a GUI-val)
        print("DEBUG: Elemzési riport készítése (create_analysis_report)...", flush=True)
        analysis_data = adatfeldolgozas_parser.create_analysis_report(processed_data, tmp_path)
        print("DEBUG: Elemzési riport kész.", flush=True)
        
        # HIBAJAVÍTÁS: tables_count hozzáadása manuálisan (mint az app.py-ban)
        if 'extra_stats' not in analysis_data:
            analysis_data['extra_stats'] = {}
        analysis_data['extra_stats']['tables_count'] = len(fovetes_df)
        
        # Hiba ellenőrzés
        if "error" in analysis_data:
            print(f"DEBUG: Logikai hiba az elemzésben: {analysis_data['error']}", flush=True)
            raise HTTPException(status_code=422, detail=analysis_data["error"])
            
        applicant_info = analysis_data.get('applicant_info', {})
        summary_df = analysis_data.get('summary_df', pd.DataFrame())
        extra_stats = analysis_data.get('extra_stats', {})

        # 3. Exportok generálása
        # Markdown
        print("DEBUG: Markdown generálása...", flush=True)
        markdown_content = markdown_exporter.generate_markdown_report(
            analysis_data, fovetes_df, masodvetes_list, summary_dict, applicant_info.get('name', 'N/A')
        )
        print("DEBUG: Markdown kész.", flush=True)
        
        # Visszaküldünk egy JSON-t az adatokkal és a Markdown szöveggel
        return {
            "success": True,
            "applicant": applicant_info.get('name', 'N/A'),
            "markdown": markdown_content,
            "summary": {
                "total_area": summary_dict.get("hasznositas_total", 0.0),
                "tables_count": analysis_data.get("extra_stats", {}).get("tables_count", 0)
            }
        }

    except Exception as e:
        error_msg = f"Feldolgozási hiba: {str(e)}"
        print(f"CRITICAL ERROR: {error_msg}", flush=True)
        traceback.print_exc()
        # Visszaadjuk a teljes traceback-et a válaszban a debuggoláshoz
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass
