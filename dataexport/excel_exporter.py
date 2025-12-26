# Fájlnév: dataexport/excel_exporter.py
import pandas as pd
import os
import re

def _write_analysis_report_to_writer(writer: pd.ExcelWriter, data_dict: dict, sheet_name: str):
    workbook = writer.book
    worksheet = workbook.add_worksheet(sheet_name)
    
    bold_format = workbook.add_format({'bold': True})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1})
    number_format = workbook.add_format({'num_format': '0.0000', 'border': 1})
    text_format = workbook.add_format({'border': 1})
    total_format = workbook.add_format({'bold': True, 'num_format': '0.0000', 'bg_color': '#F2F2F2', 'top': 1})
    
    # JAVÍTVA: A riport adatait az "Adatfeldolgozás" kulcs alól vesszük
    report_data = data_dict.get("Adatfeldolgozás", {})
    if not report_data:
        worksheet.write(0, 0, "Hiba: Az elemzési riport adatai hiányoznak.")
        return

    row_idx = 0
    worksheet.write(row_idx, 0, "Gazda megnevezése:", bold_format)
    worksheet.write(row_idx, 1, report_data.get("applicant_info", {}).get("name", "N/A"))
    row_idx += 1
    worksheet.write(row_idx, 0, "MÁK Azonosító:", bold_format)
    worksheet.write(row_idx, 1, report_data.get("applicant_info", {}).get("mak_id", "N/A"))
    
    row_idx += 2
    
    df = report_data.get("summary_df")
    if df is not None and not df.empty:
        for col_idx, col_name in enumerate(df.columns):
            worksheet.write(row_idx, col_idx, col_name, header_format)
        
        row_idx += 1
        for _, row_data in df.iterrows():
            # Az utolsó, "Összesen:" sor formázásának kezelése
            is_total_row = row_data.get('Megnevezés') == 'Összesen:'
            current_num_format = total_format if is_total_row else number_format
            current_text_format = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'top': 1}) if is_total_row else text_format

            for col_idx, cell_data in enumerate(row_data):
                format_to_use = current_num_format if isinstance(cell_data, (int, float)) else current_text_format
                worksheet.write(row_idx, col_idx, cell_data, format_to_use)
            row_idx += 1

    row_idx += 1 # Hagyunk egy üres sort

    stats = report_data.get("extra_stats", {})
    worksheet.write(row_idx, 0, "Nitrátérzékeny terület (összesen):", bold_format)
    worksheet.write_number(row_idx, 1, stats.get("nitrate_sum", 0), workbook.add_format({'num_format': '0.0000'}))
    row_idx += 1
    worksheet.write(row_idx, 0, "5 legnagyobb tábla területe (összesen):", bold_format)
    worksheet.write_number(row_idx, 1, stats.get("top_5_plots_sum", 0), workbook.add_format({'num_format': '0.0000'}))
    
    # ÚJ: Táblák száma
    row_idx += 1
    worksheet.write(row_idx, 0, "Táblák száma (db):", bold_format)
    worksheet.write_number(row_idx, 1, stats.get("tables_count", 0), workbook.add_format({'num_format': '0'}))
    
    row_idx += 2
    worksheet.write(row_idx, 0, "Elvégzett agrotechnikai műveletek:", bold_format)
    row_idx += 1
    for tech in stats.get("agrotechnics", []):
        worksheet.write(row_idx, 0, tech)
        row_idx += 1

    row_idx += 1
    worksheet.write(row_idx, 0, "Kiválasztott Támogatási Igények:", bold_format)
    row_idx += 1
    for req in stats.get("support_requests", []):
        worksheet.write(row_idx, 0, req)
        row_idx += 1

    worksheet.set_column('A:A', 15)
    worksheet.set_column('B:B', 40)
    worksheet.set_column('C:F', 20)

