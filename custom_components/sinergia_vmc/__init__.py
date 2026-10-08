"""Integrazione Home Assistant per unità VMC Sinergia (elettronica CPRO3OEM-K) via Modbus RTU.

Usa la connessione Modbus condivisa fornita dall'integrazione core
``modbus`` (``async_get_unit``), come le integrazioni device-specific
"moderne" (``sofar``, ``flexit``) - non apre una porta seriale propria.
"""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import (
    CONF_DEVICE,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TYPE,
    Platform,
)
from homeassistant.core import HomeAssistant
from modbus_connection import ModbusSerialParams, ModbusTcpParams

from .const import (
    CONF_BAUDRATE,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_UNIT,
    DEFAULT_SCAN_INTERVAL,
    TYPE_SERIAL,
)
from .coordinator import SinergiaVmcConfigEntry, VmcCoordinator

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]


def create_modbus_params(data: dict) -> ModbusSerialParams | ModbusTcpParams:
    """Costruisce i parametri di connessione Modbus dall'entry.

    Seriale (USB-RS485 diretto) o TCP (gateway RS485<->Ethernet, es.
    Waveshare RS485 TO ETH in modalità "Modbus TCP to RTU" - il caso più
    comune: con quella modalità attiva il master Modbus TCP, qui
    Home Assistant, non parla mai direttamente la seriale).
    """
    if data[CONF_TYPE] == TYPE_SERIAL:
        return ModbusSerialParams(
            device=data[CONF_DEVICE],
            baudrate=data[CONF_BAUDRATE],
            bytesize=8,
            parity=data[CONF_PARITY],
            stopbits=data[CONF_STOPBITS],
        )
    return ModbusTcpParams(host=data[CONF_HOST], port=data[CONF_PORT])


async def async_setup_entry(hass: HomeAssistant, entry: SinergiaVmcConfigEntry) -> bool:
    """Ottiene una unit sulla connessione Modbus condivisa e avvia il coordinator."""
    unit = async_get_unit(
        hass, entry, create_modbus_params(entry.data), entry.data[CONF_UNIT]
    )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = VmcCoordinator(hass, entry, unit, timedelta(seconds=scan_interval))

    # Se la connessione/lettura fallisce qui, HA la converte automaticamente
    # in ConfigEntryNotReady e ritenta più tardi.
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: SinergiaVmcConfigEntry
) -> None:
    """Ricarica l'entry quando cambiano le opzioni (es. intervallo di polling)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SinergiaVmcConfigEntry) -> bool:
    """Scarica l'entry. La connessione condivisa si chiude da sola quando
    l'ultimo consumatore la rilascia (gestito da ``async_get_unit``)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
