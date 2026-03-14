"""Jellyfin client for interacting with Jellyfin API."""

from __future__ import annotations
from typing import Any

import requests
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_AUTH_TOKEN, CONF_SERVER_URL, SCAN_INTERVAL, QUERY_TIMEOUT
from .model import JellyfinData, Session
from .utils import get_api_url


_LOGGER = logging.getLogger(__name__)


class JellyfinCoordinator(DataUpdateCoordinator[JellyfinData]):
    """Client to interact with Jellyfin server and coordinate updates."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the Jellyfin coordinator."""
        self.hass = hass
        self.config_entry: ConfigEntry = config_entry
        self.server_url = config_entry.data[CONF_SERVER_URL]
        self.auth_token = config_entry.data[CONF_AUTH_TOKEN]

        # Initialize coordinator
        super().__init__(
            hass,
            _LOGGER,
            name="Jellyfin Info",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

        # Data store
        self.data = JellyfinData()

        _LOGGER.debug(f"Initialized client for {self.server_url}")

    async def _async_update_data(self) -> JellyfinData:
        """Fetch data from Jellyfin."""
        try:
            if not self.data.initialized:
                await self.hass.async_add_executor_job(self.fetch_system)

            await self.hass.async_add_executor_job(self.fetch_users)
            await self.hass.async_add_executor_job(self.fetch_sessions)

            return self.data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Jellyfin: {err}") from err
    
    def _query(self, endpoint: str) -> Any:
        url = get_api_url(self.server_url, self.auth_token, endpoint)
        response = requests.get(url=url, timeout=QUERY_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def fetch_system(self) -> None:
        """Get server system information."""
        try:
            _LOGGER.debug(f"Fetch system info for {self.server_url}")
            self.data.system = self._query("System/Info/Public")
            self.data.initialized = True
        except Exception as err:
            _LOGGER.error("Error getting system info: %s", err)
            raise

    def fetch_users(self) -> None:
        """Get users from the Jellyfin server."""
        try:
            _LOGGER.debug(f"Fetch users for {self.server_url}")
            self.data.users = self._query("Users")
            _LOGGER.debug(f"{len(self.data.users)} users found")
        except Exception as err:
            _LOGGER.error("Error getting users: %s", err)
            raise

    def fetch_sessions(self) -> None:
        """Get active sessions from the Jellyfin server."""
        try:
            _LOGGER.debug(f"Fetch sessions for {self.server_url}")
            self.data.sessions = self._query("Sessions")
            _LOGGER.debug(f"{len(self.data.sessions)} sessions found")
        except Exception as err:
            _LOGGER.error("Error getting sessions: %s", err)
            raise

    def get_playing_session(self, username: str) -> Session | None:
        """Get session for a specific user."""
        try:
            _LOGGER.debug(f"Get session for {username}")

            if not self.data.sessions:
                _LOGGER.debug("No session found")
                return None

            # Get active session
            for session in self.data.sessions:
                if (
                    session.get("UserName") == username
                    and session.get("NowPlayingItem")
                    and session.get("PlayState")
                    and session.get("PlayState").get("IsPaused") == False
                ):
                    _LOGGER.debug(f"Found playing session {session["Id"]}")
                    return session
            
            # Get paused session
            for session in self.data.sessions:
                if (
                    session.get("UserName") == username
                    and session.get("NowPlayingItem")
                ):
                    _LOGGER.debug(f"Found paused session {session["Id"]}")
                    return session
 
            _LOGGER.debug("No session found")
            return None
        except Exception as err:
            _LOGGER.error("Error getting session for user %s: %s", username, err)
            raise
