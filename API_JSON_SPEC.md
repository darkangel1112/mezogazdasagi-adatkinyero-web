# 🔌 EK JSON API Specifikáció - Python Program Számára

## 📋 Áttekintés

Ez a dokumentum **pontosan** leírja, hogy milyen JSON struktúrát kell visszaadnia a Python programnak, hogy a frontend hibamentesen tudja importálni az Egységes Kérelem adatokat.

---

## 🎯 API Végpont

**URL:** `/api/extractor/analyze` (meglévő)  
**Method:** `POST`  
**Content-Type:** `multipart/form-data` vagy `application/json`  
**Response Type:** `application/json`

---

## 📦 Teljes Response Struktúra

```json
{
  "success": true,
  "applicant": "Csizmadia Lászlóné",
  "data": {
    "summary": [ /* EK Összesítő táblázat */ ],
    "mainCrop": [ /* EK Fővetés táblázat */ ],
    "secondaryCrop": [ /* EK Másodvetés/Agrotechnika táblázat */ ],
    "compliance": {
      "agrotechnika": [ /* Agrotechnikai műveletek lista */ ],
      "tamogatas": [ /* Támogatási igények lista {name, area} */ ]
    },
    "statistics": { /* Számított statisztikák */ }
  }
}
```

---

## 📊 1. EK Összesítő (summary)

**Frontend state:** `summaryData`  
**Típus:** `Array<SummaryRow>`

### SummaryRow Objektum

| Mező | Típus | Kötelező | Leírás | Példa |
|------|-------|----------|--------|-------|
| `code` | `string` | ✅ Igen | Növény NÉBIH kódja | `"ALL02"` |
| `name` | `string` | ✅ Igen | Növény megnevezése | `"Állandó gyep (kaszált)"` |
| `mainCrop` | `number` | ✅ Igen | Fővetés területe (hektár) | `16.4703` |
| `secondaryCrop` | `number` | ✅ Igen | Másodvetés területe (hektár) | `0.0` |
| `totalArea` | `number` | ⚪ Opcionális | Összesen terület (ha) | `16.4703` |

### Példa JSON

```json
"summary": [
  {
    "code": "ALL02",
    "name": "Állandó gyep (kaszált)",
    "mainCrop": 16.4703,
    "secondaryCrop": 0.0,
    "totalArea": 16.4703
  },
  {
    "code": "KAL27",
    "name": "Őszi tritikálé",
    "mainCrop": 1.0722,
    "secondaryCrop": 0.0,
    "totalArea": 1.0722
  },
  {
    "code": "FOR01",
    "name": "Lucerna",
    "mainCrop": 30.3862,
    "secondaryCrop": 0.0,
    "totalArea": 30.3862
  },
  {
    "code": "KEV01",
    "name": "Keverék kultúra",
    "mainCrop": 0.0,
    "secondaryCrop": 208.8471,
    "totalArea": 208.8471
  }
]
```

### ⚠️ Fontos Megjegyzések

1. **Hiányzó mezők:** A `landUse`, `rentedArea`, `freeLeaseArea` mezők **NEM** szükségesek! Ezeket a frontend állítja `null`/`0` értékre és a user tölti ki manuálisan.
2. **Számformátum:** Decimális számok, **NE** string! (pl. `16.4703` nem `"16.4703"`)
3. **Egyedi sorok:** Minden növénykód (`code`) csak **egyszer** szerepeljen!

---

## 🌾 2. EK Fővetés (mainCrop)

**Frontend state:** `mainCropData`  
**Típus:** `Array<MainCropRow>`

### MainCropRow Objektum

