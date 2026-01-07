# Heatly Cloud for Home Assistant (Alpha)
Dette er den offisielle Home Assistant-integrasjonen for Heatly. Integrasjonen bruker fysikkmodeller og alkoritmer fra Heatly Cloud for å optimalisere varmestyringen din basert på strømpris, værmelding og din boligs termiske egenskaper.

## Funksjoner
Intelligent Termostat-as-a-service: Heatly Cloud tar beslutninger, Home Assistant utfører.
Enkel Onboarding: GUI-basert oppsett uten behov for YAML-konfigurasjon.

## Installasjon
Metode 1: HACS (Anbefalt)
* Åpne HACS i din Home Assistant.
* Klikk på de tre prikkene øverst i høyre hjørne og velg Custom repositories.
* Lim inn URL-en til dette GitHub-repoet.
* Velg kategorien Integration og klikk Add.

* Finn "Heatly Cloud" i listen og klikk Download.

Restart Home Assistant.

## Oppsett (Onboarding)
Når integrasjonen er installert og HA er startet på nytt:

* Gå til Settings -> Devices & Services.
* Klikk på Add Integration nederst til høyre.
* Søk etter Heatly Cloud.

Fyll ut skjemaet:

* Room ID: Din unike ID utlevert av Heatly (f.eks. loft-pilot-02).
* Temperature Sensor: Velg din eksisterende temperatursensor i HA.
* Heater Switch: Velg bryteren, smartpluggen eller ovnen som skal styres.

Klikk Submit.

## Bruk
Integrasjonen vil nå opprette en ny termostat-enhet kalt Heatly [Ditt Rom]. Du kan legge denne til i ditt dashbord som et vanlig "Thermostat Card".
Merk: Siden dette er en AI-styrt termostat, vil den automatisk hoppe mellom "Heating" (på) og "Idle/Off" basert på instruksjoner fra Heatly Cloud.