# Heatly Cloud for Home Assistant (Alpha)
Dette er den offisielle Home Assistant-integrasjonen for Heatly. Integrasjonen bruker fysikkmodeller og algoritmer fra Heatly Cloud for å optimalisere varmestyringen din basert på strømpris, værmelding og din boligs termiske egenskaper.

## Funksjoner
- **Hybrid Smart/Dumb Controller**: Velg mellom intelligent AI-styring (AUTO-modus) eller lokal termostat-kontroll (HEAT-modus)
- **Multiple Heater Support**: Kontroller flere varmeovner samtidig i samme rom
- **Schedule Selection**: Velg mellom ulike forhåndskonfigurerte varmeprogram direkte fra Home Assistant
- **Local Failsafe**: Automatisk lokal termostat-kontroll hvis API-tilkoblingen går ned
- **State Persistence**: Bevarer innstillinger ved omstart av Home Assistant
- **Intelligent Termostat-as-a-service**: Heatly Cloud tar beslutninger, Home Assistant utfører
- **Enkel Onboarding**: GUI-basert oppsett uten behov for YAML-konfigurasjon
- **Automatisk sensor data sync**: Sender temperaturdata minimum hvert minutt til Heatly API
- **Støtte for utendørs temperatur**: Forbedrer MPC-prediksjoner med værdata

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
* **Heater Switch(es)**: Velg én eller flere brytere, smartplugger eller ovner som skal styres
* **Outdoor Temperature Sensor** (valgfritt): Velg utendørs temperatursensor for bedre prediksjoner
* **API URL**: URL til Heatly Python API (standard: `http://localhost:5364`)
* **Cold Tolerance** (valgfritt): Grader under måltemperatur før varmen slås på (standard: 0.5°C)
* **Hot Tolerance** (valgfritt): Grader over måltemperatur før varmen slås av (standard: 0.5°C)

Klikk Submit.

## Bruk

### Termostat Modes

Integrasjonen vil opprette en ny termostat-enhet kalt Heatly [Ditt Rom]. Termostaten støtter tre driftsmodus:

#### AUTO (Smart Mode) - Anbefalt
- Heatly Cloud AI kontrollerer varmen basert på strømpris, værmelding og termisk modell
- MPC (Model Predictive Control) optimaliserer energiforbruk
- Krever aktiv tilkobling til Heatly API
- Best for daglig bruk og optimal energiøkonomi

#### HEAT (Local Mode) - Backup/Override
- Lokal "dum" termostat med hysterese-logikk
- Fungerer uten internett eller API-tilkobling
- Enkel på/av-kontroll basert på temperatur
- Bruk ved:
  - API-problemer
  - Behov for manuell overstyring
  - Testing av utstyr

#### OFF
- Slår av alle varmeovner
- Termostaten er deaktivert

### Schedule Selection (Preset Modes)

Velg mellom ulike varmeprogram ved å endre "Preset Mode" i Home Assistant:
- **hverdag**: Standard ukeplan for arbeidsdager
- **helg**: Helgeplan med lengre morgensøvn
- **kalibrering**: Full temperatur-frihet for kalibrering
- **kontor_hverdag**: Arbeidsplan for kontormiljø
- **medium_18_24**: Konstant moderat temperatur
- **lav_14_22**: Lavere temperaturområde
- **lav_14_15**: Minimal temperatur

Endringer synkroniseres automatisk til både Python API og WordPress database.

### Multiple Heaters

Hvis du har konfigurert flere varmeovner for samme rom:
- Alle ovner kontrolleres simultant (slås på/av samtidig)
- Brukbart for store rom med flere varmeelementer
- Støtter switches, input_boolean og lights som aktuatorer

### Hysteresis Configuration

For å unngå hyppig på/av-svitching ("short cycling") i HEAT-modus:
- **Cold Tolerance**: Hvor mye kaldere enn måltemperatur før varmen slås på
- **Hot Tolerance**: Hvor mye varmere enn måltemperatur før varmen slås av
- Eksempel: Med target 20°C og toleranser på 0.5°C:
  - Varme PÅ når temp ≤ 19.5°C
  - Varme AV når temp ≥ 20.5°C
  - Ingen endring mellom 19.5-20.5°C (deadband)

Juster disse verdiene via Settings -> Devices & Services -> Heatly Cloud -> Configure.

## Data Flow
1. **Sensor Data**: Home Assistant → Heatly Python API (minimum hvert minutt)
2. **MPC Computation**: Heatly Python API beregner optimal varmestrategi (kun i AUTO-modus)
3. **Control Decision**: 
   - AUTO: Heatly Python API → Home Assistant (heater on/off)
   - HEAT: Lokal bang-bang controller i Home Assistant
4. **Data Sync**: Python API → WordPress MySQL (hver 2. minutt for frontend visning)

## Feilsøking

### "API feil: Connection refused"
- Sjekk at Heatly Python API kjører på konfigurert URL
- Verifiser at API URL er korrekt i integrasjonskonfigurasjonen
- Bytt til HEAT-modus for lokal kontroll mens API er nede

### "Room not found"
- Sjekk at Room ID matcher eksakt med rommet opprettet i frontend
- Vent noen minutter for synkronisering mellom WordPress og Python API

### Sensor data kommer ikke frem
- Sjekk at temperatursensor rapporterer gyldige verdier
- Se i Home Assistant logs for feilmeldinger fra Heatly

### Termostaten bytter ikke modus
- Sjekk logger for feilmeldinger
- Verifiser at varmeovn-enheten fungerer korrekt
- Test manuelt å slå varmeovnen på/av fra Home Assistant

### Hyppig på/av-svitching
- Øk hysteresis-verdiene (cold_tolerance og hot_tolerance)
- Standard 0.5°C kan økes til 1.0°C eller mer for roligere drift
- Kun relevant i HEAT-modus

## Support
For hjelp og support, kontakt support@heatly.no eller besøk [dokumentasjonen](https://github.com/ToreAndreRosander/heatly-cloud).