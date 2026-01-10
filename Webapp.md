# Webalkalmazás tervezési dokumentáció

## Célkitűzés
A dokumentáció célja, hogy részletes tervet nyújtson a jelenlegi Python alapú alkalmazás JavaScript alapú webalkalmazássá történő átalakításához. A terv biztosítja, hogy az új alkalmazás megőrizze a meglévő funkcionalitást, felhasználói élményt és adatkinyerési mechanizmusokat.

## Jelenlegi alkalmazás elemzése
A jelenlegi alkalmazás Python nyelven íródott. Az adatkinyerés főként regex illesztésekkel történik. A felhasználói felület füles megjelenítést alkalmaz, és különböző figyelmeztető üzeneteket jelenít meg.

A főbb fájlok és azok szerepe:
* `main.py`: Az alkalmazás fő belépési pontja, kezeli a felhasználói interakciókat és az adatkinyerési folyamatot.
* `dataprocess/`: Adatfeldolgozási logika található itt.
* `GUI/gui_manager.py`: GUI kezelése.

## Javasolt technológiák
*   **Frontend:** React (komponens alapú architektúra, könnyű karbantartás), HTML, CSS
*   **Backend:** Node.js (JavaScript futtatókörnyezet), Express.js (webszerver)
*   **Adatbázis:** (opcionális, ha szükséges az adatok tárolása) MongoDB, PostgreSQL
*   **Egyéb:** Axios (HTTP kérések küldéséhez), Regex

## Webalkalmazás architektúra
Az alkalmazás egy kliens-szerver architektúrát követ. A kliens oldalon a React felel a felhasználói felület megjelenítéséért és a felhasználói interakciók kezeléséért. A szerver oldalon a Node.js és az Express.js kezeli a HTTP kéréseket, az adatkinyerést és az adatbázis műveleteket.

### Frontend (React)
*   Komponens alapú felépítés:
    *   Fő alkalmazás komponens (`App.js`): Kezeli az alkalmazás állapotát és a főbb nézeteket.
    *   Füles navigációs komponens (`Tabs.js`): Megvalósítja a füles navigációt.
    *   Adatkinyerő komponens (`DataExtractor.js`): Tartalmazza az adatkinyeréshez szükséges űrlapokat és vezérlőket.
    *   Eredmény megjelenítő komponens (`Results.js`): Megjeleníti a kinyert adatokat táblázatos formában.
    *   Figyelmeztető üzenet komponens (`Alert.js`): Megjeleníti a figyelmeztető üzeneteket.
*   Állapotkezelés: React useState hook-ok a komponensek állapotának kezeléséhez.

### Backend (Node.js, Express.js)
*   API végpontok:
    *   `/extract`: Fogadja az adatkinyerési kéréseket.
    *   `/data`: Adatbázisból származó adatok lekérdezése (opcionális).
*   Adatkinyerési logika:
    *   A szerver oldalon futnak a regex illesztések.
    *   A kinyert adatokat JSON formátumban küldi vissza a kliensnek.

## Adatkinyerési logika (Regex illesztések)
A következő regex illesztéseket kell átültetni JavaScriptbe:

### dataprocess/adatfeldolgozas_parser.py
```python
name_pattern = re.compile(
    r"(?:Kedvezményezett neve|4\s*-*\s*Kedvezményezett adatai\s*Név):\s*([^\n\r]+)", 
    re.IGNORECASE | re.DOTALL
)
id_pattern = re.compile(
    r"A kérelmező támogatási azonosítója:\s*(\d{10})|Támogatási azonosító:\s*(\d{10})"
)
pattern = re.compile(r'q4\s+([^\n\rq]+)', re.MULTILINE)
```

JavaScript megfelelője:

```javascript
const namePattern = new RegExp(
    "(?:Kedvezményezett neve|4\\s*-*\\s*Kedvezményezett adatai\\s*Név):\\s*([^\\n\\r]+)",
    "gi"
);
const idPattern = new RegExp(
    "A kérelmező támogatási azonosítója:\\s*(\\d{10})|Támogatási azonosító:\\s*(\\d{10})"
);
const pattern = new RegExp('q4\\s+([^\\n\\rq]+)', 'm');
```

