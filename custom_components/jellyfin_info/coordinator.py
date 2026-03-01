"""Jellyfin client for interacting with Jellyfin API."""

from __future__ import annotations

import logging
from datetime import timedelta

import jellyfin
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from jellyfin.generated.api_10_10.api.session_api import SessionApi
from jellyfin.generated.api_10_10.api.system_api import SystemApi
from jellyfin.generated.api_10_10.api.user_api import UserApi
from jellyfin.generated.api_10_10.models.session_info_dto import SessionInfoDto
from jellyfin.generated.api_10_10.models.system_info import SystemInfo
from jellyfin.generated.api_10_10.models.user_dto import UserDto

from .const import DOMAIN, CONF_AUTH_TOKEN, CONF_SERVER_URL, SCAN_INTERVAL


_LOGGER = logging.getLogger(DOMAIN)


class JellyfinData:
    system: SystemInfo | None = None
    users: list[UserDto]
    sessions: list[SessionInfoDto]


class JellyfinCoordinator(DataUpdateCoordinator[JellyfinData]):
    """Client to interact with Jellyfin server and coordinate updates."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the Jellyfin coordinator."""
        self.hass = hass
        self.config_entry: ConfigEntry = config_entry
        self.server_url = config_entry.data[CONF_SERVER_URL]

        # Initialize coordinator
        super().__init__(
            hass,
            _LOGGER,
            name="Jellyfin Info",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

        # Data store
        self.data = JellyfinData()

        # Initialize client
        _LOGGER.debug(f"Initialize client for {self.server_url}")
        auth_token = config_entry.data[CONF_AUTH_TOKEN]
        self.api = jellyfin.api(self.server_url, auth_token)

    async def _async_update_data(self) -> JellyfinData:
        """Fetch data from Jellyfin."""
        try:
            if not self.data.system:
                await self.hass.async_add_executor_job(self.fetch_system)

            await self.hass.async_add_executor_job(self.fetch_users)
            await self.hass.async_add_executor_job(self.fetch_sessions)

            return self.data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Jellyfin: {err}") from err

    def fetch_sessions(self) -> None:
        """Get active sessions from the Jellyfin server."""
        try:
            _LOGGER.debug(f"Fetch sessions for {self.server_url}")
            api = SessionApi(self.api.client)
            self.data.sessions = api.get_sessions()
            _LOGGER.debug(f"{len(self.data.sessions)} sessions found")
        except Exception as err:
            _LOGGER.error("Error getting sessions: %s", err)
            raise

    def fetch_system(self) -> None:
        try:
            _LOGGER.debug(f"Fetch system info for {self.server_url}")
            api = SystemApi(self.api.client)
            self.data.system = api.get_system_info()
        except Exception as err:
            _LOGGER.error("Error getting system info: %s", err)
            raise

    def fetch_users(self) -> None:
        try:
            _LOGGER.debug(f"Fetch users for {self.server_url}")
            api = UserApi(self.api.client)
            self.data.users = api.get_users()
        except Exception as err:
            _LOGGER.error("Error getting users: %s", err)
            raise

    def get_playing_session(self, username: str) -> SessionInfoDto | None:
        """Get session for a specific user."""
        try:
            _LOGGER.debug(f"Get session for {username}")

            # Get active session
            for session in self.data.sessions:
                if (
                    session.user_name == username
                    and session.now_playing_item
                    and session.play_state
                    and not session.play_state.is_paused
                ):
                    _LOGGER.debug(f"Found playing session {session.id}")
                    return session
            
            # Get paused session
            for session in self.data.sessions:
                if (
                    session.user_name == username 
                    and session.now_playing_item
                ):
                    _LOGGER.debug(f"Found paused session {session.id}")
                    return session
 
            _LOGGER.debug("No session found")
            return None
        except Exception as err:
            _LOGGER.error("Error getting session for user %s: %s", username, err)
            raise
