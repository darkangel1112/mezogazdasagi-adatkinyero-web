# Mezőgazdasági Adatkinyerő API - Technikai Dokumentáció (v1.0)

Ez a dokumentáció leírja, hogyan lehet külső alkalmazásból meghívni a mezőgazdasági PDF feldolgozó API-t, és hogyan lehet visszakapni az elemzés eredményét Markdown formátumban.

## 1. Hitelesítés

Az API minden kérést követel egy egyedi API kulcsot, amelyet a HTTP fejlécben kell átadni.

**Fejléc neve:** `X-API-Key`
**Aktuális kulcs:** `mezo-secret-2024` (Teszt környezet)

## 2. PDF Elemzés Végpont

Az elemzés indításához egy `POST` kérést kell küldeni a `/analyze` végpontra.

- **URL:** `https://[hf-space-url]/analyze`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

### Paraméterek:
- `file`: A feldolgozandó PDF fájl (Binary).

### Példa kérés (cURL):
```bash
curl -X 'POST' \
  'https://darkangel1112-mezogazdasagi-adatkinyero-web.hf.space/analyze' \
  -H 'accept: application/json' \
  -H 'X-API-Key: mezo-secret-2024' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@minta_kerelem.pdf;type=application/pdf'
```

## 3. Válasz Formátum

Az API sikeres feldolgozás esetén egy JSON objektumot ad vissza.

### Sikeres válasz (200 OK):
```json
{
  "success": true,
  "applicant": "Kovács János",
  "markdown": "# Egységes Kérelem Elemzés\n\n## Alapadatok\n...",
  "summary": {
    "total_area": 45.62,
    "tables_count": 12
  }
}
```

- `success`: Logikai érték a feldolgozás sikerességéről.
- `applicant`: A kérelemben talált kedvezményezett neve.
- `markdown`: A teljes elemzési riport Markdown formátumban.
- `summary`: Rövid statisztikai összefoglaló.

## 4. Példakódok

### Python (requests)
```python
import requests

url = "https://darkangel1112-mezogazdasagi-adatkinyero-web.hf.space/analyze"
headers = {"X-API-Key": "mezo-secret-2024"}
files = {"file": open("kerelem.pdf", "rb")}

response = requests.post(url, headers=headers, files=files)

if response.status_code == 200:
    data = response.json()
    with open("riport.md", "w", encoding="utf-8") as f:
        f.write(data["markdown"])
    print(f"Sikeres elemzés: {data['applicant']}")
else:
    print(f"Hiba: {response.status_code}, {response.text}")
```

### JavaScript (fetch)
```javascript
const fs = require('fs');
const FormData = require('form-data');
const fetch = require('node-fetch');

async function analyzePDF() {
    const form = new FormData();
    form.append('file', fs.createReadStream('kerelem.pdf'));

    const response = await fetch('https://darkangel1112-mezogazdasagi-adatkinyero-web.hf.space/analyze', {
        method: 'POST',
        headers: {
            'X-API-Key': 'mezo-secret-2024',
            ...form.getHeaders()
        },
        body: form
    });

    if (response.ok) {
        const data = await response.json();
        fs.writeFileSync('riport.md', data.markdown);
        console.log(`Sikeres elemzés: ${data.applicant}`);
    } else {
        console.error('Hiba a feldolgozás során');
    }
}
```

## 6. Strukturált JSON Végpont (ÚJ!)

Az `/ek/json` végpont ugyanazt a PDF feldolgozást végzi, de **strukturált JSON formátumban** adja vissza az adatokat, amely közvetlenül használható frontend táblázatokhoz és adatbázis integrációhoz.

### Endpoint

- **URL:** `https://[hf-space-url]/ek/json`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Hitelesítés:** Ugyanaz az `X-API-Key` header

### Paraméterek:
- `file`: A feldolgozandó PDF fájl (Binary)

### Példa kérés (cURL):
```bash
curl -X 'POST' \
  'https://darkangel1112-mezogazdasagi-adatkinyero-web.hf.space/ek/json' \
  -H 'accept: application/json' \
  -H 'X-API-Key: mezo-secret-2024' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@minta_kerelem.pdf;type=application/pdf'
```

### Válasz Formátum (200 OK):

```json
{
  "success": true,
  "applicant": "Csizmadia Lászlóné",
  "data": {
    "summary": [
      {
        "code": "ALL02",
        "name": "Állandó gyep (kaszált)",
        "mainCrop": 16.4703,
        "secondaryCrop": 0.0,
        "totalArea": 16.4703
      }
    ],
    "mainCrop": [
      {
        "county": "Zala",
        "settlement": "Zalakaros",
        "block": "Y08XR421",
        "table": 75,
        "code": "ALL02",
        "name": "Állandó gyep (kaszált)",
        "area": 0.5639,
        "eco": "Igen",
        "fertilizer": "N/A",
        "planting": "N/A",
        "termination": "N/A",
        "nitrate": "Igen"
      }
    ],
    "secondaryCrop": [
      {
        "block": "Y08XR421",
        "table": 75,
        "row": "75/2",
        "type": "Agrotechnika",
        "description": "Kaszálás alternáló vagy szársértő nélküli kasza használatával",
        "fertilizer": "N/A",
        "cropCode": "N/A",
        "area": 0.5639
      }
    ],
    "compliance": {
      "agrotechnika": [
        "Kaszálás alternáló vagy szársértő nélküli kasza használatával",
        "Középmély lazítás",
        "Mikrobiológiai készítmények alkalmazása"
      ],
      "tamogatas": [
        "Agro-ökológiai Program",
        "Termeléshez kötött növénytermesztés igazolások"
      ]
    },
    "statistics": {
      "mainCropArea": 271.7683,
      "secondaryCropArea": 208.8471,
      "nitrateArea": 271.77,
      "top5Area": 166.47,
      "tableCount": 35
    }
  }
}
```

### Példa Python kód:

```python
import requests

url = "https://darkangel1112-mezogazdasagi-adatkinyero-web.hf.space/ek/json"
headers = {"X-API-Key": "mezo-secret-2024"}
files = {"file": open("kerelem.pdf", "rb")}

response = requests.post(url, headers=headers, files=files)

if response.status_code == 200:
    data = response.json()
    
    # Fővetés táblák feldolgozása
    for table in data["data"]["mainCrop"]:
        print(f"Tábla {table['table']}: {table['name']} - {table['area']} ha")
    
    # Statisztikák
    stats = data["data"]["statistics"]
    print(f"Összes fővetés: {stats['mainCropArea']} ha")
    print(f"Táblák száma: {stats['tableCount']}")
else:
    print(f"Hiba: {response.status_code}")
```

### Részletes specifikáció:

A teljes JSON struktúra és mezőleírások az `API_JSON_SPEC.md` fájlban találhatók.

---

## 7. Tervezett fejlesztések (Hamarosan)
- **PDF Export:** Az API a JSON válaszban Base64 kódolással vissza fogja adni a generált PDF riportot is (`pdf_base64` mező).
- **Excel Export:** Tömeges feldolgozás esetén ZIP archívum letöltési lehetőség.