| Mező | Típus | Kötelező | Leírás | Példa |
|------|-------|----------|--------|-------|
| `county` | `string` | ✅ Igen | Vármegye | `"Zala"` |
| `settlement` | `string` | ✅ Igen | Település neve | `"Zalakaros"` |
| `block` | `string` | ✅ Igen | Blokk azonosító | `"Y08XR421"` |
| `table` | `number` | ✅ Igen | Tábla sorszám | `75` |
| `code` | `string` | ✅ Igen | Növény kódja | `"ALL02"` |
| `name` | `string` | ✅ Igen | Növény neve | `"Állandó gyep (kaszált)"` |
| `area` | `number` | ✅ Igen | Terület (hektár) | `0.5639` |
| `eco` | `string` | ✅ Igen | ÖKO gazdálkodás | `"Igen"` vagy `"Nem"` |
| `fertilizer` | `string` | ✅ Igen | Szaporító anyag használat | `"Igen"`, `"Nem"`, vagy `"N/A"` |
| `planting` | `string` | ⚪ Opcionális | Telepítés dátuma | `"2024.10.18"` vagy `"N/A"` |
| `termination` | `string` | ⚪ Opcionális | Termőre fordulás dátuma | `"2025.01.01"` vagy `"N/A"` |
| `nitrate` | `string` | ✅ Igen | Nitrátérzékeny terület | `"Igen"` vagy `"Nem"` |

### Példa JSON

```json
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
  },
  {
    "county": "Zala",
    "settlement": "Zalakomár",
    "block": "Y53V0821",
    "table": 7,
    "code": "KAL01",
    "name": "Őszi búza",
    "area": 2.2843,
    "eco": "Nem",
    "fertilizer": "Nem",
    "planting": "2024.10.18",
    "termination": "N/A",
    "nitrate": "Igen"
  }
]
```

### ⚠️ Fontos Megjegyzések

1. **table:** Szám típus, nem string! (`75` nem `"75"`)
2. **eco, fertilizer, nitrate:** Pontosan `"Igen"` vagy `"Nem"` string, kis-nagybetű érzékeny!
3. **Dátumok:** `YYYY.MM.DD` formátum vagy `"N/A"` ha nincs adat
4. **N/A kezelés:** Ahol nincs releváns adat (pl. állandó gyep telepítése), használj `"N/A"` stringet
5. **fertilizerStr mező NEM kell!** (Ez a "Műtrágya" oszlop, jelenleg nem használjuk)

---

## 🌱 3. EK Másodvetés/Agrotechnika (secondaryCrop)

**Frontend state:** `secondaryCropData`  
**Típus:** `Array<SecondaryCropRow>`

### SecondaryCropRow Objektum

| Mező | Típus | Kötelező | Leírás | Példa |
|------|-------|----------|--------|-------|
| `block` | `string` | ✅ Igen | Blokk azonosító | `"Y08XR421"` |
| `table` | `number` | ✅ Igen | Tábla sorszám | `75` |
| `row` | `string` | ✅ Igen | Sorszám (Blokk/Tábla formátum) | `"75/2"` |
| `type` | `string` | ✅ Igen | Típus | `"Agrotechnika"` vagy `"Másodvetés"` |
| `description` | `string` | ✅ Igen | Művelet/növény megnevezése | `"Kaszálás alternáló vagy szársértő nélküli..."` |
| `fertilizer` | `string` | ⚪ Opcionális | Anyag megnevezése | `"Keverék kultúra"` vagy `"N/A"` |
| `cropCode` | `string` | ⚪ Opcionális | Növénykód (csak Másodvetésnél) | `"KEV01"` vagy `"N/A"` |
| `area` | `number` | ✅ Igen | Terület (hektár) | `0.5639` |

### Példa JSON

```json
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
  },
  {
    "block": "Y807XK21",
    "table": 45,
    "row": "45/8",
    "type": "Másodvetés",
    "description": "Másodvetés zöldtrágyázás céljából",
    "fertilizer": "Keverék kultúra",
    "cropCode": "KEV01",
    "area": 4.9306
  },
  {
    "block": "Y1D7WP21",
    "table": 2,
    "row": "2/3",
    "type": "Agrotechnika",
    "description": "Középmély lazítás",
    "fertilizer": "N/A",
    "cropCode": "N/A",
    "area": 3.2194
  }
]
```

### ⚠️ Fontos Megjegyzések

1. **type:** Pontosan `"Agrotechnika"` vagy `"Másodvetés"` (kis-nagybetű érzékeny!)
2. **row:** String formátum, pl. `"75/2"`, `"10/1"`
3. **cropCode:** Csak `"Másodvetés"` típusnál van értelme, `"Agrotechnika"`-nál `"N/A"`
4. **fertilizer (Anyag):** Csak `"Másodvetés"` típusnál releváns (pl. `"Keverék kultúra"`), egyébként `"N/A"`

