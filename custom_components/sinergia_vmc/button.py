"""Button: sincronizzazione dell'orologio della scheda con Home Assistant."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import SinergiaVmcConfigEntry
from .entity import VmcEntity
from .sensor import BOARD_EPOCH


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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SinergiaVmcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([VmcSyncClockButton(coordinator)])
