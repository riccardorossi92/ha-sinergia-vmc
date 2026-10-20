"""Button: sincronizzazione orologio e azzeramento ore filtri."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import SinergiaVmcConfigEntry, modbus_write_errors
from .entity import VmcEntity
from .sensor import BOARD_EPOCH

# Una scrittura alla volta sul bus seriale.
PARALLEL_UPDATES = 1


class VmcSyncClockButton(VmcEntity, ButtonEntity):
    """Scrive l'ora locale di Home Assistant nell'orologio della scheda.

    Le fasce orarie dipendono da questo orologio, che non segue da solo il
    cambio ora legale/solare.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(
            coordinator,
            "status",
            "board_clock",
            name="Sincronizza Orologio",
            unique_id_suffix="sync_clock",
        )

    async def async_press(self) -> None:
        now = dt_util.now().replace(tzinfo=None, microsecond=0)
        await self._async_write(int((now - BOARD_EPOCH).total_seconds()))


class VmcResetFilterHoursButton(VmcEntity, ButtonEntity):
    """Dopo la pulizia/sostituzione dei filtri: azzera M01 e registra PM90.

    M01 (ore ventilatore mandata) è il contatore che la scheda confronta con
    il limite M00 per l'allarme filtri; PM90 è la data di ultima manutenzione
    (manuale EVCO). L'azzeramento non è reversibile.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator) -> None:
        super().__init__(
            coordinator,
            "maintenance",
            "supply_fan_hours",
            name="Azzera Ore Filtri",
            unique_id_suffix="reset_filter_hours",
        )

    async def async_press(self) -> None:
        now = dt_util.now().replace(tzinfo=None, microsecond=0)
        maintenance = self.coordinator.device.maintenance
        async with modbus_write_errors(str(self.name)):
            await maintenance.write("supply_fan_hours", 0)
            await maintenance.write(
                "last_maintenance", int((now - BOARD_EPOCH).total_seconds())
            )
        await self.coordinator.async_refresh_after_write()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SinergiaVmcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [VmcSyncClockButton(coordinator), VmcResetFilterHoursButton(coordinator)]
    )
