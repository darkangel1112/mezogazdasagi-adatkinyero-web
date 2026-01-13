# Fejlesztői Dokumentáció - Mezőgazdasági Adatkinyerő

## Változtatások naplója

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


### [Jövőbeli tervek]
- PDF generáló logika integrálása a FastAPI-ba (`api_app.py`).
- Base64 kódolt PDF visszaküldése az API-n keresztül.
