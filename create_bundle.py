# Fájlnév: create_bundle.py
import os

# A projektmappák és fájlok, amiket össze akarunk fűzni
project_structure = {
    ".": [
        "main.py",
        "README.md",
        "create_bundle.py" # Opcionális: a szkript saját magát is beleteheti
    ],
    "GUI": [
        "gui_manager.py"
    ],
    "dataprocess": [
        "fovetes_parser.py",
        "masodvetes_parser.py",
        "osszesitok_parser.py",
        "adatfeldolgozas_parser.py" # HOZZÁADVA
    ],
    "dataexport": [
        "excel_exporter.py"
    ],
    "assets": [
        "help.txt"
    ]
}

output_filename = "projekt_kivonat.txt"

def create_project_bundle():
    """
    Összegyűjti a megadott projektfájlok tartalmát egyetlen szövegfájlba.
    """
    try:
        with open(output_filename, "w", encoding="utf-8") as bundle_file:
            for directory, filenames in project_structure.items():
                for filename in filenames:
                    # Az útvonalakat helyesen építjük fel a könyvtárnév alapján
                    filepath = os.path.join(directory, filename)
                    
                    if os.path.exists(filepath):
                        print(f"Feldolgozás: {filepath}")
                        
                        # Elválasztó a fájlnévvel
                        bundle_file.write(f"--- START OF FILE {filepath.replace(os.sep, '/')} ---\n\n")
                        
                        # Fájl tartalmának beolvasása és írása
                        with open(filepath, "r", encoding="utf-8") as source_file:
                            bundle_file.write(source_file.read())
                        
                        # Lezáró sorok a jobb olvashatóságért
                        bundle_file.write("\n\n--- END OF FILE ---\n\n")
                    else:
                        print(f"Figyelmeztetés: A(z) '{filepath}' fájl nem található, kihagyva.")
        
        print(f"\nSiker! A projekt összefűzve a(z) '{output_filename}' fájlba.")

    except Exception as e:
        print(f"\nHiba történt a fájlok összefűzése közben: {e}")

if __name__ == "__main__":
    create_project_bundle()