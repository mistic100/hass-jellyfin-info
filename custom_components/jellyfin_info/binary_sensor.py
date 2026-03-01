"""Binary sensor platform for Jellyfin Info."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_platform as ep

from .coordinator import JellyfinCoordinator
from .const import ATTR_MEDIA_NAME, ATTR_MEDIA_TYPE, DOMAIN


_LOGGER = logging.getLogger(DOMAIN)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    _async_add_entities: AddEntitiesCallback,
) -> None:
    """Add and remove entities."""
    platform = ep.async_get_current_platform()
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    @callback
    async def async_update_entities() -> None:
        """Update entities when coordinator data is updated."""

        if not coordinator.data.users:
            return

        usernames = {str(user.name) for user in coordinator.data.users}

        if usernames:
            new_entities = [
                JellyfinSessionBinarySensor(coordinator, username)
                for username in usernames
            ]
            await platform.async_add_entities(new_entities)
            _LOGGER.debug(f"Created entities for users: {usernames}")

    await async_update_entities()

    unsub = async_dispatcher_connect(hass, "update_sensors", async_update_entities)
    config_entry.async_on_unload(unsub)


class JellyfinSessionBinarySensor(CoordinatorEntity[JellyfinCoordinator], BinarySensorEntity):
    """Jellyfin session binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JellyfinCoordinator,
        username: str
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)

        _LOGGER.debug(f"Initialize session sensor for {username}")

        self.username = username

    @property
    def name(self) -> str:
        return self.username
    
    @property
    def unique_id(self) -> str | None:
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_{self.username}_session"

    @property
    def device_info(self) -> DeviceInfo:
        manufacturer: str | None = None
        sw_version: str | None = None

        if self.coordinator.data.system:
            manufacturer = self.coordinator.data.system.product_name
            sw_version = self.coordinator.data.system.version

        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.config_entry.entry_id}_session")},
            name="Jellyfin Sessions",
            manufacturer=manufacturer,
            sw_version=sw_version,
            
        )

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        try:
            session = self.coordinator.get_playing_session(self.username)
            return True if session else False
        except Exception:
            return False
        
    @property
    def icon(self) -> str | None:
        try:
            session = self.coordinator.get_playing_session(self.username)

            if session and session.now_playing_item:
                match session.now_playing_item.type:
                    case "Audio":
                        return "mdi:music"
                    case "Episode":
                        return "mdi:television-classic"
                    case "Movie":
                        return "mdi:filmstrip"
                    case _:
                        return "mdi:play"
            else:
                return "mdi:stop"
        except Exception:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        try:
            session = self.coordinator.get_playing_session(self.username)
            attributes = {}

            if session and session.now_playing_item:
                item = session.now_playing_item

                attributes[ATTR_MEDIA_TYPE] = item.type

                match item.type:
                    case "Audio":
                        attributes[ATTR_MEDIA_NAME] = f"{item.album_artist} - {item.album}"
                    case "Episode":
                        attributes[ATTR_MEDIA_NAME] = f"{item.series_name} - {item.season_name}"
                    case _:
                        attributes[ATTR_MEDIA_NAME] = item.name
            
            return attributes
        except Exception:
            return {}
