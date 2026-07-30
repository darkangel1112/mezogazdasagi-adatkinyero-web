# Fejlesztői Dokumentáció - Mezőgazdasági Adatkinyerő

## Változtatások naplója

### [2026.07.30] - HF Space Hibajavítás (4 hiba)

- **Azonosító N/A javítás:** `adatfeldolgozas_parser.py`-ban a `mak_id` kulcs átnevezve `support_id`-re, hogy egységes legyen az összes fogyasztóval (PDF fedlap, HF Space UI, Markdown exporter). Az `excel_exporter.py`-ban is frissítve.
- **Excel Hasznosítás/Blokkok nullás értékek javítás:** `excel_exporter.py` numerikus konverziójában kiegészítve ezres elválasztó szóköz eltávolításával (`.str.replace(' ', '')`), így az "1 013,9991" formátumú területértékek helyesen konvertálódnak számmá.
- **`_kivonat` suffix:** `app.py`-ban a `base_filename` képzésénél (ZIP export és egyedi letöltés) hozzáadva a `"_kivonat"` utótag minden kimeneti fájlnevetípushoz (xlsx, pdf, md, json).
- **Érintett fájlok:** `hf-space/src/dataprocess/adatfeldolgozas_parser.py`, `hf-space/src/dataexport/excel_exporter.py`, `hf-space/app.py`.



### [2026.01.11] - API Dokumentáció és MD fókusz
- **API Leírás:** Létrehozva az `api.md` fájl, amely tartalmazza a `/analyze` végpont használatát, a hitelesítést és példakódokat Python/JS nyelven.
- **Routing Javítás:** Nginx konfiguráció módosítása (`hf-space/nginx.conf`), hogy helyesen kezelje a `/api` prefixet (trailing slash hozzáadása), így a FastAPI helyesen kapja meg az útvonalakat.
- **API Javítás:** `api_app.py` teljes refaktorálása. Mostantól a `adatfeldolgozas_parser.create_analysis_report` függvényt használja (ugyanazt, mint a GUI), így garantált, hogy a statisztikák (`extra_stats`), az összesített táblázat (`summary_df`) és a nitrátérzékenység számítása is helyes és teljes körű.
- **Routing Javítás:** Nginx konfiguráció módosítása (`hf-space/nginx.conf`), hogy helyesen kezelje a `/api` prefixet (trailing slash hozzáadása), így a FastAPI helyesen kapja meg az útvonalakat.
- **API Javítás (korábbi):** `api_app.py` függvényhívásainak javítása (AttributeError fix).
- **Tervezés:** Az API jelenlegi állapota szerint csak Markdown-t ad vissza. A PDF visszaküldés a következő fázisban valósul meg.
- **DPI Beállítás:** (Korábbi módosítások alapján) A default DPI 300-ra lett állítva, 500 DPI opció hozzáadva.
- **Modellek:** Gemini 2.5 Pro és 3.0 Pro opciók előkészítve a konfigurációs felületen.

### [2026.01.13] - Strukturált JSON API Végpont
- **Új API Végpont:** Létrehozva az `/ek/json` POST endpoint, amely strukturált JSON-t ad vissza az `API_JSON_SPEC.md` specifikáció szerint.
- **JSON Transformer Modul:** Új `hf-space/src/dataexport/json_transformer.py` modul 5 helper függvénnyel:
  - `build_summary_array()` - EK Összesítő táblázat
  - `build_main_crop_array()` - Fővetés táblák (12 mező)
  - `build_secondary_crop_array()` - Másodvetés/Agrotechnika
  - `build_compliance_object()` - Jogcímek & műveletek
  - `calculate_statistics()` - Összesített statisztikák
- **Típuskonverziók:** Biztosítva hogy a számok `number` típusúak (nem string), enum értékek pontosak (`"Igen"/"Nem"/"N/A"`).
- **Backward Compatibility:** A meglévő `/analyze` endpoint változatlan maradt (markdown kimenet).
- **Helye:** `hf-space/src/api_app.py` - új `/ek/json` handler


### [2026.01.27] - PDF Export Javítás (CRITICAL HOTFIX)
- **Hiba:** `TypeError: unhashable type: 'slice'` a PDF generálásnál.
- **Ok:** A `support_requests` (támogatási igények) adatszerkezete megváltozott (string -> dict), de a PDF generáló kód (`web_app.py`, `hf-space/app.py`) még a régi string formátumot várta.
- **Javítás:** A PDF generáló ciklus mostantól ellenőrzi a típusát (`isinstance(req, dict)`), és helyesen kezeli mind az új (dict), mind a régi (string) formátumot.
- **Érintett fájlok:** `web_app.py`, `hf-space/app.py`.
- **API Hatás:** Az API kimenet nem változott, csak a PDF generálás javult.


### [2026.02.09] - Excel Export Robusztusság Növelése (Bugfix)
- **Hiba:** Hiányzó munkalapok az Excel exportban, csendes összeomlás a generálás során.
- **Ok:** A szigorú oszlopnév-egyeztetés (`"Terület (ha)"` vs `"Terület"`) és a numerikus konverziós hibák miatti kivételkezelés hiánya leállította a munkalapok írását.
- **Javítások:**
  - **Sheet-level try-except:** Minden munkalap írása elkülönített hibakezelést kapott, így egy hiba nem rántja magával a többi fület.
  - **Dinamikus oszlopillesztés:** A kód mostantól kulcsszavak alapján (pl. "terület", "méret", "ha") keresi a numerikus oszlopokat, nem pedig fix nevek alapján.
  - **Safe Worksheet Write:** Bevezetve a `try-except` a cellák írásakor is, hogy az illegális karakterek vagy típusok ne akasszák meg a folyamatot.
  - **Export_Log:** Új munkalap hozzáadva, amely felsorolja a generálás közben történt esetleges hibákat a "csendes összeomlás" elkerülése érdekében.
- **Érintett fájlok:** `dataexport/excel_exporter.py`, `hf-space/src/dataexport/excel_exporter.py`.
- **API Hatás:** Az API és a PDF generálás érintetlen maradt.

### [2026.02.09] - Excel Esztétikai és Nyomtatási Optimalizálás
- **Fejlesztés:** Teljes keret (grid lines) hozzáadása minden táblázathoz minden munkalapon.
- **Dinamikus oszlopszélesség:** A `_autoformat_columns` továbbfejlesztve, hogy a fejlécet és az adatokat is figyelembe véve számolja ki a szélességet, minden munkalapon egységesen.
- **Nyomtathatóság:** A keretek biztosítják, hogy az Excel fájlok nyomtatásban is átlátható táblázatként jelenjenek meg.
- **Vizuális fix (Végtelen rács):** Megoldva az a probléma, hogy a rácsvonalak lefutottak az üres sorokra is. Mostantól csak az adattartomány kap keretet.
- **Érintett fájlok:** `dataexport/excel_exporter.py`, `hf-space/src/dataexport/excel_exporter.py`.
- PDF generáló logika integrálása a FastAPI-ba (`api_app.py`).
- Base64 kódolt PDF visszaküldése az API-n keresztül.
