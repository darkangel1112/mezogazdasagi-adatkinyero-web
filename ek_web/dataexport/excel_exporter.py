# Fájlnév: dataexport/excel_exporter.py
import pandas as pd
import os
import re

def _hu_float(s):
    """Magyar tizedes vesszős szám (pl. '3,7787') konverziója float-tá."""
    try:
        return float(str(s).replace('\xa0', '').replace('\u00a0', '').replace(' ', '').replace(',', '.'))
    except Exception:
        return 0.0


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
    worksheet.write(row_idx, 1, report_data.get("applicant_info", {}).get("support_id", "N/A"))
    
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
                try:
                    worksheet.write(row_idx, col_idx, cell_data, format_to_use)
                except:
                    worksheet.write(row_idx, col_idx, str(cell_data), current_text_format)
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
        if isinstance(req, dict):
            req_text = req.get('name', str(req))
        else:
            req_text = str(req)
        worksheet.write(row_idx, 0, req_text)
        row_idx += 1

    worksheet.set_column('A:A', 15)
    worksheet.set_column('B:B', 40)
    worksheet.set_column('C:H', 20)

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
    workbook = writer.book
    
    # Formátumok definiálása
    header_format = workbook.add_format({
        'bold': True, 
        'bg_color': '#DDEBF7', 
        'border': 1, 
        'align': 'center', 
        'valign': 'vcenter'
    })
    
    # Adat keret formátumok (csak a tartományra lesznek alkalmazva)
    base_border_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
    number_border_format = workbook.add_format({'num_format': '0.0000', 'border': 1, 'valign': 'vcenter'})
    
    # Rugalmasabb oszlop definíciók a kulcsokhoz
    export_map = {
        "Adatfeldolgozás": [],
        "Fővetés": [],
        "Másodvetés": ['Blokk', 'Tábla', 'Sorszám', 'Típus', 'Megnevezés', 'Anyag', 'Növény kód', 'Terület'],
        "Jogcímek": ['Jogcím', 'Terület'],
        "Hasznosítás": ['Kód', 'Megnevezés', 'Terület'],
        "Blokkok": ['Blokk', 'Terület']
    }

    errors = []

    for sheet_name, columns in export_map.items():
        try:
            data = data_dict.get(sheet_name)
            
            final_sheet_name = _sanitize_sheet_name(f"{prefix}{sheet_name}")

            if sheet_name == "Adatfeldolgozás":
                _write_analysis_report_to_writer(writer, data_dict, final_sheet_name)
                continue
                
            if data is None or (isinstance(data, list) and not data) or (isinstance(data, pd.DataFrame) and data.empty):
                 continue

            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                # Hasznosítás és Blokkok esetén: az utolsó oszlop mindig a terület
                # Explicit float konverzió MÉG a DataFrame létrehozása előtt,
                # hogy a vesszős tizedes ('3,7787') biztosan számként kerüljön be.
                if sheet_name in ["Hasznosítás", "Blokkok"] and isinstance(data, list) and data:
                    data = [row[:-1] + [_hu_float(row[-1])] for row in data]

                if columns and len(data[0]) != len(columns):
                    row_columns = list(columns)
                    if sheet_name == "Másodvetés" and len(data[0]) == len(row_columns) + 1:
                        row_columns.append("Kérelmező")
                        df = pd.DataFrame(data, columns=row_columns)
                    else:
                        df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame(data, columns=columns if columns else None)
            
            # Numerikus konverzió
            numeric_candidates = [col for col in df.columns if any(x in col.lower() for x in ['terület', 'méret', 'összesen', 'ha'])]
            
            for col in numeric_candidates:
                try:
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.replace('\xa0', '', regex=False)
                        .str.replace('\u00a0', '', regex=False)
                        .str.replace(' ', '', regex=False)
                        .str.replace(',', '.', regex=False)
                        .replace('N/A', '0')
                        .replace('', '0')
                    )
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                except:
                    pass
            
            # Összesítők kezelése
            if sheet_name in ["Hasznosítás", "Blokkok"]:
                total_key = f"{sheet_name.lower()}_total"
                total = data_dict.get(total_key) or data_dict.get(total_key.replace('á', 'a'), 0.0)
                if total:
                    try:
                        total_val = float(str(total).replace(',', '.'))
                        if total_val > 0:
                            total_row = ['' for _ in range(len(df.columns))]
                            total_row[-1] = total_val
                            total_row[-2] = 'Összesen:'
                            df.loc[len(df)] = total_row
                    except:
                        pass

            # Kiírás Excelbe (fejléc nélkül, azt mi írjuk ki formázva)
            df.to_excel(writer, sheet_name=final_sheet_name, index=False, header=True)
            
            worksheet = writer.sheets[final_sheet_name]
            
            # 1. Fejléc újraírása formázva
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # 2. Oszlopszélességek beállítása (KERET NÉLKÜL a set_column-ban!)
            _autoformat_columns(writer, final_sheet_name, df, numeric_candidates)
            
            # 3. Keretek alkalmazása CSAK a tartományra
            for row_num in range(1, len(df) + 1):
                for col_num in range(len(df.columns)):
                    val = df.iloc[row_num-1, col_num]
                    col_name = df.columns[col_num]
                    
                    is_numeric = numeric_candidates and col_name in numeric_candidates
                    fmt = number_border_format if is_numeric else base_border_format
                    
                    try:
                        if pd.isna(val) or val == "" or val == "N/A":
                            worksheet.write_blank(row_num, col_num, "", fmt)
                        elif is_numeric:
                            worksheet.write_number(row_num, col_num, float(val), fmt)
                        else:
                            worksheet.write(row_num, col_num, val, fmt)
                    except:
                        worksheet.write(row_num, col_num, str(val), fmt)
            
        except Exception as e:
            errors.append(f"Hiba a(z) '{sheet_name}' munkalap írásakor: {str(e)}")

    if errors:
        try:
            err_ws = writer.book.add_worksheet("Export_Log")
            for i, err in enumerate(errors):
                err_ws.write(i, 0, err)
        except:
            pass

def _identify_numeric_columns(df: pd.DataFrame, sheet_name: str) -> list:
    numeric_cols = []
    if sheet_name == "Fővetés": numeric_cols = ["Méret (ha)", "Méret"]
    elif sheet_name == "Másodvetés": numeric_cols = ["Terület (ha)", "Terület"]
    elif sheet_name in ["Jogcímek", "Hasznosítás", "Blokkok"]: numeric_cols = ["Terület (ha)", "Terület"]
    return [col for col in numeric_cols if col in df.columns]

def _autoformat_columns(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame, 
                       numeric_columns: list = None):
    worksheet = writer.sheets[sheet_name]
    
    for idx, col in enumerate(df.columns):
        series = df[col]
        try:
            max_val_len = series.astype(str).map(len).max()
            max_col_len = len(str(series.name))
            max_len = max(max_val_len, max_col_len) + 4
        except:
            max_len = 15
            
        # CSAK SZÉLESSÉGET ÁLLÍTUNK, NEM FORMÁTUMOT (így nincs végtelen rács)
        worksheet.set_column(idx, idx, min(max(max_len, 12), 65))

def _sanitize_sheet_name(name: str) -> str:
    invalid_chars = re.compile(r'[\\*?:/\[\]]')
    sanitized = invalid_chars.sub("", name)
    return sanitized[:31]
