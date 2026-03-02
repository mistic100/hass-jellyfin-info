"""Config flow for Jellyfin Info integration."""

import logging
import requests
from urllib.parse import urlparse
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import CONF_AUTH_TOKEN, CONF_SERVER_URL, DOMAIN, QUERY_TIMEOUT
from .utils import get_api_url


_LOGGER = logging.getLogger(DOMAIN)


def _base_schema():
    return vol.Schema(
        {
            vol.Required(CONF_SERVER_URL): str,
            vol.Required(CONF_AUTH_TOKEN): str,
        }
    )


def _reconfigure_schema(entry: ConfigEntry):
    return vol.Schema(
        {
            vol.Required(
                CONF_SERVER_URL,
                default=entry.data.get(CONF_SERVER_URL, ""),
            ): str,
            vol.Required(
                CONF_AUTH_TOKEN,
                default=entry.data.get(CONF_AUTH_TOKEN, ""),
            ): str,
        }
    )


class JellyfinInfoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jellyfin Info."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
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
            step_id="user", data_schema=_base_schema(), errors=errors
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
            step_id="reconfigure", data_schema=_reconfigure_schema(entry), errors=errors
        )

    async def _validate_jellyfin_connection(self, server_url: str, auth_token: str) -> bool:
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
