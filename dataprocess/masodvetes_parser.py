# Fájlnév: dataprocess/masodvetes_parser.py
import re
import pdfplumber

def extract_masodvetes_data(pdf_path: str) -> list:
    """
    Fő belépési pont a másodvetés/agrotechnika adatainak kinyeréséhez.
    
    Args:
        pdf_path (str): A feldolgozandó PDF fájl elérési útja.
        
    Returns:
        list: Lista, amelyben a kinyert adatsorokat tartalmazó listák vannak.
              Ha nincs adat, üres listát ad vissza.
    """
    data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 1. Az összes oldal szövegét kinyerjük és karaktertisztítást végzünk.
            full_text_pages = [_clean_text(page.extract_text()) for page in pdf.pages if page.extract_text()]
            full_cleaned_text = "\n".join(full_text_pages)

            # 2. Megkeressük a "Másodvetés/Agrotechnika" szekció kezdetét.
            masodvetes_section_start = full_cleaned_text.lower().find("másodvetés/agrotechnika")
            if masodvetes_section_start == -1:
                return [] # Ha nincs ilyen szekció, nincs teendő.
            
            # Csak a releváns szövegrésszel dolgozunk tovább.
            relevant_text_segment = full_cleaned_text[masodvetes_section_start:]
            
            # 3. A szöveget blokkokra bontjuk a "Blokk: ... Tábla: ..." minta alapján.
            raw_blocks_split = re.split(r'(Blokk:\s*[A-Z0-9]+\s+Tábla:\s*\d+/\d+)', relevant_text_segment)
            
            # 4. Végigiterálunk a blokkokon és feldolgozzuk őket.
            for i in range(1, len(raw_blocks_split), 2):
                if i + 1 < len(raw_blocks_split):
                    # Összefűzzük a blokk fejlécét és a tartalmát.
                    current_operation_block = f"{raw_blocks_split[i].strip()}\n{raw_blocks_split[i+1].strip()}"
                    entry_data = _parse_masodvetes_entry(current_operation_block)
                    if entry_data:
                        data.append(entry_data)
        return data
    except Exception as e:
        print(f"Hiba történt a másodvetés adatok feldolgozása során: {e}")
        return []

