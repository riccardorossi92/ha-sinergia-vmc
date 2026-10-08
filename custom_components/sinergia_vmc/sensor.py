"""Sensori (sole letture) per Sinergia VMC."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SinergiaVmcConfigEntry
from .entity import VmcEntity
from .vmc_modbus_device.device import (
    TIME_BAND_DAYS,
    TIME_BANDS_PER_DAY,
    TimeBandCode,
    time_band,
)

# La scheda segnala una sonda assente/guasta con valori sentinella
# 0x80xx (es. 0x8004 = -32764 -> -3276.4 °C dopo la scala 0.1).
PROBE_ERROR_THRESHOLD = -3000.0


@dataclass(frozen=True, kw_only=True)
class VmcSensorSpec:
    component: str
    attr: str
    name: str
    unique_id_suffix: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    entity_category: str | None = None
    enum_valued: bool = False
    enabled_default: bool = True
    enum_type: type[IntEnum] | None = None  # converte un intero grezzo in nome enum


SENSORS: tuple[VmcSensorSpec, ...] = (
    # --- Sonde ---
    VmcSensorSpec(
        component="probes", attr="temp_return_room", name="Temperatura Ambiente/Ripresa",
        unique_id_suffix="temp_return_room", unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT,
    ),
    VmcSensorSpec(
        component="probes", attr="temp_outdoor", name="Temperatura Esterna",
        unique_id_suffix="temp_outdoor", unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT,
    ),
    VmcSensorSpec(
        component="probes", attr="temp_water", name="Temperatura Acqua",
        unique_id_suffix="temp_water", unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT,
    ),
    VmcSensorSpec(
        component="probes", attr="temp_exhaust", name="Temperatura Espulsione",
        unique_id_suffix="temp_exhaust", unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT,
    ),
    VmcSensorSpec(
        component="probes", attr="temp_free_cooling", name="Temperatura Free-Cooling",
        unique_id_suffix="temp_free_cooling", unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT,
    ),
    VmcSensorSpec(
        component="probes", attr="temp_evaporation", name="Temperatura Evaporazione (Inverter)",
        unique_id_suffix="temp_evaporation", unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT,
        enabled_default=False,  # solo versione Inverter
    ),
    VmcSensorSpec(
        component="probes", attr="humidity_return_room", name="Umidità Ambiente/Ripresa",
        unique_id_suffix="humidity_return_room", unit="%",
        device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT,
    ),
    # --- Uscite analogiche ---
    VmcSensorSpec(
        component="outputs", attr="supply_fan_pct", name="Velocità Ventilatore Mandata",
        unique_id_suffix="supply_fan_pct", unit="%", state_class=SensorStateClass.MEASUREMENT,
    ),
    VmcSensorSpec(
        component="outputs", attr="return_fan_pct", name="Velocità Ventilatore Ripresa",
        unique_id_suffix="return_fan_pct", unit="%", state_class=SensorStateClass.MEASUREMENT,
    ),
    VmcSensorSpec(
        component="outputs", attr="compressor_pct", name="Compressore % (Inverter)",
        unique_id_suffix="compressor_pct", unit="%", state_class=SensorStateClass.MEASUREMENT,
        enabled_default=False,  # solo versione Inverter
    ),
    VmcSensorSpec(
        component="outputs", attr="external_damper_pct", name="Serranda Esterna %",
        unique_id_suffix="external_damper_pct", unit="%", state_class=SensorStateClass.MEASUREMENT,
    ),
    # --- Stato unità ---
    VmcSensorSpec(
        component="status", attr="unit_status", name="Stato Unità",
        unique_id_suffix="unit_status", enum_valued=True,
    ),
    VmcSensorSpec(
        component="status", attr="mode_status", name="Modalità Operativa",
        unique_id_suffix="mode_status", enum_valued=True,
    ),
    VmcSensorSpec(
        component="status", attr="actual_setpoint", name="Setpoint Attuale Ambiente",
        unique_id_suffix="actual_setpoint", unit="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    VmcSensorSpec(
        component="status", attr="supply_fan_status", name="Stato Ventilatore Mandata",
        unique_id_suffix="supply_fan_status", enum_valued=True,
    ),
    VmcSensorSpec(
        component="status", attr="return_fan_status", name="Stato Ventilatore Ripresa",
        unique_id_suffix="return_fan_status", enum_valued=True,
    ),
    VmcSensorSpec(
        component="status", attr="compressor_status", name="Stato Compressore",
        unique_id_suffix="compressor_status", enum_valued=True,
    ),
    VmcSensorSpec(
        component="status", attr="external_damper_modulating_pct",
        name="Serranda Esterna Modulante %",
        unique_id_suffix="external_damper_modulating_pct", unit="%",
    ),
    VmcSensorSpec(
        component="status", attr="external_damper_status", name="Stato Serranda Esterna",
        unique_id_suffix="external_damper_status", enum_valued=True,
    ),
    VmcSensorSpec(
        component="status", attr="recirc_damper_status", name="Stato Serranda Ricircolo",
        unique_id_suffix="recirc_damper_status", enum_valued=True,
    ),
    # --- Fasce orarie ---
    VmcSensorSpec(
        component="status", attr="active_time_band", name="Fascia Oraria Attiva",
        unique_id_suffix="active_time_band", enum_type=TimeBandCode,
    ),
    # --- Manutenzione ---
    VmcSensorSpec(
        component="maintenance", attr="supply_fan_hours", name="Ore Ventilatore Mandata",
        unique_id_suffix="supply_fan_hours", unit="h",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # --- Allarmi (bitmask grezze, utili per template/diagnostica) ---
    VmcSensorSpec(
        component="alarms", attr="packed_1", name="Allarmi Bitmask 1 (AL01-AL16)",
        unique_id_suffix="alarms_packed_1", entity_category="diagnostic",
    ),
    VmcSensorSpec(
        component="alarms", attr="packed_2", name="Allarmi Bitmask 2 (AL17-AL32)",
        unique_id_suffix="alarms_packed_2", entity_category="diagnostic",
    ),
    VmcSensorSpec(
        component="alarms", attr="packed_3", name="Allarmi Bitmask 3 (AL33-AL39)",
        unique_id_suffix="alarms_packed_3", entity_category="diagnostic",
    ),
)


class VmcSensor(VmcEntity, SensorEntity):
    """Sensore generico basato su VmcSensorSpec."""

    def __init__(self, coordinator, spec: VmcSensorSpec) -> None:
        super().__init__(
            coordinator,
            spec.component,
            spec.attr,
            name=spec.name,
            unique_id_suffix=spec.unique_id_suffix,
        )
        self._spec = spec
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_device_class = spec.device_class
        self._attr_state_class = spec.state_class
        self._attr_entity_registry_enabled_default = spec.enabled_default
        if spec.entity_category:
            self._attr_entity_category = EntityCategory(spec.entity_category)

    @property
    def native_value(self):
        value = self._raw_value
        if value is None:
            return None
        if self._spec.enum_valued and isinstance(value, IntEnum):
            return value.name
        if self._spec.enum_type is not None:
            try:
                return self._spec.enum_type(value).name
            except ValueError:
                return None
        if (
            self._spec.device_class == SensorDeviceClass.TEMPERATURE
            and value <= PROBE_ERROR_THRESHOLD
        ):
            return None
        return value


DAY_NAMES = {
    "mon": "Lunedì", "tue": "Martedì", "wed": "Mercoledì", "thu": "Giovedì",
    "fri": "Venerdì", "sat": "Sabato", "sun": "Domenica",
}
BAND_NAMES = {
    TimeBandCode.OFF: "OFF", TimeBandCode.COMFORT: "Comfort",
    TimeBandCode.ECONOMY: "Economy", TimeBandCode.NIGHT: "Night",
}


class VmcScheduleDaySensor(VmcEntity, SensorEntity):
    """Programma a fasce di un giorno, es. "07:00 Economy, 10:00 Comfort"."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, day: str) -> None:
        super().__init__(
            coordinator,
            "time_bands",
            f"{day}_1_type",
            name=f"Programma {DAY_NAMES[day]}",
            unique_id_suffix=f"schedule_{day}",
        )
        self._day = day

    def _bands(self) -> list[tuple[str, str]] | None:
        bands = []
        for index in range(1, TIME_BANDS_PER_DAY + 1):
            kind, seconds = time_band(self._component, self._day, index)
            if kind is None or seconds is None:
                return None
            if kind == TimeBandCode.DISABLED or kind not in BAND_NAMES:
                continue
            start = f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"
            bands.append((start, BAND_NAMES[TimeBandCode(kind)]))
        return bands

    @property
    def native_value(self) -> str | None:
        bands = self._bands()
        if bands is None:
            return None
        return ", ".join(f"{start} {name}" for start, name in bands) or "Nessuna fascia"

    @property
    def extra_state_attributes(self) -> dict | None:
        bands = self._bands()
        if bands is None:
            return None
        return {"fasce": [{"inizio": start, "fascia": name} for start, name in bands]}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SinergiaVmcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(VmcSensor(coordinator, spec) for spec in SENSORS)
    async_add_entities(VmcScheduleDaySensor(coordinator, day) for day in TIME_BAND_DAYS)