### dataprocess/fovetes_parser.py
```python
block_pattern = re.compile(r"Blokkazonosító:\s*([A-Z0-9]+)")
nitrat_pattern = re.compile(r"Nitrátérzékeny terület:\s*(Igen|Nem)")
varmegye_pattern = re.compile(r"Vármegye:\s*([^\n]+)")
telepules_pattern = re.compile(r"Település:\s*([^\n]+)")
block_pattern2 = re.compile(
    r"Blokk:\s*(.*?)\s+Tábla:\s*(.*?)\s*(?:Állapot:\s*(.*?))?\n(.*?)(?=(?:Blokk: |8 — Másodvetés/Agrotechnika|—{3,}))", 
    re.DOTALL
)
fonoveny_match = re.search(r"Főnövény hasznosítási kód:\s*([A-Z0-9]+)\s*(.*?)\n", content)
terulet_match = re.search(r"Tábla igényelt terület \(ha\):\s*([\d,.]+)", content)
optional_fields = {
    "ÖKO": r"Ökológiai gazdálkodás:\s*([A-Za-zÁ-ú]+)",
    "Szap.anyag": r"Szaporítóanyag célra:\s*([A-Za-zÁ-ú]+)",
    "Telepítés": r"Főnövény vetési/telepítési időpontja:\s*([\d\.]+)",
    "Termőre ford.": r"Ültetvény termőre fordulásának éve:\s*(\d{4})"
}
```

JavaScript megfelelője:

```javascript
const blockPattern = /Blokkazonosító:\s*([A-Z0-9]+)/;
const nitratPattern = /Nitrátérzékeny terület:\s*(Igen|Nem)/;
const varmegyePattern = /Vármegye:\s*([^\n]+)/;
const telepulesPattern = /Település:\s*([^\n]+)/;
const blockPattern2 = /Blokk:\s*(.*?)\s+Tábla:\s*(.*?)\s*(?:Állapot:\s*(.*?))?\n(.*?)(?=(?:Blokk: |8 — Másodvetés\/Agrotechnika|—{3,}))/s;
const fonovenyMatch = /Főnövény hasznosítási kód:\s*([A-Z0-9]+)\s*(.*?)\n/;
const teruletMatch = /Tábla igényelt terület \(ha\):\s*([\d,.]+)/;
const optionalFields = {
    "ÖKO": /Ökológiai gazdálkodás:\s*([A-Za-zÁ-ú]+)/,
    "Szap.anyag": /Szaporítóanyag célra:\s*([A-Za-zÁ-ú]+)/,
    "Telepítés": /Főnövény vetési\/telepítési időpontja:\s*([\d\.]+)/,
    "Termőre ford.": /Ültetvény termőre fordulásának éve:\s*(\d{4})/
};
```

### dataprocess/masodvetes_parser.py
```python
re.split(r'(Blokk:\s*[A-Z0-9]+\s+Tábla:\s*\d+/\d+)', relevant_text_segment)
pattern = rf'{re.escape(keyword)}:?\s*([^\n\r]+?)(?=\s*(?:{stop_pattern})|\s*$)'
blokk_match = re.search(r'Blokk:\s*([A-Z0-9]+).*?Tábla:\s*(\d+)/(\d+)', block_text.split('\n')[0])
sorszam_match = re.search(r'sorszáma:\s*(\d+/\d+)', block_text)
terulet_match = re.search(r'Igényelt terület \(ha\):\s*([\d,\.]+)', block_text)
hasznositas_match = re.search(r'Hasznosítás:\s*([A-Z0-9]+)\s+([^\n\r]+?)(?=\s*(?:Vegyes|Másodvetés|Igényelt|$))', text, re.IGNORECASE)
vegyes_matches = re.findall(r'Vegyes hasznosítás [A-Z]:\s*([A-Z0-9]+)\s+([^\n\r]+?)(?=\s*(?:Vegyes hasznosítás|Igényelt|Másodvetés|$))', text, re.IGNORECASE)
```

JavaScript megfelelője:

```javascript
/(Blokk:\s*[A-Z0-9]+\s+Tábla:\s*\d+\/\d+)/
new RegExp(escapeRegExp(keyword) + ':?\\s*([^\\n\\r]+?)' + '(?=\\s*(?:' + stopPattern + ')|\\s*$)', 'i')
/Blokk:\s*([A-Z0-9]+).*?Tábla:\s*(\d+)\/(\d+)/
/sorszáma:\s*(\d+\/\d+)/
/Igényelt terület \(ha\):\s*([\d,\.]+)/
/Hasznosítás:\s*([A-Z0-9]+)\s+([^\n\r]+?)(?=\s*(?:Vegyes|Másodvetés|Igényelt|$))/i
/Vegyes hasznosítás [A-Z]:\s*([A-Z0-9]+)\s+([^\n\r]+?)(?=\s*(?:Vegyes hasznosítás|Igényelt|Másodvetés|$))/i
```

### dataprocess/osszesitok_parser.py
```python
jogcim_regex = r"Támogatási jogcímek és AKG célprogramok szerint\s*\n(.*?)(?=Területek összesítése hasznosítási adatok szerint)"
hasznositas_regex = r"Hasznosítási adatok szerint.*?\(főnövény, másodvetés, agrotechnika\)\s*\n(.*?)(?=Területek összesítése blokkhasználat szerint)"
blokk_regex = r"Területek összesítése blokkhasználat szerint\s*\n(.*?)(?=\n\d+\s*—|\n[A-Z\s]+ nyilatkozat|\Z)"
match = re.match(r'^(.*?)\s+([\d,.]+)$', line.strip())
pattern = re.compile(r"^([A-Z]{3}\d{2})\s+(.+?)\s+([\d,.]+)$")
```