---

## 📋 4. Jogcímek & Műveletek (compliance)

**Frontend state:** `agrotechnikaData`, `tamogatasData`  
**Típus:** `Object`

### Compliance Objektum

```typescript
{
  "agrotechnika": string[],  // Egyedi agrotechnikai műveletek listája
  "tamogatas": {             // Támogatási igények lista
    name: string;
    area: number;
  }[]
}
```

### Példa JSON

```json
"compliance": {
  "agrotechnika": [
    "Kaszálás alternáló vagy szársértő nélküli kasza használatával",
    "Középmély lazítás",
    "Mikrobiológiai készítmények alkalmazása",
    "Melléktermék bedolgozása"
  ],
  "tamogatas": [
    {
      "name": "Agro-ökológiai Program",
      "area": 269.4581
    },
    {
      "name": "Termeléshez kötött növénytermesztés igazolások",
      "area": 51.9874
    },
    {
      "name": "ST - Agrár-környezetgazdálkodás 2024",
      "area": 29.5432
    }
  ]
}
```

### ⚠️ Fontos Megjegyzések

1. **Egyedi értékek:** Minden elem csak egyszer szerepeljen! (Duplikációk szűrése)
2. **Sorrend:** Nem számít, de logikus ha alfabetikusan vagy fontosság szerint vannak
3. **agrotechnika:** Csak a `secondaryCrop` tömbből származó **egyedi** `description` értékek, ahol `type === "Agrotechnika"`
4. **tamogatas:** A PDF-ből kinyert támogatási jogcímek listája

---

## 📊 5. Statisztikák (statistics)

**Frontend state:** `stats` (automatikusan számolt is, de hasznos visszaküldeni validációhoz)  
**Típus:** `Object`

### Statistics Objektum

| Mező | Típus | Kötelező | Leírás | Példa |
|------|-------|----------|--------|-------|
| `mainCropArea` | `number` | ✅ Igen | Összes fővetés terület (ha) | `271.7683` |
| `secondaryCropArea` | `number` | ✅ Igen | Összes másodvetés terület (ha) | `208.8471` |
| `nitrateArea` | `number` | ✅ Igen | Nitrátérzékeny terület (ha) | `271.77` |
| `top5Area` | `number` | ✅ Igen | Top 5 legnagyobb tábla összterülete (ha) | `166.47` |
| `tableCount` | `number` | ✅ Igen | Táblák száma | `35` |

### Példa JSON

```json
"statistics": {
  "mainCropArea": 271.7683,
  "secondaryCropArea": 208.8471,
  "nitrateArea": 271.77,
  "top5Area": 166.47,
  "tableCount": 35
}
```

### ⚠️ Fontos Megjegyzések

1. **Számítás:** 
   - `mainCropArea`: `sum(summary[].mainCrop)`
   - `secondaryCropArea`: `sum(summary[].secondaryCrop)`
   - `nitrateArea`: `sum(mainCrop[].area where nitrate === "Igen")`
   - `top5Area`: Top 5 legnagyobb táblák területének összege fővetésből
   - `tableCount`: `mainCrop.length` (táblák száma)

2. **Validáció:** A frontend újraszámolja ezeket, de jó ha látjuk hogy egyezik-e!

---

