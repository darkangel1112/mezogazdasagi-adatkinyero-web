# Fájlnév: dataprocess/fovetes_parser.py
import re
import pandas as pd
import pdfplumber

def extract_fovetes_data(pdf_path: str) -> pd.DataFrame:
    """
    Fő belépési pont a fővetés adatainak kinyeréséhez egy adott PDF fájlból.

    Args:
        pdf_path (str): A feldolgozandó PDF fájl elérési útja.

    Returns:
        pd.DataFrame: Egy DataFrame, amely a kinyert és rendezett fővetési adatokat
                      tartalmazza. Ha nincs adat, üres DataFrame-et ad vissza.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 1. Kinyerjük a blokk-szintű részleteket (vármegye, település, stb.) a térképes oldalakról.
            block_details_lookup = _extract_block_details_from_maps(pdf)
            
            # 2. Kinyerjük a "7 - Táblaadatok" szekcióból a részletes táblaadatokat.
            all_plots_data = _extract_main_table_data(pdf)

        if not all_plots_data:
            return pd.DataFrame()

        # 3. Összefésüljük és formázzuk az adatokat.
        df = pd.DataFrame(all_plots_data)
        
        # Duplikátumok eltávolítása, a legelső előfordulást tartjuk meg.
        df_final = df.drop_duplicates(subset=["Blokk", "Tábla"], keep="first").copy()
        
        # A blokk-szintű részletek hozzárendelése a táblaadatokhoz a blokk azonosító alapján.
        df_final["Vármegye"] = df_final["Blokk"].map(lambda x: block_details_lookup.get(x, {}).get("varmegye", "N/A"))
        df_final["Település"] = df_final["Blokk"].map(lambda x: block_details_lookup.get(x, {}).get("telepules", "N/A"))
        df_final["Nitrát"] = df_final["Blokk"].map(lambda x: block_details_lookup.get(x, {}).get("nitrat", "Nem"))
        df_final["Tábla"] = pd.to_numeric(df_final["Tábla"], errors="coerce").astype("Int64")
        
        # A végső oszlopok sorrendjének meghatározása a GUI-nak megfelelően.
        ordered_columns = [
            "Vármegye", "Település", "Blokk", "Tábla", "Kód", "Név", 
            "Méret (ha)", "ÖKO", "Szap.anyag", "Telepítés", 
            "Termőre ford.", "Nitrát"
        ]
        df_final = df_final.reindex(columns=ordered_columns, fill_value="N/A")
        
        return df_final
    except Exception as e:
        print(f"Hiba történt a fővetési adatok feldolgozása során: {e}")
        return pd.DataFrame()


def _extract_block_details_from_maps(pdf: pdfplumber.PDF) -> dict:
    """
    Segédfüggvény: Kinyeri a PDF térképes oldalairól a blokk-szintű adatokat.
    """
    block_details_lookup = {}
    block_pattern = re.compile(r"Blokkazonosító:\s*([A-Z0-9]+)")
    nitrat_pattern = re.compile(r"Nitrátérzékeny terület:\s*(Igen|Nem)")
    varmegye_pattern = re.compile(r"Vármegye:\s*([^\n]+)")
    telepules_pattern = re.compile(r"Település:\s*([^\n]+)")

    for page in pdf.pages:
        text = page.extract_text(x_tolerance=1, y_tolerance=1)
        if text and "A kiemelt fizikai blokk adatai:" in text:
            block_match = block_pattern.search(text)
            if block_match:
                block_id = block_match.group(1).strip()
                if block_id not in block_details_lookup:
                    nitrat_match = nitrat_pattern.search(text)
                    varmegye_match = varmegye_pattern.search(text)
                    telepules_match = telepules_pattern.search(text)
                    
                    # Tisztítás, hogy ne csússzanak bele más mezők adatai
                    varmegye_clean = varmegye_match.group(1).split("Blokkazonosító:")[0].strip() if varmegye_match else "N/A"
                    telepules_clean = telepules_match.group(1).split("Összterület:")[0].strip() if telepules_match else "N/A"
                    
                    block_details_lookup[block_id] = {
                        "nitrat": nitrat_match.group(1).strip() if nitrat_match else "N/A",
                        "varmegye": varmegye_clean,
                        "telepules": telepules_clean
                    }
    return block_details_lookup


def _extract_main_table_data(pdf: pdfplumber.PDF) -> list:
    """
    Segédfüggvény: Kinyeri a PDF-ből a "7 - Táblaadatok" szekció tartalmát.
    """
    all_plots_data = []
    
    # Az egész PDF szövegét egyetlen stringgé fűzzük a megbízhatóbb keresésért.
    full_text = "".join(page.extract_text(x_tolerance=1, y_tolerance=1) or "" for page in pdf.pages)
    
    # Ez a regex keresi a "Blokk: ... Tábla: ..." kezdetű blokkokat, és mindent
    # begyűjt a következő ilyen blokkig vagy a dokumentum más fő szekciójáig.
    block_pattern = re.compile(
        r"Blokk:\s*(.*?)\s+Tábla:\s*(.*?)\s*(?:Állapot:\s*(.*?))?\n(.*?)(?=(?:Blokk: |8 — Másodvetés/Agrotechnika|—{3,}))", 
        re.DOTALL
    )
    
    for match in block_pattern.finditer(full_text):
        block_id_str, table_id_str, status_str, content = match.groups()
        
        # Visszavont állapotú táblák kihagyása
        if status_str and "visszavont" in status_str.lower():
            continue

        plot_data = {"Blokk": block_id_str.strip(), "Tábla": table_id_str.strip()}
        
        # Alapvető, kötelező adatok kinyerése
        fonoveny_match = re.search(r"Főnövény hasznosítási kód:\s*([A-Z0-9]+)\s*(.*?)\n", content)
        terulet_match = re.search(r"Tábla igényelt terület \(ha\):\s*([\d,.]+)", content)
        
        # Ha a kötelező adatok hiányoznak, a blokk érvénytelen, kihagyjuk
        if not (fonoveny_match and terulet_match):
            continue

        plot_data["Kód"] = fonoveny_match.group(1).strip()
        plot_data["Név"] = fonoveny_match.group(2).strip().split("Kockázatkezelés")[0].strip()
        
        try:
            plot_data["Méret (ha)"] = float(terulet_match.group(1).strip().replace(",", "."))
        except (ValueError, AttributeError):
            plot_data["Méret (ha)"] = 0.0
        
        # Opcionális mezők kinyerése (ha léteznek)
        optional_fields = {
            "ÖKO": r"Ökológiai gazdálkodás:\s*([A-Za-zÁ-ú]+)",
            "Szap.anyag": r"Szaporítóanyag célra:\s*([A-Za-zÁ-ú]+)",
            "Telepítés": r"Főnövény vetési/telepítési időpontja:\s*([\d\.]+)",
            "Termőre ford.": r"Ültetvény termőre fordulásának éve:\s*(\d{4})"
        }
        
        for key, pattern in optional_fields.items():
            match_obj = re.search(pattern, content)
            plot_data[key] = match_obj.group(1).strip() if match_obj else "N/A"
            
        all_plots_data.append(plot_data)

    return all_plots_data