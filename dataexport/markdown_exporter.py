"""
Markdown Export Modul - Mezőgazdasági Adatkinyerő v7.5
Strukturált markdown riportok generálása a feldolgozott adatokból
"""

import pandas as pd
from datetime import datetime


def generate_markdown_report(analysis_data, fovetes_df, masodvetes_list, summary_dict, applicant_name):
    """
    Teljes markdown riport generálása
    
    Args:
        analysis_data: Adatfeldolgozás eredménye (dict)
        fovetes_df: Fővetés DataFrame
        masodvetes_list: Másodvetés lista
        summary_dict: Összesítő adatok (dict)
        applicant_name: Kérelmező neve
    
    Returns:
        str: Formázott markdown tartalom
    """
    
    sections = []
    
    # Fejléc
    sections.append(_format_applicant_header(analysis_data.get('applicant_info', {}), applicant_name))
    
    # Összesítő táblázat
    summary_df = analysis_data.get('summary_df', pd.DataFrame())
    if not summary_df.empty:
        sections.append(_format_summary_table(summary_df))
    
    # Statisztikák
    extra_stats = analysis_data.get('extra_stats', {})
    sections.append(_format_statistics(extra_stats, len(fovetes_df)))
    
    # Fővetés
    if not fovetes_df.empty:
        sections.append(_format_fovetes_table(fovetes_df))
    
    # Másodvetés
    if masodvetes_list:
        sections.append(_format_masodvetes_table(masodvetes_list))
    
    # Összesítő szekciók
    sections.append(_format_summary_sections(summary_dict))
    
    # Agrotechnikai műveletek és támogatási igények
    sections.append(_format_extra_details(extra_stats))
    
    # Lábléc
    sections.append(_format_footer())
    
    return "\n\n".join(sections)


def _format_applicant_header(applicant_info, applicant_name):
    """Kérelmező adatok fejléc formázása"""
    
    header = f"""# 🌾 Egységes Kérelem Elemzés

**Kérelmező neve:** {applicant_info.get('name', applicant_name)}  
**Támogatási azonosító:** {applicant_info.get('mak_id') or applicant_info.get('support_id') or 'N/A'}<br>
**Generálva:** {datetime.now().strftime('%Y.%m.%d %H:%M')}"""
    
    return header


def _format_summary_table(summary_df):
    """Összesítő táblázat formázása"""
    
    section = "## 📊 Összesítő Táblázat\n\n"
    section += summary_df.to_markdown(index=False, floatfmt='.4f')
    
    return section


def _format_statistics(extra_stats, tables_count):
    """Kulcsmutatók formázása"""
    
    nitrate = extra_stats.get('nitrate_sum', 0)
    top_5 = extra_stats.get('top_5_plots_sum', 0)
    
    section = f"""## 📈 Kulcsmutatók

| Mutató | Érték |
|--------|-------|
| 🌊 Nitrátérzékeny terület | {nitrate:.2f} ha |
| 🏆 Top 5 tábla területe | {top_5:.2f} ha |
| 📊 Táblák száma | {tables_count} db |"""
    
    return section


def _format_fovetes_table(fovetes_df):
    """Fővetés táblázat formázása"""
    
    section = f"""## 🌾 Fővetés Adatok

**Táblák száma:** {len(fovetes_df)} db

"""
    section += fovetes_df.to_markdown(index=False, floatfmt='.4f')
    
    return section


def _format_masodvetes_table(masodvetes_list):
    """Másodvetés/Agrotechnika táblázat formázása"""
    
    masodvetes_df = pd.DataFrame(
        masodvetes_list,
        columns=['Blokk', 'Tábla', 'Sorszám', 'Típus', 'Megnevezés', 'Anyag', 'Növény kód', 'Terület']
    )
    
    section = f"""## 🌱 Másodvetés / Agrotechnikai Adatok

**Bejegyzések száma:** {len(masodvetes_list)} db

"""
    section += masodvetes_df.to_markdown(index=False, floatfmt='.4f')
    
    return section


def _format_summary_sections(summary_dict):
    """Jogcímek, Hasznosítás, Blokkok szekciók formázása"""
    
    sections = []
    
    # Támogatási jogcímek
    jogcim_data = summary_dict.get('jogcim', [])
    if jogcim_data:
        jogcim_df = pd.DataFrame(jogcim_data, columns=['Jogcím', 'Terület (ha)'])
        section = "### 💼 Támogatási Jogcímek\n\n"
        section += jogcim_df.to_markdown(index=False, floatfmt='.4f')
        sections.append(section)
    
    # Hasznosítás
    hasznositas_data = summary_dict.get('hasznositas', [])
    if hasznositas_data:
        hasznositas_df = pd.DataFrame(hasznositas_data, columns=['Kód', 'Megnevezés', 'Terület (ha)'])
        section = "### 🌿 Hasznosítási Adatok\n\n"
        section += hasznositas_df.to_markdown(index=False, floatfmt='.4f')
        total = summary_dict.get('hasznositas_total', 0)
        section += f"\n\n**Összesen:** {total:.4f} ha"
        sections.append(section)
    
    # Blokkhasználat
    blokk_data = summary_dict.get('blokkok', [])
    if blokk_data:
        blokk_df = pd.DataFrame(blokk_data, columns=['Blokk azonosító', 'Terület (ha)'])
        section = "### 🗺️ Blokkhasználat\n\n"
        section += blokk_df.to_markdown(index=False, floatfmt='.4f')
        total = summary_dict.get('blokkok_total', 0)
        section += f"\n\n**Összesen:** {total:.4f} ha"
        sections.append(section)
    
    if sections:
        return "## 📋 Összesítő Adatok\n\n" + "\n\n".join(sections)
    
    return ""


def _format_extra_details(extra_stats):
    """Agrotechnikai műveletek és támogatási igények"""
    
    sections = []
    
    # Agrotechnikai műveletek
    agrotechnics = extra_stats.get('agrotechnics', [])
    if agrotechnics:
        section = "### 🚜 Agrotechnikai Műveletek\n\n"
        for tech in agrotechnics:
            section += f"- {tech}\n"
        sections.append(section)
    
    # Támogatási igények
    support_requests = extra_stats.get('support_requests', [])
    if support_requests:
        section = "### ✅ Támogatási Igények\n\n"
        for req in support_requests:
            section += f"- {req}\n"
        sections.append(section)
    
    if sections:
        return "## 📝 Kiegészítő Információk\n\n" + "\n\n".join(sections)
    
    return ""


def _format_footer():
    """Lábléc formázása"""
    
    footer = f"""---

*Dokumentum generálva: {datetime.now().strftime('%Y.%m.%d %H:%M')}*  
*Mezőgazdasági Adatkinyerő v7.5 - Automatizált Elemzés*  
⚠️ **Figyelem:** A program regex illesztést használ, az eredményeket mindig ellenőrizze!"""
    
    return footer
