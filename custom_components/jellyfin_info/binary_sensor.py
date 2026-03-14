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
from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    _async_add_entities: AddEntitiesCallback,
) -> None:
    """Add and remove entities."""
    platform = ep.async_get_current_platform()
    coordinator: JellyfinCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    @callback
    async def async_update_entities() -> None:
        """Update entities when coordinator data is updated."""

        if coordinator.data.users:
            new_entities = [
                JellyfinSessionBinarySensor(coordinator, user["Name"])
                for user in coordinator.data.users
            ]
            await platform.async_add_entities(new_entities)
            _LOGGER.debug(f"Created entities for {len(new_entities)} users")

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
        sw_version: str | None = None

        if self.coordinator.data.system:
            sw_version = self.coordinator.data.system.get("Version")

        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.config_entry.entry_id}_session")},
            name="Jellyfin Sessions",
            manufacturer="Jellyfin Server",
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

            if session:
                match session.get("NowPlayingItem").get("Type"):
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

    def _get_image_url(self, item_id: str, variant: str = "Primary") -> str:
        url: str
        if self.coordinator.data.system.get("LocalAddress"):
            url = f"https://{self.coordinator.data.system.get("LocalAddress")}"
        else:
            url = self.coordinator.server_url
        return url + f"/Items/{item_id}/Images/{variant}?fillHeight=600&fillWidth=600&quality=95"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        try:
            session = self.coordinator.get_playing_session(self.username)
            attributes = {}

            if session:
                item = session.get("NowPlayingItem")

                attributes["type"] = item.get("Type")
                attributes["name"] = item.get("Name")

                match item.get("Type"):
                    case "Audio":
                        attributes["parent_name"] = f"{item.get("AlbumArtist")} - {item.get("Album")}"
                        attributes["cover_url"] = self._get_image_url(item.get("AlbumId"))
                    case "Episode":
                        attributes["parent_name"] = f"{item.get("SeriesName")} - {item.get("SeasonName")}"
                        attributes["cover_url"] = self._get_image_url(item.get("SeasonId"))
                    case "Movie":
                        attributes["cover_url"] = self._get_image_url(item.get("Id"))
            
            return attributes
        except Exception:
            return {}