JavaScript megfelelője:

```javascript
const jogcimRegex = /Támogatási jogcímek és AKG célprogramok szerint\s*\n(.*?)(?=Területek összesítése hasznosítási adatok szerint)/is;
const hasznositasRegex = /Hasznosítási adatok szerint.*?\(főnövény, másodvetés, agrotechnika\)\s*\n(.*?)(?=Területek összesítése blokkhasználat szerint)/is;
const blokkRegex = /Területek összesítése blokkhasználat szerint\s*\n(.*?)(?=\n\d+\s*—|\n[A-Z\s]+ nyilatkozat|\Z)/is;
const matchRegex = /^(.*?)\s+([\d,.]+)$/;
const patternRegex = /^([A-Z]{3}\d{2})\s+(.+?)\s+([\d,.]+)$/;
```
## Figyelmeztető üzenetek
A figyelmeztető üzenetek a felhasználót tájékoztatják a feldolgozás állapotáról és a lehetséges hibákról. Ezeket az üzeneteket a frontend oldalon kell megjeleníteni egy külön komponensben (`Alert.js`).

```python
# Példa regex illesztés Pythonban
import re

szoveg = "Valamilyen szöveg a mezőgazdasági adatokkal."
minta = r"mezőgazdasági adatok"
talalat = re.search(minta, szoveg)

if talalat:
    print("Találat!")
    print(talalat.group(0))
```

A fenti Python példa JavaScript megfelelője:

```javascript
// Példa regex illesztés JavaScriptben
const szoveg = "Valamilyen szöveg a mezőgazdasági adatokkal.";
const minta = /mezőgazdasági adatok/;
const talalat = szoveg.search(minta);

if (talalat !== -1) {
    console.log("Találat!");
    console.log(szoveg.substring(talalat, minta.source.length));
}
```

**Fontos:** Minden regex mintát alaposan tesztelni kell a JavaScript környezetben, mert a Python és a JavaScript regex motorjai között lehetnek különbségek.

Példák a regex illesztésekre (a teljesség igénye nélkül, a jelenlegi alkalmazásban használt minták alapján):

```javascript
// Dátum formátumok
const datumMinta = /\d{4}.\d{2}.\d{2}/; // ÉÉÉÉ.HH.NN

// Számok (tizedesvesszővel)
const szamMinta = /\d+,\d+/;

// Hivatkozások
const hivatkozasMinta = /http[s]?:\/\/\S+/;
```

A jelenlegi `adatfeldolgozas_parser.py`, `fovetes_parser.py`, `masodvetes_parser.py`, `osszesitok_parser.py` fájlokban található regex mintákat át kell ültetni és megfelelően tesztelni.

## Figyelmeztető üzenetek
A figyelmeztető üzenetek a felhasználót tájékoztatják a feldolgozás állapotáról és a lehetséges hibákról. Ezeket az üzeneteket a frontend oldalon kell megjeleníteni egy külön komponensben (`Alert.js`).

Példa figyelmeztető üzenet: "Nincs adat a megadott időszakban."

## Füles megjelenítés
A füles megjelenítés a felhasználói felület egyik fő eleme. A Reactben a füleket egy külön komponensben (`Tabs.js`) lehet megvalósítani.

## Megvalósítási terv
1.  **Környezet beállítása:**
    *   Node.js és npm telepítése.
    *   React projekt létrehozása (`create-react-app`).
    *   Express.js szerver létrehozása.
2.  **Frontend fejlesztés:**
    *   Komponensek létrehozása (Fülek, Adatkinyerő űrlap, Eredmény megjelenítő, Figyelmeztető üzenetek).
    *   Az alkalmazás állapotának kezelése (useState hook-ok).
    *   HTTP kérések küldése a szerver felé (Axios).
3.  **Backend fejlesztés:**
    *   API végpontok létrehozása (`/extract`, `/data`).
    *   Adatkinyerési logika implementálása (regex illesztések).
    *   Adatbázis integráció (opcionális).
4.  **Tesztelés:**
    *   Frontend komponensek tesztelése.
    *   Backend API végpontok tesztelése.
    *   Adatkinyerési logika tesztelése.
    *   Teljes alkalmazás tesztelése.
5.  **Telepítés:**
    *   Az alkalmazás telepítése egy web szerverre (pl. Netlify, Heroku).

## További megjegyzések
*   A regex illesztések átültetése során figyelni kell a JavaScript regex motor sajátosságaira.
*   A felhasználói felület tervezése során figyelembe kell venni a reszponzivitást (mobil eszközökön is jól működjön).
*   A kód minőségére és a karbantarthatóságra is figyelni kell.
