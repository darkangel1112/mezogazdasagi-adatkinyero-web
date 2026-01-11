# Fejlesztői Dokumentáció - Mezőgazdasági Adatkinyerő

## Változtatások naplója

### [2026.01.11] - API Dokumentáció és MD fókusz
- **API Leírás:** Létrehozva az `api.md` fájl, amely tartalmazza a `/analyze` végpont használatát, a hitelesítést és példakódokat Python/JS nyelven.
- **Routing Javítás:** Nginx konfiguráció módosítása (`hf-space/nginx.conf`), hogy helyesen kezelje a `/api` prefixet (trailing slash hozzáadása), így a FastAPI helyesen kapja meg az útvonalakat.
- **API Javítás:** `api_app.py` függvényhívásainak javítása (AttributeError fix). A parser modulok függvénynevei (`_extract_applicant_data`, `_extract_support_requests`, stb.) most már helyesen vannak meghívva.
- **Parser Robusztusság:** Fallback regex mechanizmus implementálása az `osszesitok_parser.py`-ban. Ha a szigorú regex nem talál egyezést (pl. Space környezetben eltérő sortörések miatt), egy lazább regex próbálkozik az adatkinyeréssel.
- **Tervezés:** Az API jelenlegi állapota szerint csak Markdown-t ad vissza. A PDF visszaküldés a következő fázisban valósul meg.
- **DPI Beállítás:** (Korábbi módosítások alapján) A default DPI 300-ra lett állítva, 500 DPI opció hozzáadva.
- **Modellek:** Gemini 2.5 Pro és 3.0 Pro opciók előkészítve a konfigurációs felületen.

### [Jövőbeli tervek]
- PDF generáló logika integrálása a FastAPI-ba (`api_app.py`).
- Base64 kódolt PDF visszaküldése az API-n keresztül.
