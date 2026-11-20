# Felhasználói útmutató – Mezőgazdasági Adatkinyerő v8.1

Ez az útmutató a Hugging Face-en futó Streamlit v8.1 webalkalmazás használatát írja le. Az alkalmazás Egységes Kérelem PDF-ekből nyer ki adatokat, megjeleníti azokat, és exportálható jelentéseket készít. A bal oldali sáv Súgó gombjával ez az útmutató az alkalmazásból is megnyitható. A projektgyökérben található párhuzamos, régebbi webes változat egyes részletekben eltérhet.

## 1. Rövid használati folyamat

1. Töltsd fel az egy vagy több feldolgozandó Egységes Kérelem PDF-et.
2. Kattints az Elemzés indítása gombra.
3. Várd meg, amíg minden fájl feldolgozása befejeződik.
4. A bal oldali Fájl kiválasztása listában válts a feldolgozott kérelmek között.
5. Nézd át az eredményeket a füleken.
6. Az Export fülön töltsd le az egyedi eredményt, vagy használd a ZIP letöltést. Ha több kérelem ugyanahhoz az üzemhez tartozik, készíthetsz összefűzött eredményt is.

## 2. PDF-ek feltöltése és feldolgozása

A feltöltő egy vagy több PDF-et fogad. Több fájlt egyszerre is ki lehet jelölni a fájlválasztóban. A felületen megadott fájlonkénti feltöltési korlát jelenleg 500 MB.

Az Elemzés indítása gomb végigfuttatja a kiválasztott PDF-eket. A folyamatjelző megmutatja az aktuális állapotot. A sikeresen feldolgozott kérelmek bekerülnek a bal oldali választólistába; a hibás fájlok hibajelzéssel jelennek meg.

Új PDF-ek feldolgozásakor a korábbi egyedi eredmények a munkamenetben maradnak; az azonos fájlnevű új feltöltés felülírja a korábbi eredményt. Az előző összefűzött eredmény új feltöltéskor törlődik, mert már nem feltétlenül lenne naprakész.

## 3. Az eredmény fülei

Az egyedi és az összefűzött eredmény ugyanazon a felületen jelenik meg.

- **Összefoglaló:** kérelmező neve és azonosítója, növényenkénti terület-összesítő, fő mutatók, például a fővetés és másodvetés területe, nitrátérzékeny terület, legnagyobb táblák összesített területe és a táblák száma.
- **Fővetés:** a PDF-ből kinyert fővetési táblasorok.
- **Másodvetés:** másodvetési és agrotechnikai bejegyzések. Ha a kérelem ugyanahhoz a bejegyzéshez eredeti és módosító változatot is tartalmaz, az alkalmazás a módosítót tartja meg. Az eredményeket itt is ellenőrizni kell az eredeti PDF alapján.
- **Összesítők:** támogatási jogcímek, hasznosítási adatok és blokkhasználat.
- **Export:** letölthető jelentések.

Az összesítő lap területi adatai ellenőrző célú számítások. A PDF-ben szereplő eredeti összesítő és a részletes adatsorok közötti eltérésre érdemes külön figyelni.

## 4. Kérelmek összefűzése

Az összefűzés akkor használható, ha legalább két kérelmet sikeresen feldolgozott az alkalmazásban.

1. Kattints a bal oldali **Kérelmek összefűzése (Béta)** gombra.
2. A megjelenő ablakban jelöld be az ugyanahhoz az üzemhez tartozó kérelmeket.
3. Legalább két kérelem kijelölése után aktiválódik az Összefűzés gomb.
4. A kész eredmény a választólistában **Összefűzött** néven jelenik meg.

Csak azokat jelöld ki együtt, amelyek valóban ugyanahhoz az üzemhez tartoznak. Az alkalmazás nem ellenőrzi automatikusan a gazdasági összetartozást.

### Mit csinál az összefűzés?

