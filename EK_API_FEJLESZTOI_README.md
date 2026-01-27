# 📋 EK JSON API - Fejlesztői Útmutató

## 🎯 Áttekintés

Ez a dokumentum segít a Python fejlesztőnek új JSON API végpont létrehozásához az Egységes Kérelem (EK) PDF feldolgozó rendszerhez.

---

## 🏗️ Projekt Háttér

**Projekt neve:** Partnerkezelő  
**Technológia:** React (Frontend) + Node.js/Express (Backend) + Python (PDF feldolgozás)  
**Cél:** Mezőgazdasági partnerek adatainak kezelése, beleértve az EU támogatási "Egységes Kérelem" dokumentumok feldolgozását

### Mi az Egységes Kérelem (EK)?

Az Egységes Kérelem egy hivatalos EU támogatási dokumentum, amit mezőgazdák töltenek ki évente. Tartalmazza:
- Táblák területi adatait (fővetés, másodvetés)
- Növénykultúra információkat
- Agrotechnikai műveleteket
- Támogatási jogcímeket

---

## 📂 Jelenlegi Helyzet

### ✅ Ami már működik:

A Python program jelenleg:
1. PDF-et kap inputként (`/api/extractor/analyze` endpoint)
2. Feldolgozza OCR-rel és AI-val
3. **Markdown** formátumú jelentést ad vissza
4. A markdown táblázatokat tartalmaz az EK adatokról

### ❌ Mi a probléma?

A frontend **nem tud** hatékonyan dolgozni markdown táblázatokkal:
- Parsolni kell → lassú, hibára hajlamos
- Típusok elvesznek (minden string lesz)
- Nehéz integrálni az adatbázisba

---

## 🎯 Feladat

**Cél:** Módosítsd a Python scriptet, hogy **strukturált JSON**-t adjon vissza markdown helyett (vagy mellett).

### Pontosan mit kell csinálni?

1. **Olvasd el:** `API_JSON_SPEC.md` - Ez a teljes specifikáció
2. **Módosítsd:** A Python script output-ját az új formátumra
3. **Tesztelj:** Az `SL_EK25.json` minta alapján
4. **Validálj:** A spec végén van checklist

---

## 📄 Dokumentumok

| Fájl | Leírás |
|------|--------|
| **`API_JSON_SPEC.md`** | ⭐ **FŐSPECIFIKÁCIÓ** - Ezt kövesd! Minden mező, típus, példa itt van |
| `SL_EK25.json` | Minta adat - referencia, hogy milyen adatokat várunk |
| `EK_API_FEJLESZTOI_README.md` | Ez a fájl - általános kontextus |

---

## 🔍 Fontos Részletek

### 1. API Endpoint információk

**Jelenlegi endpoint:** `/api/extractor/analyze`  
**Method:** `POST`  
**Input:** PDF fájl (multipart/form-data)  
**Output (RÉGI):** 
```json
{
  "success": true,
  "markdown": "# Táblázatok...",
  "summary": { /* egyszerű összegzés */ }
}
```

**Output (ÚJ - AMIT KELL):**
```json
{
  "success": true,
  "applicant": "Gazda Neve",
  "data": {
    "summary": [ /* 5 mezős objektumok tömbje */ ],
    "mainCrop": [ /* 12 mezős objektumok tömbje */ ],
    "secondaryCrop": [ /* 8 mezős objektumok tömbje */ ],
    "compliance": {
      "agrotechnika": [ /* string tömb */ ],
      "tamogatas": [ /* string tömb */ ]
    },
    "statistics": { /* 5 mező */ }
  }
}
```

### 2. Kritikus követelmények

⚠️ **Ezeket KÖTELEZŐ betartani:**

1. **Számok számként:**
   - `"area": 16.4703` ✅
   - `"area": "16.4703"` ❌

2. **`table` mező szám:**
   - `"table": 75` ✅
   - `"table": "75"` ❌

3. **Enum értékek pontosan:**
   - `"eco": "Igen"` vagy `"Nem"` ✅
   - `"eco": "igen"` vagy `"yes"` ❌

4. **N/A string használat:**
   - `"planting": "N/A"` ✅ (ha nincs adat)
   - `"planting": null` ❌
   - `"planting": ""` ❌

### 3. Struktúra részletei

**5 fő objektum van:**

