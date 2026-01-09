# Heatly Cloud for Home Assistant (Alpha)
Dette er den offisielle Home Assistant-integrasjonen for Heatly. Integrasjonen bruker fysikkmodeller og algoritmer fra Heatly Cloud for å optimalisere varmestyringen din basert på strømpris, værmelding og din boligs termiske egenskaper.

## Funksjoner
- Intelligent Termostat-as-a-service: Heatly Cloud tar beslutninger, Home Assistant utfører.
- Enkel Onboarding: GUI-basert oppsett uten behov for YAML-konfigurasjon.
- Automatisk sensor data sync: Sender temperaturdata minimum hvert minutt til Heatly API.
- Støtte for utendørs temperatur: Forbedrer MPC-prediksjoner med værdata.

## Installasjon
### Metode 1: HACS (Anbefalt)
* Åpne HACS i din Home Assistant.
* Klikk på de tre prikkene øverst i høyre hjørne og velg Custom repositories.
* Lim inn URL-en til dette GitHub-repoet.
* Velg kategorien Integration og klikk Add.
* Finn "Heatly Cloud" i listen og klikk Download.
* Restart Home Assistant.

## Oppsett (Onboarding)

### Steg 1: Opprett rom i Heatly Frontend
1. Gå til [https://heatly.no](https://heatly.no) (eller din lokale frontend)
2. Logg inn med din bruker
3. Gå til Dashboard og klikk "Add Room"
4. Fyll ut romdetaljer:
   - Room ID (f.eks. `living_room_01`)
   - Name (f.eks. "Living Room")
   - Heater Power (watts)
   - Active Schedule
5. Noter deg Room ID - du trenger dette i neste steg

### Steg 2: Konfigurer Home Assistant-integrasjonen
Når integrasjonen er installert og HA er startet på nytt:

* Gå til Settings -> Devices & Services.
* Klikk på Add Integration nederst til høyre.
* Søk etter Heatly Cloud.

Fyll ut skjemaet:
* **Room ID**: Room ID fra steg 1 (f.eks. `living_room_01`)
* **Temperature Sensor**: Velg din eksisterende temperatursensor i HA
* **Heater Switch**: Velg bryteren, smartpluggen eller ovnen som skal styres
* **Outdoor Temperature Sensor** (valgfritt): Velg utendørs temperatursensor for bedre prediksjoner
* **API URL**: URL til Heatly Python API (standard: `http://localhost:5364`)

Klikk Submit.

## Bruk
Integrasjonen vil nå opprette en ny termostat-enhet kalt Heatly [Ditt Rom]. Du kan legge denne til i ditt dashbord som et vanlig "Thermostat Card".

**Merk:** Siden dette er en AI-styrt termostat, vil den automatisk hoppe mellom "Heating" (på) og "Idle/Off" basert på instruksjoner fra Heatly Cloud.

## Data Flow
1. **Sensor Data**: Home Assistant → Heatly Python API (minimum hvert minutt)
2. **MPC Computation**: Heatly Python API beregner optimal varmestrategi
3. **Control Decision**: Heatly Python API → Home Assistant (heater on/off)
4. **Data Sync**: Python API → WordPress MySQL (hver 2. minutt for frontend visning)

## Feilsøking

### "API feil: Connection refused"
- Sjekk at Heatly Python API kjører på konfigurert URL
- Verifiser at API URL er korrekt i integrasjonskonfigurasjonen

### "Room not found"
- Sjekk at Room ID matcher eksakt med rommet opprettet i frontend
- Vent noen minutter for synkronisering mellom WordPress og Python API

### Sensor data kommer ikke frem
- Sjekk at temperatursensor rapporterer gyldige verdier
- Se i Home Assistant logs for feilmeldinger fra Heatly

## Support
For hjelp og support, kontakt support@heatly.no eller besøk [dokumentasjonen](https://github.com/ToreAndreRosander/heatly-cloud).