- A fővetési és másodvetési/agrotechnikai részletes sorokat egymás után hozzáfűzi.
- A részletes sorokat nem szűri ki táblasorszám alapján. A táblasorszám több kérelemben is azonos lehet, ezért a sorokat a program külön-külön megőrzi.
- A Fővetés és Másodvetés táblában egy **Kérelmező** oszlop jelzi, hogy az adott sor melyik kérelemből származik.
- Az azonos növénykódhoz tartozó hasznosítási területeket összeadja; ha egy növény csak az egyik kérelemben szerepel, az is megmarad.
- Az azonos nevű támogatási jogcímek területét összeadja.
- Azonos blokkazonosító esetén a blokkterületeket összeadja.
- Az összefoglaló számított fővetési és másodvetési területeit a részletes sorokból újraszámolja. A másodvetés területébe csak a Másodvetés típusú sorok számítanak bele; az agrotechnikai műveletek nem növelik a növényterületet.
- Az AKG és ÖKO területeket a kérelmenkénti növényösszesítőkből adja össze.
- A nitrátérzékeny és a legfeljebb öt legnagyobb fővetési tábla mutatóját az összefűzött fővetési sorokból újraszámolja.
- A támogatási igények és agrotechnikai műveletek felsorolásában az ismétlődő megnevezéseket egy tételként mutatja.

**Béta figyelmeztetés:** az összefűzés eredménye automatikusan nem tekinthető hivatalos vagy végleges adatnak. Minden esetben ellenőrizd a részletes sorokat és az összesítőket.

Az AKG és ÖKO oszlopok összefűzött növényösszesítőben való összeadása a HF v8.1 kiadás működése; a projektgyökér régebbi változata eltérhet.

## 5. Letöltés és export

### Egyedi kérelem

Az Export fülön ezek a formátumok érhetők el:

- **Excel (.xlsx):** munkalapok az adatfeldolgozási összefoglalóhoz, fővetéshez, másodvetéshez és a támogatási/területi összesítőkhöz.
- **PDF:** jelentés az összefoglalóról és a kinyert táblázatokról.
- **Markdown (.md):** szöveges, táblázatos jelentés.
- **JSON (.json):** strukturált adatkimenet.

### Összefűzött eredmény

Az összefűzött eredmény Export fülén jelenleg csak az Excel és a PDF letöltése aktív.

### ZIP letöltés

A bal oldali Tömeges Export részen elérhető ZIP az összes sikeresen feldolgozott egyedi kérelmet tartalmazza. Ha készült összefűzött eredmény, az is bekerül a ZIP-be.

- Egyedi kérelmenként: Excel, PDF, Markdown és JSON.
- Összefűzött eredményként: Excel és PDF.

A ZIP-ben a hibás feldolgozású fájlok nem kapnak exportot. Ha valamelyik formátum előállítása hibát jelez, az adott export hiányozhat a ZIP-ből.

## 6. Eredmények törlése

Az **Összes törlése (Hard Reset)** gomb törli a munkamenetben tárolt feldolgozott eredményeket és kiüríti a fájlfeltöltőt. A művelet után újra fel kell tölteni és elemezni a kérelmeket.

## 7. Adatkezelés és korlátok

- A PDF feldolgozásakor az alkalmazás a fájlt ideiglenes szerveroldali fájlba írja. A feldolgozás lezárásakor ezt törli.
- A kinyert adatok az aktív webes munkamenet memóriájában vannak; az alkalmazás nem készít tartós adatbázis-mentést. A Hard Reset törli az eredményeket.
- Az adatkinyerés PDF-szövegen és mintákon alapul. A PDF formátuma, szövegkódolása vagy elrendezése miatt adat maradhat ki vagy hibásan kerülhet kiolvasásra.
- A program eredményeit mindig vesd össze az eredeti PDF-fel. Különösen ellenőrizd az azonosítókat, területeket, jogcímeket és az összefűzött sorok forrását.
- Az összefűzés béta funkció, és a felhasználó által kijelölt kérelmek helyességét nem vizsgálja.

## 8. Gyakori problémák

**Nem jelenik meg egy kérelem a választólistában.**  
Ellenőrizd, hogy a feldolgozás sikeres volt-e. A hibás eredmény mellett hibaüzenet látható.

**Nem aktív az összefűzés gomb.**  
Az összefűzési ablak megnyitásához legalább két sikeresen feldolgozott kérelem szükséges. Az ablakon belül legalább két kérelmet kell kijelölni.

**Üres vagy hiányos egy táblázat.**  
Ellenőrizd a PDF megfelelő oldalait. Ha a PDF képként beszkennelt vagy szokatlan elrendezésű, a szövegkinyerés nem feltétlenül működik.

**Nem tölthető le az export.**  
Próbáld újra az exportfül megnyitása után. Ha hibaüzenet jelenik meg, jegyezd fel a kiválasztott kérelmet és a formátumot.

---
Útmutató az alkalmazás v8.1 webes felületéhez.