def export_to_excel(processed_data: dict, output_option: str, file_list: list, gui_queue=None, 
                   output_path=None, output_directory=None) -> bool:
    def update_status(message):
        if gui_queue: gui_queue.put(message)

    if not processed_data: return False

    try:
        if output_option == "SEPARATE":
            total_files = len(file_list)
            for i, file_path in enumerate(file_list):
                filename = os.path.basename(file_path)
                update_status(f"Exportálás ({i+1}/{total_files}): {filename}")
                data = processed_data.get(filename)
                if data and "error" not in data:
                    output_name = output_path if total_files == 1 and output_path else os.path.join(output_directory, f"{os.path.splitext(filename)[0]}_kivonat.xlsx")
                    _write_single_file_excel(output_name, data)
        
        elif output_option == "COMBINE":
            if not output_path:
                update_status("Hiba: Nincs megadva kimeneti útvonal!")
                return False
            update_status("Összesített Excel fájl írása...")
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                for filename, data in processed_data.items():
                    if "error" in data: continue
                    sheet_prefix = _sanitize_sheet_name(os.path.splitext(filename)[0])
                    _write_sheets_to_writer(writer, data, sheet_prefix)
        
        return True
    except Exception as e:
        update_status(f"Exportálási hiba: {e}")
        return False

def _write_single_file_excel(output_path: str, data_dict: dict):
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        _write_sheets_to_writer(writer, data_dict)

def _write_sheets_to_writer(writer: pd.ExcelWriter, data_dict: dict, sheet_prefix=""):
    prefix = f"{sheet_prefix}_" if sheet_prefix else ""
    
    export_map = {
        "Adatfeldolgozás": [],
        "Fővetés": list(data_dict.get("Fővetés").columns) if isinstance(data_dict.get("Fővetés"), pd.DataFrame) else [],
        "Másodvetés": ['Blokk', 'Tábla', 'Sorszám', 'Típus', 'Megnevezés', 'Anyag', 'Növény kód', 'Terület (ha)'],
        "Jogcímek": ['Támogatási jogcím', 'Terület (ha)'],
        "Hasznosítás": ['Kód', 'Megnevezés', 'Terület (ha)'],
        "Blokkok": ['Blokk azonosító', 'Terület (ha)']
    }

    for sheet_name, columns in export_map.items():
        data = data_dict.get(sheet_name)
        
        final_sheet_name = _sanitize_sheet_name(f"{prefix}{sheet_name}")

        if sheet_name == "Adatfeldolgozás":
            _write_analysis_report_to_writer(writer, data_dict, final_sheet_name)
            continue
            
        if data is None or (isinstance(data, list) and not data):
             continue

        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data, columns=columns)
        
        numeric_columns = _identify_numeric_columns(df, sheet_name)
        
        if sheet_name != "Fővetés":
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        if sheet_name in ["Hasznosítás", "Blokkok"]:
            total = data_dict.get(f"{sheet_name.lower()}_total", 0.0)
            if total > 0:
                total_row = ['Összesen:', total] if sheet_name == "Blokkok" else ['', 'Összesen:', total]
                while len(total_row) < len(df.columns): total_row.insert(0, '')
                df.loc[len(df)] = total_row

        df.to_excel(writer, sheet_name=final_sheet_name, index=False)
        _autoformat_columns(writer, final_sheet_name, df, numeric_columns)

def _identify_numeric_columns(df: pd.DataFrame, sheet_name: str) -> list:
    numeric_cols = []
    if sheet_name == "Fővetés": numeric_cols = ["Méret (ha)"]
    elif sheet_name == "Másodvetés": numeric_cols = ["Terület (ha)"]
    elif sheet_name in ["Jogcímek", "Hasznosítás", "Blokkok"]: numeric_cols = ["Terület (ha)"]
    return [col for col in numeric_cols if col in df.columns]

def _autoformat_columns(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame, numeric_columns: list = None):
    worksheet = writer.sheets[sheet_name]
    workbook = writer.book
    number_format = workbook.add_format({'num_format': '0.0000'})
    
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = max((series.astype(str).map(len).max(), len(str(series.name)))) + 2
        format_to_use = number_format if numeric_columns and col in numeric_columns else None
        worksheet.set_column(idx, idx, max_len, format_to_use)

def _sanitize_sheet_name(name: str) -> str:
    invalid_chars = re.compile(r'[\\*?:/\[\]]')
    sanitized = invalid_chars.sub("", name)
    return sanitized[:31]