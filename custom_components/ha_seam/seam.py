"""The Seam Integeration for Home Assistant integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import seamapi
from seamapi.types import AccessCode, Device as SeamDevice

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .lock import SeamLock

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]


class SeamManager:
    """Manages a single Seam account."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api_key: str,
        max_sensor_count: int = 3,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = entry

        self.max_sensor_count = max_sensor_count

        self.api_client = seamapi.Seam(api_key)
        self.locks: dict[str, SeamLock] = {}

    async def authenticate(self) -> bool:
        """Authenticate."""
        try:
            self.api_client.locks.list()
            return True
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Failed to authenticate: %s", exc)
            return False

    async def init_locks(self):
        """Get all locks."""
        for seam_device in await self.hass.async_add_executor_job(self.api_client.locks.list):
            if seam_device.device_type == "august_lock":
                # skip locks without a keypad
                if 'access_code' not in seam_device.capabilities_supported:
                    _LOGGER.info("Skipping lock without keypad: %s", seam_device.device_id)
                    continue

                _LOGGER.info("Found lock: %s", seam_device.device_id)
                seam_lock = SeamLock(self, seam_device)
                await seam_lock.init_sensors()
                await seam_lock.update_sensors()
                self.locks[seam_lock.unique_id] = seam_lock
            else:
                _LOGGER.info("Skipping unsupported device type: %s", seam_device.device_id)

    async def get_access_code_by_lock(self, lock: SeamDevice):
        """Get all access codes for a lock."""
        return await self.hass.async_add_executor_job(self.api_client.access_codes.list,lock)

    async def create_access_code(
        self,
        device: SeamDevice,
        code: str = "8888",
        name: str = "test",
        starts_at: str = "2023-05-01T16:00:00-0600",
        ends_at: str = "2033-12-31T11:15:00-0600",
    ) -> AccessCode:
        """Create a new access code."""
        return await self.hass.async_add_executor_job(
            self.api_client.access_codes.create,
            device,
            name,
            code,
            starts_at,
            ends_at,
        )

    async def delete_access_code(self, access_code: AccessCode) -> None:
        """Delete an access code."""
        return await self.hass.async_add_executor_job(
            self.api_client.access_codes.delete,
            access_code,
        )