## ✅ Teljes Minta Response

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
      },
      {
        "code": "KAL01",
        "name": "Őszi búza",
        "mainCrop": 36.9736,
        "secondaryCrop": 0.0,
        "totalArea": 36.9736
      },
      {
        "code": "KEV01",
        "name": "Keverék kultúra",
        "mainCrop": 0.0,
        "secondaryCrop": 208.8471,
        "totalArea": 208.8471
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
      },
      {
        "county": "Zala",
        "settlement": "Zalakomár",
        "block": "Y53V0821",
        "table": 7,
        "code": "KAL01",
        "name": "Őszi búza",
        "area": 2.2843,
        "eco": "Nem",
        "fertilizer": "Nem",
        "planting": "2024.10.18",
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
      },
      {
        "block": "Y807XK21",
        "table": 45,
        "row": "45/8",
        "type": "Másodvetés",
        "description": "Másodvetés zöldtrágyázás céljából",
        "fertilizer": "Keverék kultúra",
        "cropCode": "KEV01",
        "area": 4.9306
      }
    ],
    "compliance": {
      "agrotechnika": [
        "Kaszálás alternáló vagy szársértő nélküli kasza használatával",
        "Középmély lazítás",
        "Mikrobiológiai készítmények alkalmazása",
        "Melléktermék bedolgozása"
      ],
      "tamogatas": [
        "Agro-ökológiai Program",
        "Termeléshez kötött növénytermesztés igazolások",
        "ST - Agrár-környezetgazdálkodás 2024"
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

---

## 🔥 Kritikus Szabályok

### ✅ DO (Csináld)

1. **Számok számként:** Minden `area`, `mainCrop`, `secondaryCrop` mező legyen `number`, NE `string`!
2. **Pontos string értékek:** `"Igen"` / `"Nem"` kis-nagybetű helyesen!
3. **Egyedi listák:** `compliance.agrotechnika` és `compliance.tamogatas` ne tartalmazzon duplikátumokat
4. **Sorrend:** `table` mező legyen `number` típus
5. **N/A használat:** Ahol nincs adat, használj `"N/A"` stringet (nem `null`, nem `""`)

### ❌ DON'T (Ne csináld)

1. **NE** küldj `markdown` mezőt! (felesleges, nem használjuk)
2. **NE** keverd a `type` értékeket (`"Agrotechnika"` vs `"agrotechnika"`)
3. **NE** használj `null` értékeket számokra (használj `0`-t)
4. **NE** használj magyar karaktereket JSON key-ekben (maradjon angol: `mainCrop` nem `fővetes`)
5. **NE** add vissza az `Összesen:` sort a `summary` tömbben (csak a tényleges növények)

---

## 🧪 Teszt Checklist Python Fejlesztőnek

Mielőtt élesbe megy, ellenőrizd:

- [ ] **JSON valid?** (JSON parser nem dob hibát)
- [ ] **Számok számok?** (`typeof area === 'number'`)
- [ ] **table mező szám?** (nem string)
- [ ] **eco/fertilizer/nitrate értékek?** (`"Igen"` / `"Nem"` / `"N/A"`)
- [ ] **type értékek?** (`"Agrotechnika"` / `"Másodvetés"`)
- [ ] **Duplikációk szűrve?** (`compliance` listák egyediek)
- [ ] **Statisztikák helyesek?** (összegek egyeznek a tömb összegzésével)
- [ ] **Minden kötelező mező jelen van?**

---

## 📝 TypeScript Típus Definíciók (Referencia)

```typescript
interface EkApiResponse {
  success: boolean;
  applicant: string;
  data: {
    summary: SummaryRow[];
    mainCrop: MainCropRow[];
    secondaryCrop: SecondaryCropRow[];
    compliance: {
      agrotechnika: string[];
      tamogatas: {
        name: string;
        area: number;
      }[];
    };
    statistics: {
      mainCropArea: number;
      secondaryCropArea: number;
      nitrateArea: number;
      top5Area: number;
      tableCount: number;
    };
  };
}

interface SummaryRow {
  code: string;
  name: string;
  mainCrop: number;
  secondaryCrop: number;
  totalArea?: number;
}

interface MainCropRow {
  county: string;
  settlement: string;
  block: string;
  table: number;
  code: string;
  name: string;
  area: number;
  eco: "Igen" | "Nem";
  fertilizer: "Igen" | "Nem" | "N/A";
  planting?: string;
  termination?: string;
  nitrate: "Igen" | "Nem";
}

interface SecondaryCropRow {
  block: string;
  table: number;
  row: string;
  type: "Agrotechnika" | "Másodvetés";
  description: string;
  fertilizer?: string;
  cropCode?: string;
  area: number;
}
```

---

**Verzió:** 1.0  
**Utolsó frissítés:** 2026-01-13  
**Készítette:** Antigravity AI a darkangel1112/Partnerkezelo projekt számára
