# Fájlnév: dataprocess/adatfeldgozas_parser.py
import pandas as pd
import re
import pdfplumber

def _extract_applicant_data(pdf_path: str) -> dict:
    """
    Kinyeri a kérelmező/kedvezményezett nevét és támogatási azonosítóját a PDF-ből.
    Ez a verzió kezeli a sortörés nélküli és a több kötőjeles formátumot is.
    """
    applicant_info = {'name': 'N/A', 'mak_id': 'N/A'}
    
    # Robusztus regex minták, amelyek több formátumot is lefednek
    name_pattern = re.compile(
        r"(?:Kedvezményezett neve|4\s*-*\s*Kedvezményezett adatai\s*Név):\s*([^\n\r]+)", 
        re.IGNORECASE | re.DOTALL
    )
    id_pattern = re.compile(
        r"A kérelmező támogatási azonosítója:\s*(\d{10})|Támogatási azonosító:\s*(\d{10})"
    )

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Az első néhány oldalon keressük az adatokat
            for page in pdf.pages[:3]:
                text = page.extract_text(x_tolerance=2, layout=True)
                if not text: continue
                
                # Név keresése
                if applicant_info['name'] == 'N/A':
                    name_match = name_pattern.search(text)
                    if name_match:
                        # A regex több csoportot is tartalmazhat, megtaláljuk az első nem üres találatot
                        name = next((g for g in name_match.groups() if g is not None), None)
                        if name:
                            applicant_info['name'] = name.strip()
                
                # Azonosító keresése
                if applicant_info['mak_id'] == 'N/A':
                    id_match = id_pattern.search(text)
                    if id_match:
                        # A regex több csoportot is tartalmazhat, megtaláljuk az első nem üres találatot
                        mak_id = next((g for g in id_match.groups() if g is not None), None)
                        if mak_id:
                            applicant_info['mak_id'] = mak_id.strip()
                
                if applicant_info['name'] != 'N/A' and applicant_info['mak_id'] != 'N/A':
                    break
    except Exception as e:
        print(f"Hiba a kérelmező adatainak kinyerése során: {e}")
    
    return applicant_info

def _extract_support_requests(pdf_path: str) -> list:
    """
    Kinyeri a kipipált támogatási igényeket a PDF-ből.
    """
    checked_items = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            target_page_index = -1
            
            for i, page in enumerate(pdf.pages[:4]):
                text_content = page.extract_text()
                if text_content and ("Támogatási/kifizetési igények" in text_content):
                    target_page_index = i
                    break
            
            if target_page_index == -1:
                return []

            page = pdf.pages[target_page_index]
            text = page.extract_text()
            
            if not text:
                return []
            
            # Csak a "q4" karakterekkel jelölt elemeket keressük (ezek a kipipáltak)
            pattern = re.compile(r'q4\s+([^\n\rq]+)', re.MULTILINE)
            
            matches = pattern.findall(text)
            for match in matches:
                clean_line = match.strip()
                clean_line = re.sub(r'\s+', ' ', clean_line)
                
                if len(clean_line) > 3:
                    checked_items.append(clean_line)
            
            # Ha nem találtunk semmit, próbáljuk alternatív módszerrel
            if not checked_items:
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('q4'):
                        # A következő sorban keressük a támogatás nevét
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if len(next_line) > 3 and not next_line.startswith('q'):
                                checked_items.append(next_line)
                            
    except Exception as e:
        print(f"Hiba a támogatási igények kinyerése során: {e}")
    
    return checked_items

