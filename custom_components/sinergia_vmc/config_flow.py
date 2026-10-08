"""Config flow per l'integrazione Sinergia VMC (Modbus)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import (
    CONF_DEVICE,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SerialPortSelector,
    TextSelector,
)
from modbus_connection import ModbusError

from . import create_modbus_params
from .const import (
    CONF_BAUDRATE,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_UNIT,
    DEFAULT_BAUDRATE,
    DEFAULT_PARITY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STOPBITS,
    DEFAULT_TCP_PORT,
    DEFAULT_UNIT,
    DOMAIN,
    PARITY_OPTIONS,
    TYPE_SERIAL,
    TYPE_TCP,
)
from .vmc_modbus_device.device import VmcDevice

_LOGGER = logging.getLogger(__name__)

BAUDRATE_OPTIONS = ["1200", "2400", "4800", "9600", "19200", "28800", "38400", "57600"]

UNIT_SELECTOR = vol.All(
    NumberSelector(NumberSelectorConfig(min=1, max=247, mode=NumberSelectorMode.BOX)),
    vol.Coerce(int),
)

# Gateway RS485<->Ethernet (es. Waveshare RS485 TO ETH in modalità
# "Modbus TCP to RTU", porta tipicamente 502 una volta attivata quella
# modalità - verifica quella effettivamente in uso sul tuo gateway).
STEP_TCP_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(),
        vol.Required(CONF_PORT, default=DEFAULT_TCP_PORT): vol.All(
            NumberSelector(
                NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
            ),
            vol.Coerce(int),
        ),
        vol.Required(CONF_UNIT, default=DEFAULT_UNIT): UNIT_SELECTOR,
    }
)

# Adattatore USB-RS485 collegato direttamente all'host Home Assistant.
STEP_SERIAL_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE): SerialPortSelector(),
        vol.Required(CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)): vol.All(
            SelectSelector(SelectSelectorConfig(options=BAUDRATE_OPTIONS)),
            vol.Coerce(int),
        ),
        vol.Required(CONF_PARITY, default=DEFAULT_PARITY): SelectSelector(
            SelectSelectorConfig(options=PARITY_OPTIONS)
        ),
        vol.Required(CONF_STOPBITS, default=DEFAULT_STOPBITS): vol.All(
            NumberSelector(NumberSelectorConfig(min=1, max=2, mode=NumberSelectorMode.BOX)),
            vol.Coerce(int),
        ),
        vol.Required(CONF_UNIT, default=DEFAULT_UNIT): UNIT_SELECTOR,
    }
)


async def check_connection(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Apre una unit temporanea e prova a leggere lo stato dell'unità.

    Ritorna una chiave di errore (per strings.json), o None se ok.
    """
    try:
        async with async_get_temporary_unit(
            hass, create_modbus_params(data), data[CONF_UNIT]
        ) as unit:
            device = VmcDevice(unit)
            # sm_UnitStatus (1104) e' il registro piu' "universale": presente
            # anche senza pannello remoto collegato.
            await device.status.async_update()
    except (HomeAssistantError, ModbusError):
        _LOGGER.debug("Impossibile connettersi alla VMC Sinergia", exc_info=True)
        return "cannot_connect"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Errore imprevisto durante il test connessione")
        return "unknown"
    return None


def _title(data: dict[str, Any]) -> str:
    if data[CONF_TYPE] == TYPE_TCP:
        return f"Sinergia VMC ({data[CONF_HOST]})"
    return f"Sinergia VMC ({data[CONF_DEVICE]})"


class SinergiaVmcConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow per Sinergia VMC: scelta tra connessione TCP o seriale."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Primo passo: TCP (gateway RS485<->Ethernet) o seriale (USB-RS485)."""
        return self.async_show_menu(step_id="user", menu_options=["tcp", "serial"])

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Connessione tramite gateway Modbus TCP (es. Waveshare RS485 TO ETH)."""
        return await self._async_step_connection(
            TYPE_TCP, STEP_TCP_DATA_SCHEMA, user_input
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Connessione tramite adattatore USB-RS485 diretto."""
        return await self._async_step_connection(
            TYPE_SERIAL, STEP_SERIAL_DATA_SCHEMA, user_input
        )

    async def _async_step_connection(
        self,
        connection_type: str,
        schema: vol.Schema,
        user_input: dict[str, Any] | None,
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {CONF_TYPE: connection_type, **user_input}
            self._async_abort_entries_match(data)
            error = await check_connection(self.hass, data)
            if error is not None:
                errors["base"] = error
            else:
                unique_key = (
                    f"{data[CONF_HOST]}:{data[CONF_PORT]}:{data[CONF_UNIT]}"
                    if connection_type == TYPE_TCP
                    else f"{data[CONF_DEVICE]}:{data[CONF_UNIT]}"
                )
                await self.async_set_unique_id(unique_key)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=_title(data), data=data)

        return self.async_show_form(
            step_id=connection_type, data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return SinergiaVmcOptionsFlow()


class SinergiaVmcOptionsFlow(OptionsFlow):
    """Permette di cambiare l'intervallo di aggiornamento a runtime."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): NumberSelector(
                        NumberSelectorConfig(
                            min=5, max=300, step=5, unit_of_measurement="s"
                        )
                    ),
                }
            ),
        )
