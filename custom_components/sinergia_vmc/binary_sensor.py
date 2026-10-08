"""Binary sensor: allarme cumulativo e richieste attive della macchina."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SinergiaVmcConfigEntry
from .entity import VmcEntity


@dataclass(frozen=True, kw_only=True)
class VmcBinarySensorSpec:
    component: str
    attr: str
    name: str
    unique_id_suffix: str
    device_class: BinarySensorDeviceClass | None = None


BINARY_SENSORS: tuple[VmcBinarySensorSpec, ...] = (
    VmcBinarySensorSpec(
        component="alarms", attr="active", name="Allarme Attivo",
        unique_id_suffix="alarm_active", device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    # Richieste elaborate dalla macchina (sonde/DI/BMS), indipendenti dagli
    # switch "Richiesta ..." che scrivono solo il comando da BMS.
    VmcBinarySensorSpec(
        component="status", attr="dehum_request", name="Deumidifica Richiesta",
        unique_id_suffix="status_dehum_request", device_class=BinarySensorDeviceClass.RUNNING,
    ),
    VmcBinarySensorSpec(
        component="status", attr="freecooling_heating_request",
        name="Free-Cooling/Heating Richiesto",
        unique_id_suffix="status_freecooling_heating_request",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
)


class VmcBinarySensor(VmcEntity, BinarySensorEntity):
    """Binary sensor generico basato su VmcBinarySensorSpec."""

    def __init__(self, coordinator, spec: VmcBinarySensorSpec) -> None:
        super().__init__(
            coordinator,
            spec.component,
            spec.attr,
            name=spec.name,
            unique_id_suffix=spec.unique_id_suffix,
        )
        self._attr_device_class = spec.device_class

    @property
    def is_on(self) -> bool | None:
        return self._raw_value


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SinergiaVmcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(VmcBinarySensor(coordinator, spec) for spec in BINARY_SENSORS)
