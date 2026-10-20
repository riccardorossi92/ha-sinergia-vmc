"""DataUpdateCoordinator per l'unità VMC Sinergia.

Segue il pattern delle integrazioni Modbus "moderne" (vedi ``sofar`` e
``flexit`` in home-assistant/core, e
https://developers.home-assistant.io/blog/2026/07/05/modernizing-modbus/):
la connessione seriale è condivisa tramite ``homeassistant.components.modbus``
(vedi ``__init__.py``), non aperta privatamente da questa integrazione.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusError, ModbusUnit
from sinergia_vmc_modbus import VmcDevice

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type SinergiaVmcConfigEntry = ConfigEntry[VmcCoordinator]

# Valori che cambiano da soli: letti a ogni ciclo.
LIVE_COMPONENTS: tuple[str, ...] = ("probes", "outputs", "alarms", "digital_io", "status")
# Parametri che cambiano solo se modificati (da HA o dal pannello): sul bus
# RS-485 a 9600 baud sono ~20 delle 27 richieste di un ciclo completo, quindi
# si rileggono di rado e subito dopo ogni scrittura da Home Assistant.
CONFIG_COMPONENTS: tuple[str, ...] = tuple(
    name for name in VmcDevice.COMPONENT_NAMES if name not in LIVE_COMPONENTS
)
CONFIG_POLL_INTERVAL = 300  # secondi


@asynccontextmanager
async def modbus_write_errors(target: str) -> AsyncIterator[None]:
    """Trasforma un errore Modbus in scrittura in un errore leggibile in HA."""
    try:
        yield
    except ModbusError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="write_failed",
            translation_placeholders={"target": target, "error": str(err)},
        ) from err


class VmcCoordinator(DataUpdateCoordinator[None]):
    """Interroga periodicamente tutti i componenti del device VMC."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SinergiaVmcConfigEntry,
        unit: ModbusUnit,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Sinergia VMC",
            config_entry=entry,
            update_interval=update_interval,
            # Il device library mantiene i valori decodificati al suo interno;
            # non c'è uno stato "coordinator.data" da confrontare.
            always_update=True,
        )
        self.device = VmcDevice(unit)
        self._config_polled_at: float | None = None
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Sinergia VMC",
            manufacturer="Sinergia",
            model="CPRO3OEM-K / HRD-HRD+",
        )

    async def async_refresh_after_write(self) -> None:
        """Rilegge tutto (parametri compresi) dopo una scrittura da HA."""
        self._config_polled_at = None
        await self.async_request_refresh()

    @override
    async def _async_update_data(self) -> None:
        now = time.monotonic()
        poll_config = (
            self._config_polled_at is None
            or now - self._config_polled_at >= CONFIG_POLL_INTERVAL
        )
        names = LIVE_COMPONENTS + CONFIG_COMPONENTS if poll_config else LIVE_COMPONENTS
        try:
            report = await self.device.async_poll(names)
        except ModbusError as err:
            # Connessione persa o nessuna risposta: HA riprova al prossimo
            # ciclo e, se accade durante il primo refresh, async_config_entry
            # _first_refresh() lo trasforma automaticamente in
            # ConfigEntryNotReady.
            raise UpdateFailed(f"Errore Modbus: {err}") from err

        if poll_config:
            self._config_polled_at = now

        if report.failed:
            # Alcuni gruppi possono non rispondere (es. sonde sul pannello
            # remoto se non presente/abilitato): non blocchiamo l'intera
            # integrazione, segnaliamo solo nei log.
            for name, err in report.failed.items():
                _LOGGER.debug("Gruppo '%s' non aggiornato: %s", name, err)
