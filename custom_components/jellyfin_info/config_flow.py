"""Config flow for Jellyfin Info integration."""

import logging
from urllib.parse import urlparse

import requests
import voluptuous as vol
from homeassistant.config_entries import (ConfigEntry, ConfigFlow,
                                          ConfigFlowResult, OptionsFlow)
from homeassistant.core import callback

from .const import (CONF_AUTH_TOKEN, CONF_IGNORE_PAUSED, CONF_SERVER_URL,
                    DOMAIN, QUERY_TIMEOUT)
from .utils import get_api_url

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERVER_URL): str,
        vol.Required(CONF_AUTH_TOKEN): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IGNORE_PAUSED): bool,
    }
)


class JellyfinInfoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jellyfin Info."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input:
            server_url = user_input.get(CONF_SERVER_URL, "").strip().rstrip("/")
            auth_token = user_input.get(CONF_AUTH_TOKEN, "").strip()
            url_parsed = urlparse(server_url)

            # Validate URL format
            if not url_parsed.scheme or not url_parsed.netloc or not url_parsed.scheme in ["http", "https"]:
                errors["base"] = "invalid_url"
            # Validate auth token is not empty
            elif not auth_token:
                errors["base"] = "invalid_auth"
            # Validate connection
            elif not await self._validate_jellyfin_connection(server_url, auth_token):
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(url_parsed.netloc)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Jellyfin ({url_parsed.netloc})",
                    data={
                        CONF_SERVER_URL: server_url,
                        CONF_AUTH_TOKEN: auth_token,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Allow the integration to be reconfigured from the UI."""
        errors: dict[str, str] = {}

        entry = self._get_reconfigure_entry()

        if user_input:
            server_url = user_input.get(CONF_SERVER_URL, "").strip().rstrip("/")
            auth_token = user_input.get(CONF_AUTH_TOKEN, "").strip()
            url_parsed = urlparse(server_url)

            # Validate URL format
            if not url_parsed.scheme or not url_parsed.netloc or not url_parsed.scheme in ["http", "https"]:
                errors["base"] = "invalid_url"
            # Validate auth token is not empty
            elif not auth_token:
                errors["base"] = "invalid_auth"
            # Validate connection
            elif not await self._validate_jellyfin_connection(server_url, auth_token):
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry=entry,
                    title=f"Jellyfin ({url_parsed.netloc})",
                    data={
                        CONF_SERVER_URL: server_url,
                        CONF_AUTH_TOKEN: auth_token,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                CONFIG_SCHEMA, entry.data
            ),
            errors=errors
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        class OptionsFlowHandler(OptionsFlow):
            async def async_step_init(
                self, user_input: dict | None = None
            ) -> ConfigFlowResult:
                """Manage the options."""
                if user_input:
                    return self.async_create_entry(data=user_input)

                return self.async_show_form(
                    step_id="init",
                    data_schema=self.add_suggested_values_to_schema(
                        OPTIONS_SCHEMA, self.config_entry.options
                    ),
                )

        return OptionsFlowHandler()

    async def _validate_jellyfin_connection(
        self, server_url: str, auth_token: str
    ) -> bool:
        """Validate Jellyfin server connection."""
        try:
            @callback
            def get_version() -> bool:
                # Make sure to use an anthenticated endpoint
                response = requests.get(get_api_url(server_url, auth_token, "System/Info"), timeout=QUERY_TIMEOUT)
                response.raise_for_status()
                _LOGGER.info(f"Connected to {response.text}")
                return True
            return await self.hass.async_add_executor_job(get_version)
        except Exception as err:
            _LOGGER.error("Failed to connect to Jellyfin: %s", err)
            return False
