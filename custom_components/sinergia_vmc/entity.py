"""Entità base condivisa: legge/scrive un attributo di un componente del device."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import VmcCoordinator


class VmcEntity(CoordinatorEntity[VmcCoordinator]):
    """Entità che legge (e opzionalmente scrive) un campo di un componente."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VmcCoordinator,
        component: str,
        attr: str,
        *,
        name: str,
        unique_id_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._component_name = component
        self._attr_name_key = attr
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{unique_id_suffix}"
        self._attr_device_info = coordinator.device_info

    @property
    def _component(self):
        return getattr(self.coordinator.device, self._component_name)

    @property
    def _raw_value(self):
        return getattr(self._component, self._attr_name_key)

    async def _async_write(self, value) -> None:
        await self._component.write(self._attr_name_key, value)
        await self.coordinator.async_request_refresh()
