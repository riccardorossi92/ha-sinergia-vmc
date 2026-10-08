# Sinergia VMC (Modbus) per Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Validate](https://github.com/riccardorossi92/ha-sinergia-vmc/actions/workflows/validate.yml/badge.svg)](https://github.com/riccardorossi92/ha-sinergia-vmc/actions/workflows/validate.yml)

Integrazione custom di Home Assistant per le unità VMC **Sinergia** con
elettronica **CPRO3OEM-K** (HRD/HRD+), controllate via **Modbus RTU** su
RS-485 — tramite adattatore USB-RS485 diretto oppure gateway RS485↔Ethernet
(Modbus TCP).

Testata su un'unità **HRD H** (versione D, compressore on/off) con elettronica
**CPRO3OEM-K**, commercializzata come Sinergia / innova. La gamma HRD H esiste
nelle taglie 30/15 e 50/25 e nelle versioni D (deumidifica isotermica) e DC
(integrazione caldo/freddo, compressore inverter).

Usa la connessione Modbus condivisa fornita dall'integrazione core `modbus`
di Home Assistant.

## Funzionalità

- **Sensori**: sonde temperatura/umidità, uscite ventilatori/compressore/serranda,
  stato unità, ore di funzionamento
- **Sensori binari**: allarmi e ingressi/uscite digitali
- **Switch**: accensione, modalità estate/inverno, abilitazioni BMS
- **Number**: setpoint e velocità ventilatori
- **Fasce orarie**: fascia attiva (Comfort/Economy/Night/OFF), abilitazione
  della programmazione, setpoint Comfort, offset Economy/Night e velocità
  ventilatori per fascia, programma settimanale
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

## Installazione

### HACS (consigliato)

1. HACS → menu ⋮ → **Repository personalizzati**
2. URL: `https://github.com/riccardorossi92/ha-sinergia-vmc`, categoria **Integrazione**
3. Cerca "Sinergia VMC (Modbus)" e installa
4. Riavvia Home Assistant

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
comando a muro EVJD920N2VW (la "tastiera locale" del parametro H01). Si trova in
[`vmc_modbus_device/device.py`](custom_components/sinergia_vmc/vmc_modbus_device/device.py),
che è la versione aggiornata della mappa dei registri (la libreria separata
[sinergia-vmc-modbus](https://github.com/riccardorossi92/sinergia-vmc-modbus)
è archiviata e non più mantenuta).

**Indirizzamento registri.** Il manuale elenca "Addr HEX" e "Addr DEC" per ogni
registro, ma `Addr DEC = Addr HEX convertito + 1` in tutti i gruppi tranne
"COMANDI TEST" (dove sembrano coincidere, probabile refuso). Gli indirizzi
usati qui sono quelli reali da chiamare via Modbus (`Addr HEX` / `Addr DEC - 1`),
verificati incrociando 12+ registri con una scansione RS-485 reale della stessa VMC.

**Fasce orarie.** I registri della programmazione a fasce non sono documentati
da Sinergia: sono stati ricavati incrociando una scansione completa dei
registri con il manuale EVCO *c-pro 3 OEM DE* (l'ordine dei parametri coincide
con quello dei registri). La scansione si può rifare con
[`tools/modbus_scan.py`](tools/modbus_scan.py) (gateway Modbus TCP, sola lettura).

Registri volutamente esclusi (da aggiungere dopo verifica sul campo):
gruppo "COMANDI TEST" (PT01-PT11).

## Licenza

[MIT](LICENSE)