def _clean_text(text: str) -> str:
    """Segédfüggvény a speciális karakterhibák javítására."""
    if not text: return ""
    replacements = {
        'È': 'é', 'Û': 'ő', '·': 'á', 'ı': 'í', 'Ì': 'í', '¸': 'ü', 'ˆ': 'ö',
        '†': '', '£': 'Á', 'ÈrintÈs': 'érintés', 'k·r': 'kár', 'ter¸let': 'terület',
        'sorsz·ma': 'sorszáma', 'tÌpusa': 'típusa', 'idıpontja': 'időpontja',
        'alkalmaz·sa': 'alkalmazása', 'kÈszÌtmÈny': 'készítmény',
        'megnevezÈse': 'megnevezése', 'Kasz·l·s': 'Kaszálás', 'M·sodvetÈs': 'Másodvetés',
        'Agrotechnika': 'Agrotechnika', 'gyepesÌtÈssel': 'gyepesítéssel',
        'Sorkˆztakar·s': 'Sorköztakarás', 'KondÌcion·lÛ': 'Kondicionáló',
        'NitrogÈnmegkˆtı': 'Nitrogénmegkötő', 'kÈszÌtmÈnyek': 'készítmények',
        'sz·rsÈrtı': 'szársértő', 'nÈlk¸li': 'nélküli', 'haszn·lat·val': 'használatával',
        'altern·lÛ': 'alternáló', 'tervezett': 'tervezett', 'vetÈsi': 'vetési',
        'hasznosÌt·si': 'hasznosítási', 'form·ja': 'formája', 'jelentısÈg˚': 'jelentőségű',
        '÷kolÛgiai': 'Ökológiai', 'laz·s': 'lazítás', 'KˆzÈpmÈly': 'Középmély',
        'lazÌt·s': 'lazítás', 'MellÈktermÈk': 'Melléktermék',
        'visszaforgatasa': 'visszaforgatása', 'Ist·llÛtr·gya': 'Istállótrágya',
        'kijuttat·sa': 'kijuttatása'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def _extract_after_keyword(text: str, keyword: str, stop_words: list = None, colon_optional: bool = False) -> str:
    """Általános kulcsszó utáni szöveg kinyerő függvény."""
    if stop_words is None:
        stop_words = ["Igényelt", "Kijuttatás", "Másodvetés", "Agrotechnika", "Hasznosítás"]
    
    # Kulcsszó után minden a sortörésig vagy stop szóig
    stop_pattern = "|".join([re.escape(word) for word in stop_words])
    
    if colon_optional:
        # Opcionális kettőspont - kettősponttal vagy anélkül
        pattern = rf'{re.escape(keyword)}:?\s*([^\n\r]+?)(?=\s*(?:{stop_pattern})|\s*$)'
    else:
        # Kötelező kettőspont
        pattern = rf'{re.escape(keyword)}:\s*([^\n\r]+?)(?=\s*(?:{stop_pattern})|\s*$)'
    
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "N/A"

def _parse_masodvetes_entry(block_text: str) -> list or None:
    """Egyetlen másodvetés/agrotechnika bejegyzést dolgoz fel a szöveges blokkból."""
    try:
        # Alapadatok kinyerése
        blokk_match = re.search(r'Blokk:\s*([A-Z0-9]+).*?Tábla:\s*(\d+)/(\d+)', block_text.split('\n')[0])
        if not blokk_match: 
            return None
        
        blokk_id, tabla_id, muvelet_szam_part = blokk_match.groups()
        muvelet_szam = f"{tabla_id}/{muvelet_szam_part}"
        
        # Sorszám kinyerése (alternatív)
        sorszam_match = re.search(r'sorszáma:\s*(\d+/\d+)', block_text)
        if sorszam_match:
            muvelet_szam = sorszam_match.group(1)
        
        # Terület kinyerése
        terulet_match = re.search(r'Igényelt terület \(ha\):\s*([\d,\.]+)', block_text)
        terulet = terulet_match.group(1).replace(',', '.') if terulet_match else "N/A"
        
        # Kezdeti értékek
        tipus, megnevezes, kijuttatott_anyag, noveny_kod = "N/A", "N/A", "N/A", "N/A"
        
        # Típus meghatározás és adatok kinyerése
        if "Agrotechnika típusa:" in block_text:
            tipus = "Agrotechnika"
            megnevezes = _extract_agrotechnika_type(block_text)
            # Kondicionáló készítmény keresése
            if "Kondicionáló" in block_text:
                kijuttatott_anyag = _extract_kondicionalo_nev(block_text)
                
        elif "Másodvetés típusa:" in block_text:
            tipus = "Másodvetés"
            megnevezes = _extract_masodvetes_type(block_text)
            kijuttatott_anyag, noveny_kod = _extract_masodvetes_noveny(block_text)
        
        return [blokk_id, tabla_id, muvelet_szam, tipus, megnevezes, kijuttatott_anyag, noveny_kod, terulet]
        
    except Exception:
        return None

def _extract_kondicionalo_nev(text: str) -> str:
    """Kinyeri a kondicionáló készítmény nevét."""
    # Elsődleges módszer - kulcsszó alapú kinyerés
    kondicionalo_nev = _extract_after_keyword(text, "Kondicionáló készítmény megnevezése", 
                                            ["Kijuttatás", "Igényelt", "Másodvetés", "Agrotechnika"],
                                            colon_optional=True)
    
    if kondicionalo_nev != "N/A":
        # További tisztítás
        cleaned_name = re.sub(r'\s*(?:WDGT|Egy\s+elem).*', '', kondicionalo_nev, flags=re.IGNORECASE).strip()
        return cleaned_name if cleaned_name else "N/A"
    
    # Fallback - egyszerű direkt keresés (ez oldotta meg a problémát)
    direct_match = re.search(r'Kondicionáló készítmény megnevezése\s*:?\s*([^\n\r]+)', text, re.IGNORECASE)
    if direct_match:
        direct_result = direct_match.group(1).strip()
        return direct_result
    
    return "N/A"

def _extract_agrotechnika_type(text: str) -> str:
    """Kinyeri az agrotechnika típusát kulcsszó alapú kinyeréssel."""
    # Kulcsszó alapú kinyerés - bármi az "Agrotechnika típusa:" után
    return _extract_after_keyword(text, "Agrotechnika típusa", 
                                ["Igényelt", "Kijuttatás", "Kaszálás tervezett", "Kondicionáló készítmény"])

def _extract_masodvetes_type(text: str) -> str:
    """Kinyeri a másodvetés típusát kulcsszó alapú kinyeréssel."""
    # Kulcsszó alapú kinyerés - bármi a "Másodvetés típusa:" után
    return _extract_after_keyword(text, "Másodvetés típusa", 
                                ["Hasznosítás", "Igényelt", "Vegyes hasznosítás"])

def _extract_masodvetes_noveny(text: str) -> tuple:
    """Kinyeri a másodvetéshez tartozó növény nevét és kódját."""
    # Egyszerű hasznosítás keresése: "Hasznosítás: ABC12 Növény név"
    hasznositas_match = re.search(r'Hasznosítás:\s*([A-Z0-9]+)\s+([^\n\r]+?)(?=\s*(?:Vegyes|Másodvetés|Igényelt|$))', text, re.IGNORECASE)
    if hasznositas_match:
        kod = hasznositas_match.group(1)
        nev = hasznositas_match.group(2).strip()
        return nev, kod
    
    # Vegyes hasznosítás keresése: "Vegyes hasznosítás [A-Z]: ABC12 Növény név"
    vegyes_matches = re.findall(r'Vegyes hasznosítás [A-Z]:\s*([A-Z0-9]+)\s+([^\n\r]+?)(?=\s*(?:Vegyes hasznosítás|Igényelt|Másodvetés|$))', text, re.IGNORECASE)
    if vegyes_matches:
        nevek = []
        kodok = []
        for kod, nev in vegyes_matches:
            # Tisztítás
            clean_nev = re.sub(r'\s*(?:Igényelt|Másodvetés|tervezett).*', '', nev.strip())
            if clean_nev:
                nevek.append(clean_nev)
                kodok.append(kod.strip())
        
        if nevek and kodok:
            return ", ".join(nevek), ", ".join(kodok)
    
    return "N/A", "N/A"