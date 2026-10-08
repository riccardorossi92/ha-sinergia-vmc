"""Action (servizi) dell'integrazione: modifica della programmazione a fasce."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import SinergiaVmcConfigEntry
from .vmc_modbus_device.device import (
    TIME_BAND_DAYS,
    TIME_BANDS_PER_DAY,
    TimeBandCode,
    time_band,
)

SERVICE_SET_TIME_BAND = "set_time_band"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_DAYS = "days"
ATTR_BAND = "band"
ATTR_START = "start"
ATTR_MODE = "mode"

MODES = {
    "disabled": TimeBandCode.DISABLED,
    "off": TimeBandCode.OFF,
    "comfort": TimeBandCode.COMFORT,
    "economy": TimeBandCode.ECONOMY,
    "night": TimeBandCode.NIGHT,
}

SET_TIME_BAND_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
            vol.Required(ATTR_DAYS): vol.All(
                cv.ensure_list, vol.Length(min=1), [vol.In(TIME_BAND_DAYS)]
            ),
            vol.Required(ATTR_BAND): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=TIME_BANDS_PER_DAY)
            ),
            vol.Optional(ATTR_START): cv.time,
            vol.Optional(ATTR_MODE): vol.In(MODES),
        }
    ),
    cv.has_at_least_one_key(ATTR_START, ATTR_MODE),
)


def _get_entry(hass: HomeAssistant, call: ServiceCall) -> SinergiaVmcConfigEntry:
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
        entries = [entry for entry in entries if entry.entry_id == entry_id]
    if len(entries) != 1:
        raise ServiceValidationError(
            "Specifica la VMC con config_entry_id (nessuna o più di una VMC caricata)"
        )
    return entries[0]


def _format(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"


async def _async_set_time_band(hass: HomeAssistant, call: ServiceCall) -> None:
    entry = _get_entry(hass, call)
    coordinator = entry.runtime_data
    bands = coordinator.device.time_bands
    index: int = call.data[ATTR_BAND]
    start = call.data.get(ATTR_START)
    new_start = start.hour * 3600 + start.minute * 60 + start.second if start else None
    new_mode = MODES[call.data[ATTR_MODE]] if ATTR_MODE in call.data else None

    # Validazione di tutti i giorni prima di scrivere qualsiasi registro.
    for day in call.data[ATTR_DAYS]:
        schedule = [time_band(bands, day, i) for i in range(1, TIME_BANDS_PER_DAY + 1)]
        if any(kind is None or secs is None for kind, secs in schedule):
            raise HomeAssistantError("Programma fasce non ancora letto dalla VMC, riprova")
        kind, secs = schedule[index - 1]
        schedule[index - 1] = (
            new_mode if new_mode is not None else kind,
            new_start if new_start is not None else secs,
        )
        # Le fasce attive di un giorno devono avere orari crescenti.
        active = [secs for kind, secs in schedule if kind != TimeBandCode.DISABLED]
        if any(a >= b for a, b in zip(active, active[1:])):
            raise ServiceValidationError(
                f"{day}: gli orari delle fasce attive devono essere crescenti "
                f"(risultato: {', '.join(_format(s) for s in active)})"
            )

    for day in call.data[ATTR_DAYS]:
        if new_mode is not None:
            await bands.write(f"{day}_{index}_type", int(new_mode))
        if new_start is not None:
            await bands.write(f"{day}_{index}_start", new_start)

    await coordinator.async_request_refresh()


def async_setup_services(hass: HomeAssistant) -> None:
    """Registra le action dell'integrazione."""

    async def handle_set_time_band(call: ServiceCall) -> None:
        await _async_set_time_band(hass, call)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_TIME_BAND, handle_set_time_band, schema=SET_TIME_BAND_SCHEMA
    )
