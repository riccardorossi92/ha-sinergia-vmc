"""Switch: abilitazioni obbligatorie, comandi on/off, reset allarmi."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SinergiaVmcConfigEntry
from .entity import VmcEntity


@dataclass(frozen=True, kw_only=True)
class VmcSwitchSpec:
    component: str
    attr: str
    name: str
    unique_id_suffix: str
    diagnostic: bool = False
    enabled_default: bool = True
    momentary: bool = False  # scrive True e poi si "riporta" da solo sul device


SWITCHES: tuple[VmcSwitchSpec, ...] = (
    # *** Abilitazioni obbligatorie (H02/H27/H28) - vedi note nel device library:
    # senza queste il dispositivo IGNORA le scritture sui comandi corrispondenti.
    VmcSwitchSpec(
        component="enables", attr="onoff_by_bms",
        name="Abilita On/Off da BMS (H02) [OBBLIGATORIO]",
        unique_id_suffix="enable_onoff_by_bms", diagnostic=True,
    ),
    VmcSwitchSpec(
        component="enables", attr="integ_by_bms",
        name="Abilita Integrazione da BMS (H27) [OBBLIGATORIO]",
        unique_id_suffix="enable_integ_by_bms", diagnostic=True,
    ),
    VmcSwitchSpec(
        component="enables", attr="dehum_by_bms",
        name="Abilita Deumidifica da BMS (H28) [OBBLIGATORIO]",
        unique_id_suffix="enable_dehum_by_bms", diagnostic=True,
    ),
    VmcSwitchSpec(
        component="enables", attr="onoff_by_keyboard",
        name="Abilita On/Off da Tastiera Locale (H01)",
        unique_id_suffix="enable_onoff_by_keyboard", diagnostic=True,
    ),
    VmcSwitchSpec(
        component="enables", attr="time_bands_enabled",
        name="Fasce Orarie Abilitate (PH03)",
        unique_id_suffix="enable_time_bands",
    ),
    # Comandi
    VmcSwitchSpec(
        component="command", attr="onoff_by_supervisor",
        name="Accensione", unique_id_suffix="onoff_by_supervisor",
    ),
    VmcSwitchSpec(
        component="command", attr="integ_request_by_bms",
        name="Richiesta Integrazione", unique_id_suffix="integ_request_by_bms",
    ),
    VmcSwitchSpec(
        component="command", attr="dehum_request_by_bms",
        name="Richiesta Deumidifica", unique_id_suffix="dehum_request_by_bms",
    ),
    VmcSwitchSpec(
        component="command", attr="summer_winter_mode",
        name="Modalità Inverno (off=Estate)", unique_id_suffix="summer_winter_mode",
    ),
    VmcSwitchSpec(
        component="command", attr="priority_display_mode",
        name="Priorità Cambio Modalità a Ingresso Digitale (C11)",
        unique_id_suffix="priority_display_mode", diagnostic=True,
        enabled_default=False,
    ),
    VmcSwitchSpec(
        component="command", attr="reset_alarm_al02",
        name="Reset Allarme AL02 (alta umidità)",
        unique_id_suffix="reset_alarm_al02", diagnostic=True, momentary=True,
    ),
    VmcSwitchSpec(
        component="command", attr="reset_alarm_al12",
        name="Reset Allarme AL12 (alta pressione compressore)",
        unique_id_suffix="reset_alarm_al12", diagnostic=True, momentary=True,
    ),
)


class VmcSwitch(VmcEntity, SwitchEntity):
    """Switch generico basato su VmcSwitchSpec."""

    def __init__(self, coordinator, spec: VmcSwitchSpec) -> None:
        super().__init__(
            coordinator,
            spec.component,
            spec.attr,
            name=spec.name,
            unique_id_suffix=spec.unique_id_suffix,
        )
        self._spec = spec
        self._attr_entity_registry_enabled_default = spec.enabled_default
        if spec.diagnostic:
            self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool | None:
        return self._raw_value

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_write(True)
        if self._spec.momentary:
            # Registro a impulso: il dispositivo lo azzera da solo dopo il
            # reset. Rileggiamo a breve per riflettere lo stato reale.
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_write(False)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SinergiaVmcConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(VmcSwitch(coordinator, spec) for spec in SWITCHES)
