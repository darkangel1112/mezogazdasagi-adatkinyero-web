# Fájlnév: dataprocess/adatfeldgozas_parser.py
import pandas as pd
import re
import pdfplumber

def _extract_applicant_data(pdf_path: str) -> dict:
    """
    Kinyeri a kérelmező/kedvezményezett nevét és támogatási azonosítóját a PDF-ből.
    Ez a verzió kezeli a sortörés nélküli és a több kötőjeles formátumot is.
    """
    applicant_info = {'name': 'N/A', 'support_id': 'N/A'}
    
    # JAVÍTVA (v2): Kódolás-független regex — minden ékezetes karaktert '.' ponttal helyettesít.
    # A PDF Windows-1250 kódolású → a pdfplumber torzítja pl: é→Ú, ő→§, á→ß, í→Ý, ó→ˇ
    # Minta: 'A k.relmez. t.mogat.si azonos.t.ja:' → CSAK a kérelmező sorára illeszt
    # (a beadó sora 'A beadˇ...' alakú, így nem keveri össze)
    name_pattern = re.compile(
        r"(?:Kedvem.{1,30}neve|4\s*-*\s*.{1,30}N.v):\s*([^\n\r]+)", 
        re.IGNORECASE | re.DOTALL
    )
    id_pattern = re.compile(
        r"A k.relmez. t.mogat.si azonos.t.ja:\s*(\d{10})",
        re.IGNORECASE
    )

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:3]:
                # Két módban próbáljuk: sima, majd layout=True
                for extract_kwargs in [{}, {"x_tolerance": 2, "layout": True}]:
                    text = page.extract_text(**extract_kwargs)
                    if not text:
                        continue

                    # Név keresése
                    if applicant_info['name'] == 'N/A':
                        name_match = name_pattern.search(text)
                        if name_match:
                            name = next((g for g in name_match.groups() if g is not None), None)
                            if name:
                                applicant_info['name'] = name.strip()

                    # Azonosító keresése
                    if applicant_info['support_id'] == 'N/A':
                        id_match = id_pattern.search(text)
                        if id_match:
                            applicant_info['support_id'] = id_match.group(1).strip()

                    # Ha megvan mindkettő, nem kell több kör
                    if applicant_info['name'] != 'N/A' and applicant_info['support_id'] != 'N/A':
                        break

                if applicant_info['name'] != 'N/A' and applicant_info['support_id'] != 'N/A':
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

    if 'AKG' in fovetes_df.columns:
        akg_sum = fovetes_df[
            fovetes_df['AKG'].astype(str).str.lower().str.strip() == 'igen'
        ].groupby('Név')['Méret (ha)'].sum().reset_index()
    else:
        akg_sum = pd.DataFrame(columns=['Név', 'Méret (ha)'])
    akg_sum.rename(columns={'Név': 'Megnevezés', 'Méret (ha)': 'AKG'}, inplace=True)

    if 'ÖKO' in fovetes_df.columns:
        oko_sum = fovetes_df[
            fovetes_df['ÖKO'].astype(str).str.lower().str.strip() == 'igen'
        ].groupby('Név')['Méret (ha)'].sum().reset_index()
    else:
        oko_sum = pd.DataFrame(columns=['Név', 'Méret (ha)'])
    oko_sum.rename(columns={'Név': 'Megnevezés', 'Méret (ha)': 'ÖKO'}, inplace=True)

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
    report_df = pd.merge(report_df, akg_sum, on='Megnevezés', how='left')
    report_df = pd.merge(report_df, oko_sum, on='Megnevezés', how='left')

    report_df.fillna({
        'Terület (Eredeti)': 0.0,
        'Fővetés (Számított)': 0.0,
        'Másodvetés (Számított)': 0.0,
        'AKG': 0.0,
        'ÖKO': 0.0,
        'Kód': 'N/A'
    }, inplace=True)
    report_df['Összesen (Számított)'] = report_df['Fővetés (Számított)'] + report_df['Másodvetés (Számított)']
    
    final_columns = ['Kód', 'Megnevezés', 'Terület (Eredeti)', 'Fővetés (Számított)', 'Másodvetés (Számított)', 'Összesen (Számított)', 'AKG', 'ÖKO']
    report_df = report_df[final_columns]
    
    # KRITIKUS: Az összegeket az "Összesen:" sor hozzáadása ELŐTT kell kiszámolni!
    fovetes_total = report_df['Fővetés (Számított)'].sum()
    masodvetes_total = report_df['Másodvetés (Számított)'].sum()
    
    sum_row = pd.DataFrame({
        'Kód': [''],
        'Megnevezés': ['Összesen:'],
        'Terület (Eredeti)': [report_df['Terület (Eredeti)'].sum()],
        'Fővetés (Számított)': [fovetes_total],
        'Másodvetés (Számított)': [masodvetes_total],
        'Összesen (Számított)': [report_df['Összesen (Számított)'].sum()],
        'AKG': [report_df['AKG'].sum()],
        'ÖKO': [report_df['ÖKO'].sum()]
    })
    report_df = pd.concat([report_df, sum_row], ignore_index=True)
    
    nitrat_sum = fovetes_df[fovetes_df['Nitrát'] == 'Igen']['Méret (ha)'].sum()
    top_5_sum = fovetes_df.nlargest(5, 'Méret (ha)')['Méret (ha)'].sum()
    agrotechnika_list = masodvetes_df[masodvetes_df['Típus'] == 'Agrotechnika']['Megnevezés'].unique().tolist()
    
    # Kinyerjük a támogatási adatokat a már feldolgozott "Jogcímek" listából (Név, Terület)
    # Ha ez megvan, akkor ezt használjuk, mert pontosabb és tartalmazza a területet is.
    support_requests_struct = []
    jogcim_data = processed_data.get("Jogcímek", [])
    
    if jogcim_data:
        for item in jogcim_data:
            if len(item) >= 2:
                name = item[0]
                area_str = str(item[1]).replace(',', '.')
                try:
                    area = float(area_str)
                except:
                    area = 0.0
                support_requests_struct.append({'name': name, 'area': area})
    else:
        # Fallback: Régi módszer (csak nevek), terület 0.0
        # CSAK akkor használjuk a PDF-ből kivehető "q4" pipákat fallbacknek, ha NINCS jogcím adat.
        raw_requests = _extract_support_requests(pdf_path)
        for req in raw_requests:
            support_requests_struct.append({'name': req, 'area': 0.0})

    # ÚJ: A JSON "requests" mezőjéhez MINDIG kinyerjük a PDF-ből a pipált listát.
    # Ez független attól, hogy van-e táblázatos jogcím adat.
    # Így nem rontjuk el a meglévő logikát (PDF/Excel/Fallback), de elérhetővé tesszük az adatot.
    all_checked_requests = _extract_support_requests(pdf_path)

    analysis_data = {
        "applicant_info": applicant_info,
        "summary_df": report_df,
        "extra_stats": {
            "nitrate_sum": nitrat_sum,
            "top_5_plots_sum": top_5_sum,
            "fovetes_sum": fovetes_total,
            "masodvetes_sum": masodvetes_total,
            "agrotechnics": agrotechnika_list if agrotechnika_list else ["Nincs agrotechnikai művelet."],
            "support_requests": support_requests_struct,
            "checkbox_list": all_checked_requests  # <--- ÚJ MEZŐ A JSON SZÁMÁRA
        }
    }
    
    return analysis_data
