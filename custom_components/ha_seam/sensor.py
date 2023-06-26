"""Creating sensors for upcoming events."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from seamapi.types import AccessCode as SeamAccessCode, Device as SeamDevice

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ACCESS_CODE_ICON, DOMAIN

if TYPE_CHECKING:
    from .lock import SeamLock
    from .seam import SeamManager


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up SeamAccessCode sensors."""
    _LOGGER.info("Setting up sensors")
    seam_manager: SeamManager = hass.data[DOMAIN][config_entry.entry_id]
    sensors = []
    for lock in seam_manager.locks.values():
        await lock.update_sensors()
        sensors.extend(lock.access_code_sensors)

    _LOGGER.info("Adding %s sensors", len(sensors))
    async_add_entities(sensors)


class SeamAccessCodeSensor(BinarySensorEntity):
    """Implementation of a seam code."""

    _attr_icon = ACCESS_CODE_ICON

    def __init__(
        self,
        seam_manager: SeamManager,
        device: SeamLock,
        lock: SeamDevice,
        access_code_slot_idx: int,
        slot_name: str = None,
        access_code: str = None,
        starts_at: str = None,
        ends_at: str = None,
        access_code_id: str = None,
    ) -> None:
        """Initialize the sensor."""
        self._seam_manager = seam_manager
        self._device = device
        self._lock = lock
        self.slot_name = slot_name
        self.access_code = access_code
        self.access_code_slot_idx = access_code_slot_idx
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.access_code_id = access_code_id

        # HA attributes
        self._entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f"{self._device.unique_id}_slot_{self.access_code_slot_idx+1}"
        self._attr_icon = ACCESS_CODE_ICON

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Seam Access Code - {self._device.name} - {self.access_code_slot_idx+1}"

    @property
    def extra_state_attributes(self):
        """Return the access code sensors as extra state attributes."""
        return {
            "access_code": self.access_code,
            "slot_name": self.slot_name,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "access_code_id": self.access_code_id,
            "access_code_slot_idx": self.access_code_slot_idx,
        }

    @property
    def device_info(self):
        """Return the device info block."""
        return self._device.device_info

    @property
    def is_on(self):
        """Return True if calendar is ready."""
        return self.access_code is not None

    async def create_code(
        self,
        access_code,
        slot_name,
        starts_at,
        ends_at,
    ) -> None:
        """Create a new sensor."""
        _LOGGER.info("Creating code: %s", access_code)
        # lock = seam_manager.device2lock[device.device_id]
        try:
            seam_access_code: SeamAccessCode = await self._seam_manager.create_access_code(
                device=self._device.seam_device,
                code=access_code,
                name=slot_name,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Failed to create code: %s", exc)
            return

        _LOGGER.info("Created code: %s", seam_access_code)
        self.slot_name = seam_access_code.name
        self.access_code = seam_access_code.code
        self.starts_at = seam_access_code.starts_at
        self.ends_at = seam_access_code.ends_at
        self.access_code_id = seam_access_code.access_code_id

    def update_sensor(
        self,
        idx: int,
        access_code: SeamAccessCode = None,
    ) -> None:
        """Update the sensor."""
        _LOGGER.info("Updating code: %s", access_code)
        self.access_code_slot_idx = idx
        if access_code is not None:
            self.slot_name = access_code.name
            self.access_code = access_code.code
            self.starts_at = access_code.starts_at
            self.ends_at = access_code.ends_at
            self.access_code_id = access_code.access_code_id
