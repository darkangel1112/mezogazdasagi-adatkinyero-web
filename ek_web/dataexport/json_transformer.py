"""
JSON Transformer Modul - Mezőgazdasági Adatkinyerő v7.5
Strukturált JSON generálása EK adatokból az API_JSON_SPEC.md szerint
"""

import pandas as pd
from typing import Dict, List, Any


def generate_ek_json_response(
    analysis_data: dict,
    fovetes_df: pd.DataFrame,
    masodvetes_list: list,
    summary_dict: dict
) -> dict:
    """
    Fő függvény: teljes JSON válasz generálása az API_JSON_SPEC.md szerint
    
    Args:
        analysis_data: Elemzési riport (create_analysis_report output)
        fovetes_df: Fővetés DataFrame
        masodvetes_list: Másodvetés/Agrotechnika lista
        summary_dict: Összesítő adatok dictionary
    
    Returns:
        dict: Strukturált JSON az API specifikáció szerint
    """
    applicant_info = analysis_data.get('applicant_info', {})
    
    return {
        "success": True,
        "applicant": applicant_info.get('name', 'N/A'),
        "data": {
            "summary": build_summary_array(analysis_data, summary_dict),
            "mainCrop": build_main_crop_array(fovetes_df),
            "secondaryCrop": build_secondary_crop_array(masodvetes_list),
            "compliance": build_compliance_object(masodvetes_list, analysis_data),
            "statistics": calculate_statistics(analysis_data, fovetes_df, summary_dict)
        }
    }


def build_summary_array(analysis_data: dict, summary_dict: dict) -> List[Dict[str, Any]]:
    """
    EK Összesítő táblázat építése
    
    Returns:
        List[SummaryRow]: Növényenkénti összesítő adatok
    """
    summary_df = analysis_data.get('summary_df', pd.DataFrame())
    
    if summary_df.empty:
        return []
    
    result = []
    
    for _, row in summary_df.iterrows():
        # Kizárjuk az "Összesen:" sort és üres kódokat
        kod = str(row.get('Kód', '')).strip()
        if not kod or kod.lower() in ['összesen:', 'összesen', '']:
            continue
        
        result.append({
            "code": kod,
            "name": str(row.get('Megnevezés', '')),
            "mainCrop": float(row.get('Fővetés (Számított)', 0.0)),
            "secondaryCrop": float(row.get('Másodvetés (Számított)', 0.0)),
            "totalArea": float(row.get('Összesen (Számított)', 0.0)),
            "akgArea": float(row.get('AKG', 0.0)),
            "ecoArea": float(row.get('ÖKO', 0.0))
        })
    
    return result