def create_analysis_report(processed_data: dict, pdf_path: str) -> dict:
    """
    Elkészíti a vezetői összefoglaló riportot a már feldolgozott adatokból.
    """
    applicant_info = _extract_applicant_data(pdf_path)
    
    fovetes_df = processed_data.get("Fővetés")
    masodvetes_list = processed_data.get("Másodvetés", [])
    hasznositas_list = processed_data.get("Hasznosítás", [])

    if fovetes_df is None or fovetes_df.empty:
        return {"error": "A riport készítéséhez hiányoznak a Fővetés adatok."}

    fovetes_sum = fovetes_df.groupby('Név')['Méret (ha)'].sum().reset_index()
    fovetes_sum.rename(columns={'Név': 'Megnevezés', 'Méret (ha)': 'Fővetés (Számított)'}, inplace=True)

    masodvetes_df = pd.DataFrame(masodvetes_list, columns=['Blokk', 'Tábla', 'Sorszám', 'Típus', 'Megnevezés', 'Anyag', 'Növény kód', 'Terület (ha)'])
    masodvetes_df['Terület (ha)'] = pd.to_numeric(masodvetes_df['Terület (ha)'], errors='coerce').fillna(0)
    
    masodvetes_sum = masodvetes_df[masodvetes_df['Típus'] == 'Másodvetés'].groupby('Anyag')['Terület (ha)'].sum().reset_index()
    masodvetes_sum.rename(columns={'Anyag': 'Megnevezés', 'Terület (ha)': 'Másodvetés (Számított)'}, inplace=True)
    
    hasznositas_df = pd.DataFrame(hasznositas_list, columns=['Kód', 'Megnevezés', 'Terület (Eredeti)'])
    hasznositas_df['Terület (Eredeti)'] = pd.to_numeric(hasznositas_df['Terület (Eredeti)'].str.replace(',', '.'), errors='coerce').fillna(0)

    all_plants = pd.concat([
        hasznositas_df['Megnevezés'],
        fovetes_sum['Megnevezés'],
        masodvetes_sum['Megnevezés']
    ]).unique()
    
    report_df = pd.DataFrame(all_plants, columns=['Megnevezés'])
    report_df = pd.merge(report_df, hasznositas_df, on='Megnevezés', how='left')
    report_df = pd.merge(report_df, fovetes_sum, on='Megnevezés', how='left')
    report_df = pd.merge(report_df, masodvetes_sum, on='Megnevezés', how='left')
    
    report_df.fillna({'Terület (Eredeti)': 0.0, 'Fővetés (Számított)': 0.0, 'Másodvetés (Számított)': 0.0, 'Kód': 'N/A'}, inplace=True)
    report_df['Összesen (Számított)'] = report_df['Fővetés (Számított)'] + report_df['Másodvetés (Számított)']
    
    final_columns = ['Kód', 'Megnevezés', 'Terület (Eredeti)', 'Fővetés (Számított)', 'Másodvetés (Számított)', 'Összesen (Számított)']
    report_df = report_df[final_columns]
    
    sum_row = pd.DataFrame({
        'Kód': [''],
        'Megnevezés': ['Összesen:'],
        'Terület (Eredeti)': [report_df['Terület (Eredeti)'].sum()],
        'Fővetés (Számított)': [report_df['Fővetés (Számított)'].sum()],
        'Másodvetés (Számított)': [report_df['Másodvetés (Számított)'].sum()],
        'Összesen (Számított)': [report_df['Összesen (Számított)'].sum()]
    })
    report_df = pd.concat([report_df, sum_row], ignore_index=True)
    
    nitrat_sum = fovetes_df[fovetes_df['Nitrát'] == 'Igen']['Méret (ha)'].sum()
    top_5_sum = fovetes_df.nlargest(5, 'Méret (ha)')['Méret (ha)'].sum()
    agrotechnika_list = masodvetes_df[masodvetes_df['Típus'] == 'Agrotechnika']['Megnevezés'].unique().tolist()
    
    support_requests = _extract_support_requests(pdf_path)
    
    analysis_data = {
        "applicant_info": applicant_info,
        "summary_df": report_df,
        "extra_stats": {
            "nitrate_sum": nitrat_sum,
            "top_5_plots_sum": top_5_sum,
            "agrotechnics": agrotechnika_list if agrotechnika_list else ["Nincs agrotechnikai művelet."],
            "support_requests": support_requests if support_requests else ["Nincs támogatási igény kiválasztva."]
        }
    }
    
    return analysis_data