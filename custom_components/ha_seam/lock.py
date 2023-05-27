"""Support for August lock."""
import logging
from typing import Any

from seamapi.types import Device
import voluptuous as vol

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SeamManager
from .const import (
    ATTR_ACCESS_CODE,
    DOMAIN,
    SERVICE_CLEAR_LOCK_ACCESS_CODE,
    SERVICE_SET_LOCK_ACCESS_CODE,
)
from .sensor import SeamAccessCodeSensor

_LOGGER = logging.getLogger(__name__)


class SeamLock(LockEntity):
    """Representation of a Seam lock."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, seam_manager: SeamManager, device: DeviceEntry, lock: Device) -> None:
        """Initialize the lock."""
        self.seam_manager = seam_manager
        self._lock_status = None
        self._device = device
        self._seam_lock = seam_manager.device2lock[device.id]

        # device is precreated in main handler
        self._attr_device_info = DeviceInfo(
            # add identifiers to link the device to its entity
            identifiers={(DOMAIN, lock.device_id)},
        )

    @property
    def name(self) -> str:
        """Return the name of this lock."""
        return self._device.name

    async def async_set_lock_access_code(
        self,
        access_code: str,
        guest_name: str = "test",
        starts_at: str = "2023-05-01T16:00:00-0600",
        ends_at: str = "2033-12-31T11:15:00-0600",
    ) -> None:
        """Set the access_code to index X on the lock."""
        _LOGGER.error("Function triggered async_set_lock_access_code")
        seam_access_code_sensor = await SeamAccessCodeSensor.create(
            self.seam_manager,
            self,
            guest_name,
            access_code,
            starts_at,
            ends_at,
        )
        _LOGGER.error("New sensor created %s", seam_access_code_sensor)

        # platform = entity_platform.async_get_current_platform()
        # platform.async_add_entities([seam_access_code_sensor])
        # _LOGGER.error("New sensor added")

        _LOGGER.debug("User code '%s' set", access_code)

    async def async_clear_lock_access_code(self, access_code: int) -> None:
        """Clear the access_code at index X on the lock."""
        # await clear_access_code(self.info.node, code_slot)
        _LOGGER.debug("User code '%s' cleared", access_code)

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        raise NotImplementedError("This integeration does not support locking")

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        raise NotImplementedError("This integeration does not support unlocking")

    async def _call_lock_operation(self, lock_operation):
        """Call the lock operation."""
        raise NotImplementedError("This integeration does not support lock operations")

    def _update_lock_status_from_detail(self):
        """Update the lock status."""
        raise NotImplementedError("This integeration does not support lock operations")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up lock entities."""
    _LOGGER.error("async_setup_entry for lock")
    data: SeamManager = hass.data[DOMAIN][config_entry.entry_id]
    for device in data.seam2ha.values():
        _LOGGER.error("Adding lock: %s", device)
        lock = data.device2lock[device.id]
        if lock.device_type == "august_lock":
            # we can use lock.device_id as the identifier if we want to
            async_add_entities(
                [SeamLock(data, device, lock)],
                True,
            )
        else:
            _LOGGER.info("Unsupported lock type: %s", lock.device_type)
            continue

    _LOGGER.error("Register for service")
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_LOCK_ACCESS_CODE,
        {
            vol.Required(ATTR_ACCESS_CODE): cv.string,
        },
        "async_set_lock_access_code",
    )

    platform.async_register_entity_service(
        SERVICE_CLEAR_LOCK_ACCESS_CODE,
        {
            vol.Required(ATTR_ACCESS_CODE): cv.string,
        },
        "async_clear_lock_access_code",
    )
