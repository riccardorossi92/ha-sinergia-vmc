"""Costanti per l'integrazione Sinergia VMC (Modbus)."""

from __future__ import annotations

DOMAIN = "sinergia_vmc"

CONF_BAUDRATE = "baudrate"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"
CONF_UNIT = "unit"

# Tipo di connessione: seriale diretta (USB-RS485) o TCP (gateway
# RS485<->Ethernet tipo Waveshare RS485 TO ETH, in modalita' "Modbus TCP to
# RTU"). homeassistant.const.CONF_TYPE viene riusato come chiave.
TYPE_TCP = "tcp"
TYPE_SERIAL = "serial"

# Impostazioni seriali di fabbrica dichiarate dal manuale Sinergia
# ("Manuale di collegamento e impostazioni MODBUS HRD/HRD+", cap. 2.1.1.3),
# confermate anche lato gateway Waveshare (baud 9600, 8 data bit, parita'
# None, 1 stop bit nella sezione Serial del tool di configurazione):
# NOTA: la tabella parametri H11-H14 dello stesso manuale Sinergia riporta
# invece un default "Pari" per la parità (H13) - le due sezioni sono in
# contraddizione, ma il riscontro pratico sul gateway conferma "None".
DEFAULT_BAUDRATE = 9600
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1
DEFAULT_UNIT = 1
DEFAULT_SCAN_INTERVAL = 30  # secondi

# Porta Modbus TCP standard. Molti gateway (es. Waveshare RS485 TO ETH)
# passano automaticamente a questa porta quando si attiva la modalità
# "Modbus TCP to RTU" - verifica quella effettivamente attiva sul tuo
# dispositivo dopo averla salvata.
DEFAULT_TCP_PORT = 502

PARITY_OPTIONS = ["N", "E", "O"]
