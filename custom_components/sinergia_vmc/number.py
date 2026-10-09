"""Number: setpoint e velocità ventilatori scrivibili."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SinergiaVmcConfigEntry
from .entity import VmcEntity


@dataclass(frozen=True, kw_only=True)
class VmcNumberSpec:
    component: str
    attr: str
    name: str
    unique_id_suffix: str
    unit: str | None
    min_value: float
    max_value: float
    step: float
    diagnostic: bool = False


NUMBERS: tuple[VmcNumberSpec, ...] = (
    VmcNumberSpec(
        component="setpoints", attr="summer", name="Setpoint Estivo",
        unique_id_suffix="setpoint_summer", unit="°C",
        min_value=-15, max_value=158, step=0.5,
    ),
    VmcNumberSpec(
        component="setpoints", attr="winter", name="Setpoint Invernale",
        unique_id_suffix="setpoint_winter", unit="°C",
        min_value=-15, max_value=158, step=0.5,
    ),
    VmcNumberSpec(
        component="setpoints", attr="humidity", name="Setpoint Umidità",
        unique_id_suffix="setpoint_humidity", unit="%",
        min_value=0, max_value=100, step=1,
    ),
    VmcNumberSpec(
        component="setpoints", attr="freecooling_heating",
        name="Setpoint Free-Cooling/Heating",
        unique_id_suffix="setpoint_freecooling_heating", unit="°C",
        min_value=0, max_value=68, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="setpoints", attr="freecooling_heating_diff",
        name="Differenziale Free-Cooling/Heating",
        unique_id_suffix="setpoint_freecooling_heating_diff", unit="°C",
        min_value=0, max_value=36, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="setpoints", attr="high_humidity_warning",
        name="Setpoint Warning Alta Umidità (A19)",
        unique_id_suffix="setpoint_high_humidity_warning", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="setpoints", attr="summer_commutation_water",
        name="Commutazione Estate Temp. Acqua (C07)",
        unique_id_suffix="setpoint_summer_commutation_water", unit="°C",
        min_value=0, max_value=158, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="setpoints", attr="winter_commutation_water",
        name="Commutazione Inverno Temp. Acqua (C08)",
        unique_id_suffix="setpoint_winter_commutation_water", unit="°C",
        min_value=0, max_value=158, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="setpoints", attr="max_time_dehum_by_di_warning",
        name="PA58 - Tempo Max Deumidifica da DI (warning)",
        unique_id_suffix="pa58_max_time_dehum", unit="min",
        min_value=0, max_value=999, step=1, diagnostic=True,
    ),
    # --- Velocità ventilatori ---
    VmcNumberSpec(
        component="fan_speeds", attr="min_supply_vmc_mode",
        name="Velocità Min. Mandata - Modo VMC (F07)",
        unique_id_suffix="fan_min_supply_vmc", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="fan_speeds", attr="max_supply_vmc_mode",
        name="Velocità Max. Mandata - Modo VMC (F08)",
        unique_id_suffix="fan_max_supply_vmc", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="fan_speeds", attr="min_supply_integration",
        name="Velocità Min. Mandata - Integrazione (F27)",
        unique_id_suffix="fan_min_supply_integ", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="fan_speeds", attr="max_supply_integration",
        name="Velocità Max. Mandata - Integrazione (F09)",
        unique_id_suffix="fan_max_supply_integ", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="fan_speeds", attr="min_supply_dehum",
        name="Velocità Min. Mandata - Deumidifica (F28)",
        unique_id_suffix="fan_min_supply_dehum", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="fan_speeds", attr="max_supply_dehum",
        name="Velocità Max. Mandata - Deumidifica (F10)",
        unique_id_suffix="fan_max_supply_dehum", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="fan_speeds", attr="min_return",
        name="Velocità Min. Ripresa (F29)",
        unique_id_suffix="fan_min_return", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="fan_speeds", attr="max_return",
        name="Velocità Max. Ripresa (F30)",
        unique_id_suffix="fan_max_return", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    # --- Fasce orarie ---
    VmcNumberSpec(
        component="time_band_setpoints", attr="comfort_summer",
        name="Setpoint Estivo Comfort (SCC)",
        unique_id_suffix="tb_comfort_summer", unit="°C",
        min_value=-15, max_value=158, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="comfort_winter",
        name="Setpoint Invernale Comfort (SCH)",
        unique_id_suffix="tb_comfort_winter", unit="°C",
        min_value=-15, max_value=158, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="economy_offset_summer",
        name="Offset Estivo Economy (OEC)",
        unique_id_suffix="tb_economy_offset_summer", unit="°C",
        min_value=-20, max_value=20, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="economy_offset_winter",
        name="Offset Invernale Economy (OEH)",
        unique_id_suffix="tb_economy_offset_winter", unit="°C",
        min_value=-20, max_value=20, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="night_offset_summer",
        name="Offset Estivo Night (ONC)",
        unique_id_suffix="tb_night_offset_summer", unit="°C",
        min_value=-20, max_value=20, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="night_offset_winter",
        name="Offset Invernale Night (ONH)",
        unique_id_suffix="tb_night_offset_winter", unit="°C",
        min_value=-20, max_value=20, step=0.5, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="supply_fan_comfort",
        name="Velocità Mandata Comfort (FSC)",
        unique_id_suffix="tb_supply_fan_comfort", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="supply_fan_economy",
        name="Velocità Mandata Economy (FSE)",
        unique_id_suffix="tb_supply_fan_economy", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="supply_fan_night",
        name="Velocità Mandata Night (FSN)",
        unique_id_suffix="tb_supply_fan_night", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="return_fan_comfort",
        name="Velocità Ripresa Comfort (FRC)",
        unique_id_suffix="tb_return_fan_comfort", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="return_fan_economy",
        name="Velocità Ripresa Economy (FRE)",
        unique_id_suffix="tb_return_fan_economy", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="time_band_setpoints", attr="return_fan_night",
        name="Velocità Ripresa Night (FRN)",
        unique_id_suffix="tb_return_fan_night", unit="%",
        min_value=0, max_value=100, step=1, diagnostic=True,
    ),
    # --- Calibrazione sonde ---
    VmcNumberSpec(
        component="calibrations", attr="room_temperature",
        name="Calibrazione Temperatura Ambiente (M80)",
        unique_id_suffix="cal_room_temperature", unit="°C",
        min_value=-10, max_value=10, step=0.1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="calibrations", attr="room_humidity",
        name="Calibrazione Umidità Ambiente (M86)",
        unique_id_suffix="cal_room_humidity", unit="%",
        min_value=-10, max_value=10, step=1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="calibrations", attr="outdoor_temperature",
        name="Calibrazione Temperatura Esterna (M81)",
        unique_id_suffix="cal_outdoor_temperature", unit="°C",
        min_value=-10, max_value=10, step=0.1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="calibrations", attr="water_temperature",
        name="Calibrazione Temperatura Acqua (M82)",
        unique_id_suffix="cal_water_temperature", unit="°C",
        min_value=-10, max_value=10, step=0.1, diagnostic=True,
    ),
    VmcNumberSpec(
        component="calibrations", attr="exhaust_temperature",
        name="Calibrazione Temperatura Espulsione (M83)",
        unique_id_suffix="cal_exhaust_temperature", unit="°C",
        min_value=-10, max_value=10, step=0.1, diagnostic=True,
    ),
    # --- Manutenzione ---
    VmcNumberSpec(
        component="command", attr="fans_hours_limit",
        name="Limite Ore Ventilatori (M00, allarme filtri)",
        unique_id_suffix="fans_hours_limit", unit="h",
        min_value=0, max_value=99990, step=10, diagnostic=True,
    ),
    VmcNumberSpec(
        component="maintenance", attr="compressor_hours_limit",
        name="Limite Ore Compressore (M03)",
        unique_id_suffix="compressor_hours_limit", unit="h",
        min_value=0, max_value=99990, step=10, diagnostic=True,
    ),
)


class VmcNumber(VmcEntity, NumberEntity):
    """Number generico basato su VmcNumberSpec."""

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, spec: VmcNumberSpec) -> None:
        super().__init__(
            coordinator,
            spec.component,
            spec.attr,
            name=spec.name,
            unique_id_suffix=spec.unique_id_suffix,
        )
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_native_min_value = spec.min_value
        self._attr_native_max_value = spec.max_value
        self._attr_native_step = spec.step
        if spec.diagnostic:
            self._attr_entity_category = EntityCategory.CONFIG

    @property
    def native_value(self) -> float | None:
        return self._raw_value

    async def async_set_native_value(self, value: float) -> None:
        await self._async_write(value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SinergiaVmcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(VmcNumber(coordinator, spec) for spec in NUMBERS)