def build_main_crop_array(fovetes_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Fővetés táblázat építése
    
    Returns:
        List[MainCropRow]: Fővetés táblák adatai
    """
    if fovetes_df.empty:
        return []
    
    result = []
    
    for _, row in fovetes_df.iterrows():
        result.append({
            "county": str(row.get('Vármegye', '')),
            "settlement": str(row.get('Település', '')),
            "block": str(row.get('Blokk', '')),
            "table": int(row.get('Tábla', 0)),  # NUMBER típus!
            "code": str(row.get('Kód', '')),
            "name": str(row.get('Név', '')),
            "area": float(row.get('Méret (ha)', 0.0)),
            "eco": _normalize_yes_no(row.get('ÖKO', 'Nem')),
            "akg": _normalize_yes_no(row.get('AKG', 'Nem')),
            "fertilizer": _normalize_yes_no_na(row.get('Szap.anyag', 'N/A')),
            "planting": _normalize_date_or_na(row.get('Telepítés', 'N/A')),
            "termination": _normalize_date_or_na(row.get('Termőre ford.', 'N/A')),
            "nitrate": _normalize_yes_no(row.get('Nitrát', 'Nem'))
        })
    
    return result


def build_secondary_crop_array(masodvetes_list: list) -> List[Dict[str, Any]]:
    """
    Másodvetés/Agrotechnika táblázat építése
    
    Returns:
        List[SecondaryCropRow]: Másodvetés és agrotechnikai műveletek
    """
    if not masodvetes_list:
        return []
    
    result = []
    
    for item in masodvetes_list:
        # item formátum: [Blokk, Tábla, Sorszám, Típus, Megnevezés, Anyag, Növény kód, Terület]
        if len(item) < 8:
            continue
        
        tipus = _normalize_type(item[3])
        
        result.append({
            "block": str(item[0]),
            "table": int(item[1]),  # NUMBER típus!
            "row": str(item[2]),
            "type": tipus,  # "Agrotechnika" vagy "Másodvetés"
            "description": str(item[4]),
            "fertilizer": str(item[5]) if item[5] and str(item[5]).strip() else "N/A",
            "cropCode": str(item[6]) if item[6] and str(item[6]).strip() else "N/A",
            "area": float(item[7])
        })
    
    return result


def build_compliance_object(masodvetes_list: list, analysis_data: dict) -> Dict[str, List[str]]:
    """
    Jogcímek & Műveletek objektum építése
    
    Returns:
        ComplianceObject: Egyedi agrotechnikai műveletek és támogatási igények
    """
    # Agrotechnikai műveletek egyedi listája (csak ahol type === "Agrotechnika")
    agrotechnika_set = set()
    
    for item in masodvetes_list:
        if len(item) < 8:
            continue
        
        tipus = _normalize_type(item[3])
        if tipus == "Agrotechnika":
            description = str(item[4]).strip()
            if description:
                agrotechnika_set.add(description)
    
    # Támogatási igények
    extra_stats = analysis_data.get('extra_stats', {})
    tamogatas_source = extra_stats.get('support_requests', [])
    
    # Feldolgozás és validálás (objektumok listáját várjuk)
    tamogatas_result = []
    seen_names = set()
    
    for item in tamogatas_source:
        entry = None
        
        # Ha már az új objektum formátum
        if isinstance(item, dict):
            entry = item
        # Ha string (legacy vagy fallback)
        elif isinstance(item, str):
            entry = {"name": item, "area": 0.0}
            
        if entry:
            name = entry.get('name', '').strip()
            if name and name not in seen_names:
                seen_names.add(name)
                tamogatas_result.append(entry)
    
    # Rendezés név szerint
    tamogatas_result.sort(key=lambda x: x.get('name', ''))

    # ÚJ: A pipálós lista (checkbox_list) hozzáadása
    # Ezt az adatfeldolgozas_parser.py-ban mentettük el
    requests_list = extra_stats.get('checkbox_list', [])

    return {
        "agrotechnika": sorted(list(agrotechnika_set)),
        "tamogatas": tamogatas_result,
        "requests": requests_list  # <--- ÚJ MEZŐ
    }


def calculate_statistics(
    analysis_data: dict,
    fovetes_df: pd.DataFrame,
    summary_dict: dict
) -> Dict[str, float]:
    """
    Statisztikák számítása
    
    Returns:
        StatisticsObject: Összesített statisztikák
    """
    summary_df = analysis_data.get('summary_df', pd.DataFrame())
    
    # Összes fővetés (Összesen: sor nélkül)
    main_crop_area = 0.0
    if not summary_df.empty:
        filtered = summary_df[summary_df['Kód'].str.strip() != '']
        filtered = filtered[~filtered['Kód'].str.lower().str.contains('összesen', na=False)]
        main_crop_area = filtered['Fővetés (Számított)'].sum()
    
    # Összes másodvetés (Összesen: sor nélkül)
    secondary_crop_area = 0.0
    if not summary_df.empty:
        filtered = summary_df[summary_df['Kód'].str.strip() != '']
        filtered = filtered[~filtered['Kód'].str.lower().str.contains('összesen', na=False)]
        secondary_crop_area = filtered['Másodvetés (Számított)'].sum()
    
    # Nitrátérzékeny terület (csak ahol Nitrát === "Igen")
    nitrate_area = 0.0
    if not fovetes_df.empty:
        nitrate_rows = fovetes_df[
            fovetes_df['Nitrát'].str.lower().str.strip() == 'igen'
        ]
        nitrate_area = nitrate_rows['Méret (ha)'].sum()

    # AKG és ÖKO összesen: ugyanabból a tábla-szintű jelölésből számoljuk, mint az összesítő táblát.
    akg_area = 0.0
    if not fovetes_df.empty and 'AKG' in fovetes_df.columns:
        akg_rows = fovetes_df[
            fovetes_df['AKG'].astype(str).str.lower().str.strip() == 'igen'
        ]
        akg_area = akg_rows['Méret (ha)'].sum()

    eco_area = 0.0
    if not fovetes_df.empty and 'ÖKO' in fovetes_df.columns:
        eco_rows = fovetes_df[
            fovetes_df['ÖKO'].astype(str).str.lower().str.strip() == 'igen'
        ]
        eco_area = eco_rows['Méret (ha)'].sum()
    
    # Top 5 legnagyobb tábla
    top5_area = 0.0
    if not fovetes_df.empty:
        sorted_tables = fovetes_df.sort_values('Méret (ha)', ascending=False)
        top5_area = sorted_tables.head(5)['Méret (ha)'].sum()
    
    # Táblák száma
    table_count = len(fovetes_df)
    
    return {
        "mainCropArea": round(float(main_crop_area), 4),
        "secondaryCropArea": round(float(secondary_crop_area), 4),
        "nitrateArea": round(float(nitrate_area), 2),
        "akgArea": round(float(akg_area), 4),
        "ecoArea": round(float(eco_area), 4),
        "top5Area": round(float(top5_area), 2),
        "tableCount": int(table_count)
    }


# =============================================================================
# HELPER FÜGGVÉNYEK - Normalizálás
# =============================================================================

def _normalize_yes_no(value: Any) -> str:
    """
    Igen/Nem normalizálás pontos kis-nagybetűvel
    """
    if pd.isna(value):
        return "Nem"
    
    v = str(value).strip().lower()
    if v in ['igen', 'i', 'yes', 'y']:
        return "Igen"
    elif v in ['nem', 'n', 'no']:
        return "Nem"
    
    return "Nem"


def _normalize_yes_no_na(value: Any) -> str:
    """
    Igen/Nem/N/A normalizálás
    """
    if pd.isna(value) or not value or str(value).strip() == '':
        return "N/A"
    
    v = str(value).strip().lower()
    if v in ['igen', 'i', 'yes', 'y']:
        return "Igen"
    elif v in ['nem', 'n', 'no']:
        return "Nem"
    elif v in ['n/a', 'na', '-']:
        return "N/A"
    
    return "N/A"


def _normalize_date_or_na(value: Any) -> str:
    """
    Dátum vagy N/A normalizálás
    """
    if pd.isna(value) or not value:
        return "N/A"
    
    v = str(value).strip()
    if not v or v.lower() in ['n/a', 'na', '-', '']:
        return "N/A"
    
    return v


def _normalize_type(value: Any) -> str:
    """
    Típus normalizálás: "Agrotechnika" vagy "Másodvetés"
    Kis-nagybetű érzékeny a specifikáció szerint!
    """
    if pd.isna(value):
        return "Agrotechnika"
    
    v = str(value).strip().lower()
    
    if 'másod' in v or 'masod' in v:
        return "Másodvetés"
    elif 'agro' in v or 'tech' in v:
        return "Agrotechnika"
    
    # Default
    return "Agrotechnika"
