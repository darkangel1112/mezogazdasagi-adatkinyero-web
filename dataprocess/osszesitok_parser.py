# Fájlnév: dataprocess/osszesitok_parser.py
import re
import pdfplumber

def extract_summary_data(pdf_path: str) -> dict:
    """
    Fő belépési pont a három összesítő táblázat adatainak kinyeréséhez.
    
    Args:
        pdf_path (str): A feldolgozandó PDF fájl elérési útja.
        
    Returns:
        dict: Egy szótár, amely tartalmazza a három táblázat adatait és az
              összesített értékeket.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        # Regex-ek, amelyek a következő táblázat címénél vagy egy új fejezetnél megállnak.
        jogcim_regex = r"Támogatási jogcímek és AKG célprogramok szerint\s*\n(.*?)(?=Területek összesítése hasznosítási adatok szerint)"
        hasznositas_regex = r"Hasznosítási adatok szerint.*?\(főnövény, másodvetés, agrotechnika\)\s*\n(.*?)(?=Területek összesítése blokkhasználat szerint)"
        blokk_regex = r"Területek összesítése blokkhasználat szerint\s*\n(.*?)(?=\n\d+\s*—|\n[A-Z\s]+ nyilatkozat|\Z)"

        jogcim_match = re.search(jogcim_regex, full_text, re.DOTALL | re.IGNORECASE)
        hasznositas_match = re.search(hasznositas_regex, full_text, re.DOTALL | re.IGNORECASE)
        blokk_match = re.search(blokk_regex, full_text, re.DOTALL | re.IGNORECASE)

        jogcim_data = _parse_jogcim_table(jogcim_match.group(1)) if jogcim_match else []
        hasznositas_data, hasznositas_total = _parse_hasznositas_table(hasznositas_match.group(1)) if hasznositas_match else ([], 0.0)
        blokk_data, blokk_total = _parse_blokk_table(blokk_match.group(1)) if blokk_match else ([], 0.0)

        return {
            'jogcim': jogcim_data,
            'hasznositas': hasznositas_data,
            'hasznositas_total': hasznositas_total,
            'blokkok': blokk_data,
            'blokkok_total': blokk_total
        }
    except Exception as e:
        print(f"Hiba történt az összesítő adatok feldolgozása során: {e}")
        return {}

def _parse_jogcim_table(text_block: str) -> list:
    """Feldolgozza a támogatási jogcímek táblázatának szövegét."""
    data = []
    lines = text_block.strip().split('\n')
    # Kihagyjuk a fejlécet, ha tartalmazza a kulcsszavakat
    if lines and ("Támogatási jogcímek" in lines[0] or "Igényelt terület" in lines[0]):
        lines = lines[1:]
    
    for line in lines:
        # A minta: bármilyen szöveg, majd szóközök, és a végén egy szám.
        match = re.match(r'^(.*?)\s+([\d,.]+)$', line.strip())
        if match:
            nev, terulet_str = match.groups()
            try:
                terulet = float(terulet_str.replace(',', '.'))
                # Formázás tizedesvesszővel a GUI számára
                data.append([nev.strip(), f"{terulet:.4f}".replace('.', ',')])
            except ValueError:
                continue
    return data

def _parse_hasznositas_table(text_block: str) -> tuple:
    """Feldolgozza a hasznosítási adatok táblázatának szövegét."""
    data = []
    total_ha = 0.0
    lines = text_block.strip().split('\n')
    if lines and ("Hasznosítás kód" in lines[0] or "Igényelt terület" in lines[0]):
        lines = lines[1:]

    # A minta: 3 betű, 2 szám, szóköz, majd a név, végül a terület
    pattern = re.compile(r"^([A-Z]{3}\d{2})\s+(.+?)\s+([\d,.]+)$")
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            kod, megnevezes, terulet_str = match.groups()
            try:
                terulet = float(terulet_str.replace(',', '.'))
                total_ha += terulet
                data.append([kod, megnevezes.strip(), f"{terulet:.4f}".replace('.', ',')])
            except ValueError:
                continue
    return data, total_ha
        
def _parse_blokk_table(text_block: str) -> tuple:
    """Feldolgozza a blokkhasználati adatok táblázatának szövegét."""
    data = []
    total_ha = 0.0
    lines = text_block.strip().split('\n')
    if lines and ("Blokk" in lines[0] or "Igényelt terület" in lines[0]):
        lines = lines[1:]
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2:
            blokk_id, terulet_str = parts
            
            # Szigorú ellenőrzés a blokk azonosító formátumára
            has_letter = any(c.isalpha() for c in blokk_id)
            has_digit = any(c.isdigit() for c in blokk_id)
            
            if len(blokk_id) == 8 and has_letter and has_digit:
                try:
                    terulet = float(terulet_str.replace(',', '.'))
                    total_ha += terulet
                    data.append([blokk_id, f"{terulet:.4f}".replace('.', ',')])
                except ValueError:
                    continue
    return data, total_ha