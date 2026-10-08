"""DataUpdateCoordinator per l'unità VMC Sinergia.

Segue il pattern delle integrazioni Modbus "moderne" (vedi ``sofar`` e
``flexit`` in home-assistant/core, e
https://developers.home-assistant.io/blog/2026/07/05/modernizing-modbus/):
la connessione seriale è condivisa tramite ``homeassistant.components.modbus``
(vedi ``__init__.py``), non aperta privatamente da questa integrazione.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusError, ModbusUnit

from .const import DOMAIN
from .vmc_modbus_device.device import VmcDevice

_LOGGER = logging.getLogger(__name__)

type SinergiaVmcConfigEntry = ConfigEntry[VmcCoordinator]


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
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Sinergia VMC",
            manufacturer="Sinergia",
            model="CPRO3OEM-K / HRD-HRD+",
        )

    @override
    async def _async_update_data(self) -> None:
        try:
            report = await self.device.async_poll(self.device.COMPONENT_NAMES)
        except ModbusError as err:
            # Connessione persa o nessuna risposta: HA riprova al prossimo
            # ciclo e, se accade durante il primo refresh, async_config_entry
            # _first_refresh() lo trasforma automaticamente in
            # ConfigEntryNotReady.
            raise UpdateFailed(f"Errore Modbus: {err}") from err

        if report.failed:
            # Alcuni gruppi possono non rispondere (es. sonde sul pannello
            # remoto se non presente/abilitato): non blocchiamo l'intera
            # integrazione, segnaliamo solo nei log.
            for name, err in report.failed.items():
                _LOGGER.debug("Gruppo '%s' non aggiornato: %s", name, err)
