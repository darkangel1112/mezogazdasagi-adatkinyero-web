# Fájlnév: main.py
import sys
import os
import time
import ctypes  # Új import
from tkinterdnd2 import TkinterDnD
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk

# JAVÍTÁS: DPI-Aware mód beállítása Windows rendszereken
if os.name == 'nt':
    try:
        # Próbáljuk beállítani a DPI-Awareness Context-et a modernebb Windows verziókhoz
        ctypes.windll.shcore.SetProcessDpiAwarenessContext(ctypes.c_int(-4)) # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    except (AttributeError, OSError):
        # Ha ez nem működik, akkor a régebbi metódust használjuk
        ctypes.windll.user32.SetProcessDPIAware()

# A saját moduljaink importálása
from GUI.gui_manager import GUIManager

# JAVÍTÁS: Ez a blokk oldja meg a "can't find package tkdnd" hibát .exe-ben
# Ennek a résznek a Tkinter ablak létrehozása ELŐTT kell lefutnia.
if getattr(sys, 'frozen', False):
    # Ha a program .exe-ként fut (PyInstaller csomagolta)
    # Beállítjuk a környezeti változót, hogy a Tcl/Tk motor
    # megtalálja a becsomagolt tkdnd könyvtárat.
    tkdnd_path = os.path.join(sys._MEIPASS, 'tkdnd')
    os.environ['TCLLIBPATH'] = tkdnd_path

def resource_path(relative_path):
    """
    Ez a kulcsfontosságú függvény biztosítja, hogy a program mindig megtalálja
    az 'assets' mappát, függetlenül a futtatási környezettől.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_splash_screen(root):
    """Létrehoz és megjelenít egy betöltő képernyőt."""
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)

    try:
        img = Image.open(resource_path("assets/logo.png"))
        img.thumbnail((480, 480), Image.Resampling.LANCZOS)
        splash_logo = ImageTk.PhotoImage(img)

        splash_width = splash_logo.width()
        splash_height = splash_logo.height() + 50

        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width // 2) - (splash_width // 2)
        y = (screen_height // 2) - (splash_height // 2)
        splash.geometry(f'{splash_width}x{splash_height}+{x}+{y}')

        tk.Label(splash, image=splash_logo, borderwidth=0).pack(pady=10)
        splash.image = splash_logo
        
        bold_font = font.Font(family="Segoe UI", size=12, weight="bold")
        tk.Label(splash, text="Mezőgazdasági Adatkinyerő Program Indítása...", font=bold_font).pack()
    except Exception as e:
        print(f"Hiba a betöltő kép betöltésekor: {e}")
        splash_width, splash_height = 480, 530
        splash.geometry(f'{splash_width}x{splash_height}')
        tk.Label(splash, text="Logó nem található...").pack(pady=20)

    splash.update()
    return splash

if __name__ == "__main__":
    MIN_SPLASH_TIME_SEC = 3.0
    start_time = time.time()

    root = TkinterDnD.Tk()
    root.withdraw()

    splash = create_splash_screen(root)
    
    app = GUIManager(root, resource_path_func=resource_path)

    duration = time.time() - start_time
    delay_ms = int((MIN_SPLASH_TIME_SEC - duration) * 1000) if duration < MIN_SPLASH_TIME_SEC else 0

    def show_main_window():
        splash.destroy()
        root.deiconify()

    root.after(delay_ms, show_main_window)
    
    root.mainloop()