| Objektum | Leírás | Elemszám (példa) |
|----------|--------|------------------|
| `summary` | Növények összesítő táblázata | ~7 növény |
| `mainCrop` | Fővetés táblák részletes adatai | ~35 tábla |
| `secondaryCrop` | Másodvetés + Agrotechnika műveletek | ~64 bejegyzés |
| `compliance.agrotechnika` | Egyedi agrotechnikai műveletek listája | ~4 művelet |
| `compliance.tamogatas` | Támogatási jogcímek listája | ~3 jogcím |

---

## 🧪 Tesztelés

### Teszt file használata:

A `SL_EK25.json` fájl tartalmaz egy majdnem megfelelő példát. **DE FIGYELEM:**
- A benne levő struktúra NEM pontos! (van benne `markdown` mező ami NEM kell)
- Az új API válasznak pontosan az `API_JSON_SPEC.md` szerint kell kinéznie
- A SL_EK25.json csak referencia, hogy milyen adatok vannak az EK-ban

### Ellenőrző lista (Spec végéről):

Mielőtt élesbe kerül:

- [ ] JSON valid?
- [ ] Számok számmá alakítva?
- [ ] `table` mező szám típusú?
- [ ] `eco`, `fertilizer`, `nitrate` értékek helyesek?
- [ ] `type` értékek helyesek? (`"Agrotechnika"` / `"Másodvetés"`)
- [ ] Duplikációk szűrve a `compliance` listákban?
- [ ] Statisztikák helyesen számolva?
- [ ] Minden kötelező mező jelen van?

---

## 🛠️ Implementációs Tippek

### Javasolt Python struktúra:

```python
def generate_ek_json(parsed_data):
    """
    Parsed PDF adatokból strukturált JSON generálása.
    """
    return {
        "success": True,
        "applicant": extract_applicant_name(parsed_data),
        "data": {
            "summary": build_summary_array(parsed_data),
            "mainCrop": build_main_crop_array(parsed_data),
            "secondaryCrop": build_secondary_crop_array(parsed_data),
            "compliance": {
                "agrotechnika": extract_unique_agrotechnika(parsed_data),
                "tamogatas": extract_tamogatas_list(parsed_data)
            },
            "statistics": calculate_statistics(parsed_data)
        }
    }
```

### Számítások:

**statistics mező számítási logika:**

```python
def calculate_statistics(data):
    summary = data['summary']
    main_crop = data['mainCrop']
    
    # Összes fővetés
    main_crop_area = sum(row['mainCrop'] for row in summary)
    
    # Összes másodvetés
    secondary_crop_area = sum(row['secondaryCrop'] for row in summary)
    
    # Nitrátérzékeny terület (csak ahol nitrate === "Igen")
    nitrate_area = sum(
        row['area'] for row in main_crop 
        if row['nitrate'] == "Igen"
    )
    
    # Top 5 tábla (legnagyobb területek)
    sorted_tables = sorted(main_crop, key=lambda x: x['area'], reverse=True)
    top5_area = sum(row['area'] for row in sorted_tables[:5])
    
    # Táblák száma
    table_count = len(main_crop)
    
    return {
        "mainCropArea": round(main_crop_area, 4),
        "secondaryCropArea": round(secondary_crop_area, 4),
        "nitrateArea": round(nitrate_area, 2),
        "top5Area": round(top5_area, 2),
        "tableCount": table_count
    }
```

---

## 📞 Kérdések?

Ha bármi nem egyértelmű, az `API_JSON_SPEC.md` fájl részletesen leírja:
- Minden mező típusát
- Példa értékeket
- Kötelezőséget
- DO / DON'T szabályokat

**Minden válasz ott van!** ✅

---

## ✅ Sikerkritériumok

Az API akkor KÉSZ, ha:

1. ✅ A válasz JSON valid és megfelel az `API_JSON_SPEC.md`-nek
2. ✅ Minden szám `number` típus (nem string)
3. ✅ A `type`, `eco`, `nitrate` enum értékek pontosak
4. ✅ A `compliance` listák nem tartalmaznak duplikátumokat
5. ✅ A `statistics` értékek helyesen számoltak
6. ✅ Teszt PDF-fel sikeresen fut
7. ✅ A frontend hiba nélkül tudja importálni

---

**Készült:** 2026-01-13  
**Projekt:** darkangel1112/Partnerkezelo  
**Verzió:** 1.0
