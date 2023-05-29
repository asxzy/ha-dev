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


# async def async_setup_platform(
#     hass: HomeAssistant, config, add_entities, discovery_info=None
# ):  # pylint: disable=unused-argument
#     """Set up this integration with config flow."""
#     return True


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

    # _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = ACCESS_CODE_ICON
    _attr_name = "Seam Access Code"

    def __init__(
        self,
        seam_manager: SeamManager,
        device: SeamLock,
        lock: SeamDevice,
        access_code_slot_idx: int,
        guest_name: str = None,
        access_code: str = None,
        starts_at: str = None,
        ends_at: str = None,
        access_code_id: str = None,
    ) -> None:
        """Initialize the sensor."""
        self._seam_manager = seam_manager
        self._device = device
        self._lock = lock
        self._guest_name = guest_name
        self._access_code = access_code
        self._access_code_slot_idx = access_code_slot_idx
        self._starts_at = starts_at
        self._ends_at = ends_at
        self._access_code_id = access_code_id

        # HA attributes
        self._entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f"{self._device.unique_id}_slot_{self._access_code_slot_idx+1}"
        self._attr_icon = ACCESS_CODE_ICON

    @property
    def device_info(self):
        """Return the device info block."""
        return self._device.device_info

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"seam_access_code_{self._device.name}_{self._access_code_slot_idx+1}_{self._guest_name}_{self._access_code}"
        # return f"seam_access_code_{self._device.name}_{self._access_code_slot_idx+1}"
        # return f"access_code_{device.name}_slot_{self._access_code_slot_idx+1}"

    @property
    def guest_name(self):
        """Return the name of the sensor."""
        return self._guest_name

    @property
    def access_code(self):
        """Return True if calendar is ready."""
        return self._access_code

    @property
    def starts_at(self):
        """Return the start of the event."""
        return self._starts_at

    @property
    def ends_at(self):
        """Return the end of the event."""
        return self._ends_at

    @property
    def access_code_id(self):
        """Return the unique_id."""
        return self._access_code_id

    @property
    def access_code_slot_idx(self):
        """Return the unique_id."""
        return self._access_code_slot_idx

    @property
    def is_on(self):
        """Return True if calendar is ready."""
        return self._access_code is not None

    async def create_code(
        self,
        access_code,
        guest_name,
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
            name=guest_name,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Failed to create code: %s", exc)
            return

        _LOGGER.info("Created code: %s", seam_access_code)
        self._guest_name = seam_access_code.name
        self._access_code = seam_access_code.code
        self._starts_at = seam_access_code.starts_at
        self._ends_at = seam_access_code.ends_at
        self._access_code_id = seam_access_code.access_code_id


    def update_sensor(
        self,
        idx: int,
        access_code: SeamAccessCode = None,
    ) -> None:
        """Update the sensor."""
        _LOGGER.info("Updating code: %s", access_code)
        self._access_code_slot_idx = idx
        if access_code is not None:
            self._guest_name = access_code.name
            self._access_code = access_code.code
            self._starts_at = access_code.starts_at
            self._ends_at = access_code.ends_at
            self._access_code_id = access_code.access_code_id
