# Fájlnév: GUI/gui_manager.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import threading
import os
import pandas as pd
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
import queue

# A saját modulok, beleértve az újat is
from dataprocess.fovetes_parser import extract_fovetes_data
from dataprocess.masodvetes_parser import extract_masodvetes_data
from dataprocess.osszesitok_parser import extract_summary_data
# JAVÍTVA: A gépelési hiba ('adatfeldgozas' -> 'adatfeldolgozas') javítva
from dataprocess.adatfeldolgozas_parser import create_analysis_report
from dataexport.excel_exporter import export_to_excel

class GUIManager:
    def __init__(self, root, resource_path_func):
        self.root = root
        self.resource_path = resource_path_func
        # Verziószám frissítése
        self.root.title("Mezőgazdasági Adatkinyerő v7.5")

        self.processed_data = {}
        self.current_file_list = []
        self.gui_queue = queue.Queue()

        try:
            self.root.iconbitmap(self.resource_path("assets/icon.ico"))
        except Exception:
            print("Ikonfájl (assets/icon.ico) nem található.")

        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.setup_styles()

        top_frame = ttk.Frame(self.root, padding="20 10")
        top_frame.pack(fill=tk.X, side=tk.TOP)
        top_frame.columnconfigure(0, weight=2)
        top_frame.columnconfigure(1, weight=2)
        top_frame.columnconfigure(2, weight=1)

        status_frame = ttk.Frame(self.root, padding="20 5")
        status_frame.pack(fill=tk.X, side=tk.TOP)

        results_frame = ttk.Frame(self.root, padding="20 10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)

        bottom_frame = ttk.Frame(self.root, padding="10 10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self._create_input_widgets(top_frame)
        self._create_output_options_widgets(top_frame)
        self._add_top_logo(top_frame)
        self._create_status_section(status_frame)
        self._create_results_notebook(results_frame)
        self._create_action_buttons(bottom_frame)
        self._create_status_bar(bottom_frame)

        self.process_queue()

    def setup_styles(self):
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.status_font = font.Font(family="Segoe UI", size=10)
        self.copyright_font = font.Font(family="Segoe UI", size=8)
        self.report_font = font.Font(family="Consolas", size=10)

        self.style.configure("TLabel", font=self.label_font)
        self.style.configure("Header.TLabel", font=self.header_font)
        self.style.configure("TButton", font=self.button_font, padding=5)
        self.style.configure("Accent.TButton", font=self.button_font, foreground="white", background="#0078D7", padding=8)
        self.style.map("Accent.TButton", background=[("active", "#005A9E")])
        self.style.configure("Smooth.Horizontal.TProgressbar", troughcolor="#E0E0E0", background="#0078D7", lightcolor="#0078D7", darkcolor="#005A9E")

    def _create_input_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Bemeneti Fájlok", labelwidget=ttk.Label(parent, text="Bemeneti Fájlok", style="Header.TLabel"))
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        frame.rowconfigure(0, weight=1)
        
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=8)
        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.handle_drop)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=1, sticky="ns", padx=(0, 15), pady=15)
        ttk.Button(button_frame, text="Hozzáadás...", command=self.add_files).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Beillesztés", command=self.paste_from_clipboard).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Kijelölt törlése", command=self.remove_selected).pack(fill=tk.X, pady=(10, 2))
        ttk.Button(button_frame, text="Lista törlése", command=self.clear_list).pack(fill=tk.X, pady=2)

    def _create_output_options_widgets(self, parent):
        self.output_options_frame = ttk.LabelFrame(parent, text="Kimeneti Opciók", labelwidget=ttk.Label(parent, text="Kimeneti Opciók", style="Header.TLabel"))
        self.output_options_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(0, 10))
        
        self.output_option_var = tk.StringVar(value="SEPARATE")
        ttk.Radiobutton(self.output_options_frame, text="Minden PDF-hez külön Excel fájl", variable=self.output_option_var, value="SEPARATE").pack(anchor="w", padx=15, pady=8)
        ttk.Radiobutton(self.output_options_frame, text="Összes adat egy új Excel fájlba\n(fájlonként külön munkalapok)", variable=self.output_option_var, value="COMBINE").pack(anchor="w", padx=15, pady=8)
        ttk.Radiobutton(self.output_options_frame, text="Összes adat hozzáfűzése egy meglévő\nExcelhez (hamarosan)", variable=self.output_option_var, value="APPEND", state="disabled").pack(anchor="w", padx=15, pady=8)

    def _add_top_logo(self, parent):
        logo_container = ttk.Frame(parent)
        logo_container.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        logo_container.columnconfigure(0, weight=1)
        logo_container.rowconfigure(0, weight=1)

        try:
            self.output_options_frame.update_idletasks()
            target_height = self.output_options_frame.winfo_height() - 20
            
            img = Image.open(self.resource_path("assets/logo.png"))
            w, h = img.size
            ratio = w / h
            new_width = int(target_height * ratio)
            
            resized_img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
            self.top_logo_image = ImageTk.PhotoImage(resized_img)
            
            logo_label = ttk.Label(logo_container, image=self.top_logo_image)
            logo_label.grid(row=0, column=0, sticky="")
        except Exception as e:
            print(f"Felső logó (assets/logo.png) nem tölthető be: {e}")

    def _create_results_notebook(self, parent):
        file_selector_frame = ttk.Frame(parent)
        file_selector_frame.grid(row=0, column=0, sticky='ew', pady=(10, 5))
        ttk.Label(file_selector_frame, text="Megjelenített fájl:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_combobox = ttk.Combobox(file_selector_frame, state="readonly", width=80)
        self.file_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.file_combobox.bind("<<ComboboxSelected>>", self._on_file_selected)

        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.tabs, self.trees = {}, {}
        
        tab_configs = {
            "Összefoglaló": [],
            "Fővetés": ['Vármegye', 'Település', 'Blokk', 'Tábla', 'Kód', 'Név', 'Méret (ha)', 'ÖKO', 'Szap.anyag', 'Telepítés', 'Termőre ford.', 'Nitrát'],
            "Másodvetés": ['Blokk', 'Tábla', 'Sorszám', 'Típus', 'Megnevezés', 'Anyag', 'Növény kód', 'Terület (ha)'],
            "Jogcímek": ['Támogatási jogcím', 'Terület (ha)'],
            "Hasznosítás": ['Kód', 'Megnevezés', 'Terület (ha)'],
            "Blokkok": ['Blokk azonosító', 'Terület (ha)']
        }
        
        for name, cols in tab_configs.items():
            tab = ttk.Frame(self.notebook, padding="5")
            self.notebook.add(tab, text=name)
            self.tabs[name] = tab
            
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(0, weight=1)

            if name == "Összefoglaló":
                self.analysis_text = tk.Text(tab, wrap=tk.NONE, font=self.report_font, state=tk.DISABLED, relief=tk.FLAT, background=self.root.cget('bg'))
                v_scroll = ttk.Scrollbar(tab, orient="vertical", command=self.analysis_text.yview)
                h_scroll_text = ttk.Scrollbar(tab, orient="horizontal", command=self.analysis_text.xview)
                self.analysis_text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll_text.set)
                
                self.analysis_text.grid(row=0, column=0, sticky="nsew")
                v_scroll.grid(row=0, column=1, sticky="ns")
                h_scroll_text.grid(row=1, column=0, sticky="ew")
            else:
                # MÓDOSÍTVA: Hozzáadva a 'height=8' paraméter
                tree = ttk.Treeview(tab, columns=cols, show='headings', height=8)
                for col in cols:
                    anchor = 'w' if col in ['Támogatási jogcím', 'Név', 'Megnevezés'] else 'center'
                    tree.heading(col, text=col, anchor=anchor)
                    tree.column(col, width=120, minwidth=80, anchor=anchor)
                
                v_scroll = ttk.Scrollbar(tab, orient="vertical", command=tree.yview)
                h_scroll = ttk.Scrollbar(tab, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
                
                tree.grid(row=0, column=0, sticky="nsew")
                v_scroll.grid(row=0, column=1, sticky="ns")
                h_scroll.grid(row=1, column=0, sticky="ew")
                
                self.trees[name] = tree
                if name in ["Hasznosítás", "Blokkok"]:
                    tree.tag_configure('total_row', font=('TkDefaultFont', 9, 'bold'))

    def _process_files(self):
        self.processed_data.clear()
        total_files = len(self.current_file_list)
        for i, f_path in enumerate(self.current_file_list):
            filename = os.path.basename(f_path)
            try:
                data = {}
                self.gui_queue.put(f"Feldolgozás ({i+1}/{total_files}): {filename} (Fővetés...)")
                data["Fővetés"] = extract_fovetes_data(f_path)
                
                self.gui_queue.put(f"Feldolgozás ({i+1}/{total_files}): {filename} (Másodvetés...)")
                data["Másodvetés"] = extract_masodvetes_data(f_path)
                
                self.gui_queue.put(f"Feldolgozás ({i+1}/{total_files}): {filename} (Összesítők...)")
                osszesitok = extract_summary_data(f_path)
                data.update({
                    "Jogcímek": osszesitok.get('jogcim', []),
                    "Hasznosítás": osszesitok.get('hasznositas', []),
                    "Hasznosítás_total": osszesitok.get('hasznositas_total', 0.0),
                    "Blokkok": osszesitok.get('blokkok', []),
                    "Blokkok_total": osszesitok.get('blokkok_total', 0.0)
                })
                
                self.gui_queue.put(f"Feldolgozás ({i+1}/{total_files}): {filename} (Elemzés készítése...)")
                analysis_data = create_analysis_report(data, f_path)
                data["Adatfeldolgozás"] = analysis_data

                self.processed_data[filename] = data
            except Exception as e:
                print(f"Hiba a feldolgozás során ({filename}): {e}")
                self.processed_data[filename] = {"error": str(e)}
        self.gui_queue.put("DONE_PROCESSING")

    def _on_file_selected(self, event=None):
        selected_file = self.file_combobox.get()
        if not selected_file: return
        data = self.processed_data.get(selected_file, {})
        
        if "error" in data:
            for tree in self.trees.values():
                for item in tree.get_children(): tree.delete(item)
                tree.insert("", "end", values=["Hiba a fájl feldolgozása során:"] + [""] * (len(tree['columns'])-1) )
            self._populate_analysis_tab({"error": data["error"]})
            return
        
        self._populate_tree("Fővetés", data.get("Fővetés"))
        self._populate_tree("Másodvetés", data.get("Másodvetés", []))
        self._populate_tree("Jogcímek", data.get("Jogcímek", []))
        self._populate_tree("Hasznosítás", data.get("Hasznosítás", []), data.get("Hasznosítás_total", 0.0))
        self._populate_tree("Blokkok", data.get("Blokkok", []), data.get("Blokkok_total", 0.0))
        
        self._populate_analysis_tab(data.get("Adatfeldolgozás", {}))

    def _populate_analysis_tab(self, analysis_data):
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete(1.0, tk.END)

        if analysis_data is None:
            self.analysis_text.config(state=tk.DISABLED)
            return

        if "error" in analysis_data:
            self.analysis_text.insert(tk.END, f"Hiba az elemzés készítésekor:\n{analysis_data.get('error', 'Ismeretlen hiba.')}")
            self.analysis_text.config(state=tk.DISABLED)
            return

        self.analysis_text.tag_configure("header", font=self.header_font, spacing3=10)
        self.analysis_text.tag_configure("bold", font=self.button_font)
        
        info = analysis_data.get("applicant_info", {})
        self.analysis_text.insert(tk.END, "Kérelmező Adatai\n", "header")
        self.analysis_text.insert(tk.END, "{:<25}".format("Gazda megnevezése:"), "bold")
        self.analysis_text.insert(tk.END, f"{info.get('name', 'N/A')}\n")
        self.analysis_text.insert(tk.END, "{:<25}".format("MÁK Azonosító:"), "bold")
        self.analysis_text.insert(tk.END, f"{info.get('mak_id', 'N/A')}\n")

        self.analysis_text.insert(tk.END, "\nTerület Kimutatás (Önellenőrzéssel)\n", "header")
        df = analysis_data.get("summary_df")
        if df is not None and not df.empty:
            table_str = df.to_string(index=False, float_format="%.4f")
            self.analysis_text.insert(tk.END, table_str)
        
        stats = analysis_data.get("extra_stats", {})
        self.analysis_text.insert(tk.END, "\n\nKiegészítő Statisztikák\n", "header")
        self.analysis_text.insert(tk.END, "{:<35}".format("Nitrátérzékeny terület összesen:"), "bold")
        self.analysis_text.insert(tk.END, f"{stats.get('nitrate_sum', 0.0):.4f} ha\n".replace('.',','))
        self.analysis_text.insert(tk.END, "{:<35}".format("5 legnagyobb tábla területe:"), "bold")
        self.analysis_text.insert(tk.END, f"{stats.get('top_5_plots_sum', 0.0):.4f} ha\n".replace('.',','))
        
        self.analysis_text.insert(tk.END, "\nElvégzett Agrotechnikai Műveletek\n", "header")
        for tech in stats.get("agrotechnics", ["Nincs adat."]):
            self.analysis_text.insert(tk.END, f" • {tech}\n")

        self.analysis_text.insert(tk.END, "\nKiválasztott Támogatási Igények\n", "header")
        requests = stats.get("support_requests", ["Nem található."])
        for req in requests:
            self.analysis_text.insert(tk.END, f" • {req}\n")

        self.analysis_text.config(state=tk.DISABLED)

    def clear_list(self):
        self.file_listbox.delete(0, tk.END); self.processed_data.clear()
        self.file_combobox['values'] = []; self.file_combobox.set('')
        for tree in self.trees.values():
            for item in tree.get_children(): tree.delete(item)
        # JAVÍTVA: A _populate_analysis_tab-ot None-nal hívjuk, hogy törölje a tartalmát
        self._populate_analysis_tab(None) 
        self.export_button.config(state="disabled")
        self.status_var.set("Készen áll. Adjon hozzá PDF fájlokat a listához.")

    def _create_status_section(self, parent):
        frame = ttk.LabelFrame(parent, text="Állapot", labelwidget=ttk.Label(parent, text="Állapot", style="Header.TLabel"))
        frame.pack(fill=tk.X, pady=(0, 10))
        self.status_var = tk.StringVar(value="Készen áll. Adjon hozzá PDF fájlokat a listához.")
        status_label = ttk.Label(frame, textvariable=self.status_var, font=self.status_font)
        status_label.pack(anchor="w", padx=15, pady=10)

    def _create_action_buttons(self, parent):
        self.process_button = ttk.Button(parent, text="Feldolgozás", style="Accent.TButton", command=self._start_processing_thread)
        # Módosítva: expand=True és fill=tk.X paraméterek hozzáadva
        self.process_button.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)
        self.export_button = ttk.Button(parent, text="Exportálás", command=self._start_export_thread, state="disabled")
        # Módosítva: expand=True és fill=tk.X paraméterek hozzáadva
        self.export_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(parent, text="Súgó", command=self._show_help).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(parent, text="Bezárás", command=self.root.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _create_status_bar(self, parent):
        try:
            img = Image.open(self.resource_path("assets/logo.png"))
            img.thumbnail((24, 24), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img)
            logo_label = ttk.Label(parent, image=self.logo_image)
            logo_label.pack(side=tk.LEFT, padx=(10, 5))
        except Exception as e:
            print(f"Logó (assets/logo.png) nem tölthető be: {e}")
        self.progress_bar = ttk.Progressbar(parent, mode="indeterminate", style="Smooth.Horizontal.TProgressbar", length=200)
        # Módosítva: expand=True és fill=tk.X paraméterek hozzáadva
        self.progress_bar.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        copyright_label = ttk.Label(parent, text="Készült Péter ötletei alapján a Gemini AI segítségével | v7.5", font=self.copyright_font, foreground="gray")
        copyright_label.pack(side=tk.RIGHT, padx=10)

    def process_queue(self):
        try:
            message = self.gui_queue.get_nowait()
            if isinstance(message, str):
                if message == "DONE_PROCESSING": self._on_processing_finished()
                elif message == "DONE_EXPORT": self._on_export_finished()
                else: self.status_var.set(message)
        except queue.Empty: pass
        finally: self.root.after(100, self.process_queue)

    def _start_processing_thread(self):
        self.current_file_list = self.file_listbox.get(0, tk.END)
        if not self.current_file_list:
            messagebox.showwarning("Hiányzó adatok", "A feldolgozáshoz adjon hozzá legalább egy PDF fájlt.")
            return
        self._toggle_controls("disabled")
        self.progress_bar.start()
        threading.Thread(target=self._process_files, daemon=True).start()

    def _start_export_thread(self):
        if not self.processed_data:
            messagebox.showwarning("Nincs adat", "Nincs mit exportálni.")
            return
        output_option = self.output_option_var.get()
        file_count = len(self.current_file_list)
        output_path, output_directory = None, None
        try:
            if output_option == "SEPARATE":
                if file_count == 1:
                    first_file = os.path.basename(self.current_file_list[0])
                    default_name = f"{os.path.splitext(first_file)[0]}_kivonat.xlsx"
                    output_path = filedialog.asksaveasfilename(title="Excel fájl mentése", defaultextension=".xlsx", filetypes=[("Excel fájlok", "*.xlsx"), ("Minden fájl", "*.*")], initialfile=default_name)
                    if not output_path: return
                else:
                    output_directory = filedialog.askdirectory(title="Válasszon könyvtárat az Excel fájlok mentéséhez")
                    if not output_directory: return
            elif output_option == "COMBINE":
                output_path = filedialog.asksaveasfilename(title="Egyesített Excel fájl mentése", defaultextension=".xlsx", filetypes=[("Excel fájlok", "*.xlsx"), ("Minden fájl", "*.*")], initialfile="egyesitett_kivonat.xlsx")
                if not output_path: return
            self._toggle_controls("disabled")
            self.progress_bar.start()
            threading.Thread(target=self._export_files, args=(output_option, output_path, output_directory), daemon=True).start()
        except Exception as e: messagebox.showerror("Hiba", f"Hiba a fájl kiválasztása során: {e}")

    def _export_files(self, output_option, output_path=None, output_directory=None):
        try:
            success = export_to_excel(self.processed_data, output_option, self.current_file_list, self.gui_queue, output_path=output_path, output_directory=output_directory)
            if success: self.gui_queue.put("DONE_EXPORT")
        except Exception as e:
            self.gui_queue.put(f"Exportálási hiba: {e}")
            self.gui_queue.put("DONE_EXPORT")

    def handle_drop(self, event): self.add_files_to_list(self.root.tk.splitlist(event.data))
    def add_files(self):
        paths = filedialog.askopenfilenames(title="PDF fájlok kiválasztása", filetypes=[("PDF Fájlok", "*.pdf")])
        if paths: self.add_files_to_list(paths)
    def paste_from_clipboard(self):
        try: self.add_files_to_list(self.root.clipboard_get().split('\n'))
        except tk.TclError: messagebox.showwarning("Hiba", "A vágólap üres vagy nem tartalmaz szöveget.")
    def add_files_to_list(self, paths):
        for p in paths:
            p_clean = p.strip().replace('{','').replace('}','')
            if p_clean and os.path.exists(p_clean) and p_clean.lower().endswith('.pdf'):
                if p_clean not in self.file_listbox.get(0, tk.END): self.file_listbox.insert(tk.END, p_clean)
        self.status_var.set(f"{self.file_listbox.size()} fájl a listában.")
    def remove_selected(self):
        for i in reversed(self.file_listbox.curselection()): self.file_listbox.delete(i)
        self.status_var.set(f"{self.file_listbox.size()} fájl a listában.")

    def _toggle_controls(self, state="normal"):
        for widget in [self.process_button, self.export_button]: 
            widget.config(state=state if widget != self.export_button or self.processed_data else "disabled")

    def _on_processing_finished(self):
        self.progress_bar.stop(); self._toggle_controls("normal")
        self.status_var.set("Feldolgozás kész. Válasszon fájlt a legördülő menüből.")
        file_names = list(self.processed_data.keys()); self.file_combobox['values'] = file_names
        if file_names: self.file_combobox.set(file_names[0]); self._on_file_selected()

    def _populate_tree(self, name, data, total=None):
        tree = self.trees.get(name)
        if not tree: return
        for item in tree.get_children(): tree.delete(item)
        if isinstance(data, pd.DataFrame):
            for _, row in data.iterrows(): tree.insert("", "end", values=list(row.fillna("N/A")))
        elif isinstance(data, list):
            for row in data: tree.insert("", "end", values=row)
        if total is not None and total > 0:
            total_str = f"{total:.4f}".replace('.', ',')
            if name == "Hasznosítás": tree.insert("", "end", values=('', 'Összesen:', total_str), tags=('total_row',))
            elif name == "Blokkok": tree.insert("", "end", values=('Összesen:', total_str), tags=('total_row',))

    def _on_export_finished(self):
        self.progress_bar.stop(); self._toggle_controls("normal")
        status = self.status_var.get()
        if "hiba" in status.lower(): messagebox.showerror("Hiba", status)
        else: self.status_var.set("Exportálás sikeresen befejeződött."); messagebox.showinfo("Siker", "Az exportálás sikeresen befejeződött.")

    def _show_help(self):
        try:
            with open(self.resource_path("assets/help.txt"), "r", encoding="utf-8") as f: help_content = f.read()
        except FileNotFoundError: help_content = "A súgófájl (assets/help.txt) nem található."
        help_window = tk.Toplevel(self.root); help_window.title("Súgó"); help_window.geometry("700x500")
        text_area = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10, font=self.label_font); text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, help_content); text_area.config(state=tk.DISABLED)
        ttk.Button(help_window, text="Bezárás", command=help_window.destroy).pack(pady=10)
        help_window.transient(self.root); help_window.grab_set()