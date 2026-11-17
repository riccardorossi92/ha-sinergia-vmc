# Sinergia VMC (Modbus) per Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://hacs.xyz)
[![Validate](https://github.com/riccardorossi92/ha-sinergia-vmc/actions/workflows/validate.yml/badge.svg)](https://github.com/riccardorossi92/ha-sinergia-vmc/actions/workflows/validate.yml)

Integrazione custom di Home Assistant per le unità VMC **Sinergia** con
elettronica **CPRO3OEM-K** (HRD/HRD+), controllate via **Modbus RTU** su
RS-485 — tramite adattatore USB-RS485 diretto oppure gateway RS485↔Ethernet
(Modbus TCP).

Testata su un'unità **HRD 30/15 H K DC** (taglia 30/15, orizzontale, elettronica
**CPRO3OEM-K**, versione DC deumidifica + integrazione caldo/freddo con
compressore on/off R134A), prodotta da Sinergia e commercializzata come
Termomarket / innova. Attenzione: nelle unità più recenti (manuale innova 2026)
la versione DC ha invece compressore inverter, con sonda di evaporazione e
uscita compressore modulante (registri 511 e 641), assenti sulla versione on/off.

Usa la connessione Modbus condivisa fornita dall'integrazione core `modbus`
di Home Assistant.

## Funzionalità

- **Sensori**: sonde temperatura/umidità, uscite ventilatori/compressore/serranda,
  stato unità, ore di funzionamento
- **Sensori binari**: allarmi e ingressi/uscite digitali
- **Switch**: accensione, modalità estate/inverno, abilitazioni BMS
- **Number**: setpoint e velocità ventilatori (anche in regolazione manuale)
- **Fasce orarie**: fascia attiva (Comfort/Economy/Night/OFF), abilitazione
  della programmazione, setpoint Comfort, offset Economy/Night e velocità
  ventilatori per fascia, programma settimanale
- **Manutenzione filtri**: pulsante *Azzera Ore Filtri* (azzera il contatore
  M01 usato per l'allarme filtri e registra la data in *Ultima Manutenzione
  (PM90)*)
- **Calibrazione sonde**: offset di temperatura ambiente (M80), umidità
  ambiente (M86), temperatura esterna/acqua/espulsione (M81-M83)
- **Action `sinergia_vmc.set_time_band`**: modifica orario di inizio e/o
  modalità di una fascia (1-4) per uno o più giorni

## Modificare le fasce orarie

Esempio (Strumenti per sviluppatori → Azioni, modalità YAML): fascia Comfort
dalle 09:30 dal lunedì al venerdì.

```yaml
action: sinergia_vmc.set_time_band
data:
  days: [mon, tue, wed, thu, fri]
  band: 2
  start: "09:30:00"
  mode: comfort
```

Gli orari delle fasce attive di un giorno devono restare crescenti: se la
modifica li renderebbe disordinati l'action viene rifiutata senza scrivere
nulla. Per togliere una fascia usa `mode: disabled`.

## Velocità in regolazione manuale

Con le fasce orarie disattivate (switch *Fasce Orarie Abilitate (PH03)*
spento, icona della mano sul pannello) i ventilatori girano alle velocità
manuali:

- **Velocità Mandata Manuale** (sensore): si imposta solo dal pannello a muro.
  Il pannello la tiene nella sua memoria e la riscrive di continuo sulla
  scheda, quindi una scrittura via Modbus verrebbe annullata subito.
- **Velocità Ripresa Manuale** (number): si imposta dal pannello o da Home
  Assistant.

La freccia del pannello aggiunge o toglie **5 punti a entrambe**, ognuna
fermandosi ai propri limiti: mandata tra **F07 e F08**, ripresa tra **F29 e
F30** (sulla macchina di test 15-100% e 40-75%). Non esiste un parametro
"scarto": la differenza tra le due cambia solo quando una delle due è ferma a
un limite. Esempio con mandata 15% e ripresa 40%:

| Pressioni ▲ | Mandata | Ripresa | Note |
|---|---|---|---|
| 0 | 15% | 40% | scarto 25 |
| 7 | 50% | 75% | la ripresa arriva al massimo F30 |
| 12 | 75% | 75% | sale solo la mandata: ora sono pari |
| oltre | 80%… | 75% | la ripresa resta ferma, lo scarto si ricrea |

Mandata e ripresa restano quindi uguali solo tra 40% e 75%; sotto il 40% la
ripresa si ferma al minimo mentre la mandata continua a scendere. Per
scegliere lo scarto senza arrivare ai limiti: imposta la mandata con la
freccia del pannello e poi la ripresa da Home Assistant (*Velocità Ripresa
Manuale*, valori ammessi da F29 a F30).

## Installazione

### HACS (consigliato)

L'integrazione è nel catalogo predefinito di HACS.

[![Apri in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=riccardorossi92&repository=ha-sinergia-vmc&category=integration)

1. In HACS cerca **"Sinergia VMC (Modbus)"** (oppure usa il pulsante qui sopra)
2. Premi **Scarica**
3. Riavvia Home Assistant

Richiede Home Assistant **2026.9.0** o successivo.

Se non la trovi nella ricerca (ad esempio con una versione di HACS non
aggiornata), puoi aggiungerla come repository personalizzato: HACS → menu ⋮ →
**Repository personalizzati** → URL
`https://github.com/riccardorossi92/ha-sinergia-vmc`, categoria
**Integrazione**.

### Manuale

Copia la cartella `custom_components/sinergia_vmc` in
`<config>/custom_components/` e riavvia Home Assistant.

## Configurazione

Impostazioni → Dispositivi e servizi → **Aggiungi integrazione** →
"Sinergia VMC (Modbus)", poi scegli:

- **Gateway di rete** (es. Waveshare RS485 TO ETH in modalità "Modbus TCP to RTU", porta 502)
- **Adattatore USB-RS485** diretto

## Collegamento fisico

RS-485 (A+/B-/GND) sui morsetti dedicati della scheda. Impostazioni seriali
di fabbrica: **9600 baud, 8 bit, parità nessuna, 1 stop bit, indirizzo 1**.

Il manuale Sinergia dichiara parità "nessuna", ma la tabella parametri H11-H14
dello stesso documento riporta un default "parità Pari" per H13: le due
sezioni sono in contraddizione. Se la connessione non risponde, riprova con
parità **Even**.

> ⚠️ Le abilitazioni H02/H27/H28 (controllo da BMS/Modbus) devono essere attive,
> altrimenti la macchina ignora le scritture sui registri corrispondenti.

## Note tecniche

La mappa dei registri si basa sul documento ufficiale *"Manuale di
collegamento e impostazioni MODBUS HRD/HRD+"* (Sinergia, r.03_10-2023) ed è
verificata sul campo su un'unità con elettronica CPRO3OEM-K e pannello di
comando a muro EVJD920N2VW (la "tastiera locale" del parametro H01). Si trova nella libreria Python
[sinergia-vmc-modbus](https://github.com/riccardorossi92/sinergia-vmc-modbus),
pubblicata su [PyPI](https://pypi.org/project/sinergia-vmc-modbus/): Home
Assistant la installa automaticamente con l'integrazione, ed è utilizzabile
anche senza Home Assistant (`pip install sinergia-vmc-modbus`).

**Indirizzamento registri.** Il manuale elenca "Addr HEX" e "Addr DEC" per ogni
registro, ma `Addr DEC = Addr HEX convertito + 1` in tutti i gruppi tranne
"COMANDI TEST" (dove sembrano coincidere, probabile refuso). Gli indirizzi
usati qui sono quelli reali da chiamare via Modbus (`Addr HEX` / `Addr DEC - 1`),
verificati incrociando 12+ registri con una scansione RS-485 reale della stessa VMC.
Vale anche per le richieste da BMS: integrazione `0x0473` = **1139** e
deumidifica `0x0474` = **1140** (non 1140/1141 come in "Addr DEC"). Dalla 0.9.4
la scrittura sul 1140 è verificata sul campo: la scheda tiene la richiesta.
In inverno non la esegue se la deumidifica invernale è disabilitata (PU02, di
fabbrica 0); l'esecuzione in estate è ancora da verificare. Sulla 1141 la scrittura falliva con *Modbus Exception 0x02*.

**PA58 (tempo massimo warning alta umidità).** Il manuale non ne indica l'unità:
è in **minuti**, verificato sul campo con PA58 = 90. Il primo AL01 (warning alta
umidità, soglia A19) è scattato alle 18:02 e AL02 (allarme, riarmo manuale) alle
19:31, esattamente 90 minuti dopo. Il conteggio non si è azzerato quando AL01 è
rientrato per pochi minuti.

**Fasce orarie.** I registri della programmazione a fasce non sono documentati
da Sinergia: sono stati ricavati incrociando una scansione completa dei
registri con il manuale EVCO *c-pro 3 OEM DE* (l'ordine dei parametri coincide
con quello dei registri). La scansione si può rifare con
[`tools/modbus_scan.py`](tools/modbus_scan.py) (gateway Modbus TCP, sola lettura).

Registri volutamente esclusi (da aggiungere dopo verifica sul campo):
gruppo "COMANDI TEST" (PT01-PT11).

## Stato verifica registri non documentati

Registri ricavati da scansione e non presenti nel manuale Sinergia. Se hai la
stessa macchina e puoi confermarne (o smentirne) uno, apri una
[issue](https://github.com/riccardorossi92/ha-sinergia-vmc/issues).

| Registri | Contenuto | Lettura | Scrittura |
|---|---|---|---|
| 1499-1582 | Programma fasce orarie (tipo + orario) | ✅ coincide con il pannello | ✅ action `set_time_band`, anche orari serali (dalla 0.7.1) |
| 1106 | Fascia oraria attiva | ✅ segue i cambi di fascia (Comfort→Economy→Night→Economy) | — |
| 1779 | PH03 - fasce orarie abilitate | ✅ | ✅ il pannello passa da icona orologio (fasce) a mano (manuale) |
| 1587-1592 | Setpoint Comfort, offset Economy/Night | ✅ coincidono con il pannello | ✅ ogni registro scritto (±0,5 °C), riletto via Modbus e ripristinato |
| 1595-1597 | Velocità mandata per fascia (FSC/FSE/FSN) | ✅ coincidono con il pannello | ✅ FSE/FSN portati a 70% da HA, riletti 7000 via Modbus |
| 1859-1861 | Velocità ripresa per fascia (FRC/FRE/FRN) | ✅ FrC modificato dal pannello, letto da HA | ✅ FrC modificato da HA, aggiornato sul pannello |
| 1614, 1858 | Velocità mandata/ripresa in regolazione manuale (fasce orarie disattivate) | ✅ cambiate dal pannello con la freccia (+5 punti a entrambe, 15→50% e 40→75%), seguite dalle uscite 639/640; il confronto completo prima/dopo non mostra altri registri di impostazione (solo le copie di stato 1114/1136) | ✅ ripresa (1858): 40% e 50% scritti via Modbus, tenuti e seguiti dall'uscita 640; ❌ mandata (1614): la comanda il pannello a muro, che sovrascrive le scritture Modbus → in Home Assistant è un sensore |
| 1616-1619, 1622 | Calibrazione sonde (M80-M83, M86) | ✅ verificato modificando M80/M86 dal pannello | ✅ M80/M86 azzerati da HA, aggiornati sul pannello |
| 1101-1102 | Orologio della scheda | ✅ | ✅ (Sincronizza Orologio) |
| 1694 | PU07 - Differenziale umidità (deumidifica da PU01 + PU07 a PU01) | ✅ vale 10 (default EVCO) | ✅ portato a 5 con umidità 60% e setpoint 55%: la deumidifica parte subito |
| 1602-1613 | Contatori ore, limiti, ultima manutenzione (PM90) | ✅ valori plausibili | ✅ limiti M00/M03 scritti (+10 h), riletti e ripristinati; M01 azzerato e data PM90 registrata, riletti via Modbus |

## Licenza

[MIT](LICENSE)
