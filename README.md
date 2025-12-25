--- START OF FILE README.md ---
Mezőgazdasági Adatkinyerő v7.5 - Dokumentáció
Ez a dokumentum a projekt felépítését, a modulok szerepét és a bennük található kulcsfontosságú függvények működését írja le. Célja, hogy segítse a jövőbeli karbantartást és fejlesztést.
Projekt Struktúra
A projekt egy modularizált, logikailag szétválasztott struktúrát követ a jobb karbantarthatóság érdekében.

EK_Feldolgozo_Projekt/
│
├── main.py # Alkalmazás indítópontja
│
├── GUI/
│ └── gui_manager.py # Felhasználói felület és eseménykezelés
│
├── dataprocess/
│ ├── fovetes_parser.py # Fővetés adatainak kinyerése
│ ├── masodvetes_parser.py # Másodvetés/Agrotechnika adatainak kinyerése
│ ├── osszesitok_parser.py # Összesítő táblázatok kinyerése
│ └── adatfeldolgozas_parser.py # Összefoglaló riport generálása
│
├── dataexport/
│ └── excel_exporter.py # Excel exportálási logika
│
└── assets/
  ├── icon.ico # Alkalmazás ikon
  ├── logo.png # GUI-ban megjelenő kép
  └── help.txt # Súgó szöveges fájl

Modulok és Függvények
main.py
A program belépési pontja.
create_splash_screen(root): Létrehoz egy betöltő képernyőt (splash screen), ami a program indulásakor, a főablak felépülése alatt látható.
Fő logika: Megjeleníti a betöltő képernyőt, példányosítja a GUIManager osztályt, majd a betöltés végeztével megjeleníti a kész főablakot.

GUI/gui_manager.py
Felelős a teljes grafikus felületért és a felhasználói interakciók kezeléséért.
GUIManager osztály: A fő osztály, ami összefogja a GUI-t.
_create_results_notebook(): Létrehozza a füles nézetet, beleértve egy tk.Text widgetet használó "Összefoglaló" fület is.
_process_files(): Ez a függvény fut a háttérszálon. Meghívja a dataprocess mappában lévő összes parser függvényt, beleértve az adatfeldolgozas_parser-t is.
_populate_analysis_tab(): Az "Összefoglaló" fület tölti fel a formázott, elemzési riporttal.
_on_file_selected(): A legördülő menüből való fájlválasztás eseménykezelője, feltölti az összes fület adatokkal.

dataprocess/fovetes_parser.py
Felelős a "7 - Táblaadatok" (Fővetés) szekció kinyeréséért.
extract_fovetes_data(pdf_path): A modul fő függvénye.
Visszatérési érték: Egy pandas.DataFrame, ami a kinyert és megtisztított fővetési adatokat tartalmazza.

dataprocess/masodvetes_parser.py
Felelős a "8 — Másodvetés/Agrotechnika" szekció kinyeréséért.
extract_masodvetes_data(pdf_path): A modul fő függvénye.
Visszatérési érték: Egy lista, amiben listák vannak. Minden belső lista egy-egy kinyert adatsort reprezentál.

dataprocess/osszesitok_parser.py
Felelős a három összesítő táblázat kinyeréséért.
extract_summary_data(pdf_path): A modul fő függvénye.
Visszatérési érték: Egy dictionary (szótár), ami a három összesítő táblázat adatait tartalmazza.

dataprocess/adatfeldolgozas_parser.py
Felelős a már kinyert adatokból egy komplex, összefoglaló riport generálásáért.
create_analysis_report(processed_data, pdf_path): A modul fő függvénye.
Visszatérési érték: Egy dictionary (szótár), ami a riport összes elemét tartalmazza: applicant_info (kérelmező adatai), summary_df (összesítő táblázat), és extra_stats (kiegészítő statisztikák, pl. igényelt támogatások).

dataexport/excel_exporter.py
Felelős a kinyert adatok .xlsx fájl(ok)ba történő mentéséért.
export_to_excel(...): A modul fő függvénye, ami a mentési opció alapján vezérli az exportálást.
_write_analysis_report_to_writer(...): Egyedi függvény, ami a formázott, több részből álló összefoglaló riportot képes egyetlen Excel munkalapra írni.

--- END OF FILE ---