"""Support for August lock."""
import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from dateutil import parser as dt_parser
from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from seamapi.types import Device as SeamDevice

from .const import (
    ATTR_ACCESS_CODE,
    ATTR_ENDS_AT,
    ATTR_RESERVATION_CODE,
    ATTR_STARTS_AT,
    DOMAIN,
    LOCK_ICON,
    SERVICE_SET_LOCK_ACCESS_CODE,
    SERVICE_SYNC_LOCK_ACCESS_CODE,
    SERVICE_UPDATE_LOCK_ACCESS_CODE,
)
from .sensor import SeamAccessCodeSensor
from .utils import normalize_name

if TYPE_CHECKING:
    from .seam import SeamManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up lock entities."""
    _LOGGER.info("Initializing lock entities")
    seam_manager: "SeamManager" = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(lock for lock in seam_manager.locks.values())

    _LOGGER.info("Register for service")
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_LOCK_ACCESS_CODE,
        {
            vol.Required(ATTR_ACCESS_CODE): cv.string,
            vol.Required(ATTR_RESERVATION_CODE): cv.string,
            vol.Required(ATTR_STARTS_AT): cv.string,
            vol.Required(ATTR_ENDS_AT): cv.string,
        },
        "async_set_lock_access_code",
    )

    platform.async_register_entity_service(
        SERVICE_SYNC_LOCK_ACCESS_CODE,
        {},
        "async_sync_lock_access_code",
    )

    platform.async_register_entity_service(
        SERVICE_UPDATE_LOCK_ACCESS_CODE,
        {
            vol.Required(ATTR_ACCESS_CODE): cv.string,
            vol.Required(ATTR_RESERVATION_CODE): cv.string,
            vol.Required(ATTR_STARTS_AT): cv.string,
            vol.Required(ATTR_ENDS_AT): cv.string,
        },
        "async_update_lock_access_code",
    )


class SeamLock(LockEntity):
    """Representation of a Seam lock."""

    _attr_should_poll = False

    def __init__(self, seam_manager: "SeamManager", seam_device: SeamDevice) -> None:
        """Initialize the lock."""
        self.seam_manager = seam_manager
        self.seam_device = seam_device

        self._lock_status = None

        # device is precreated in main handler
        self._attr_device_info = DeviceInfo(
            # add identifiers to link the device to its entity
            identifiers={(DOMAIN, self.seam_device.device_id)}
        )
        self._attr_unique_id = self.seam_device.device_id
        self._attr_icon = LOCK_ICON

        self.access_code_sensors: "SeamAccessCodeSensor" = []

    @property
    def name(self) -> str:
        """Return the name of the lock."""
        return f"Seam Lock - {normalize_name(self.seam_device.properties.name)}"

    @property
    def extra_state_attributes(self):
        """Return the access code sensors as extra state attributes."""
        return {"access_code_sensors": [normalize_name(x.name) for x in self.access_code_sensors]}

    async def init_sensors(self):
        """Initialize the sensors."""
        _LOGGER.info("Initializing %s sensors", self.seam_manager.max_sensor_count)
        self.access_code_sensors = [
            SeamAccessCodeSensor(
                seam_manager=self.seam_manager,
                device=self,
                lock=self.seam_device,
                access_code_slot_idx=x,
                reservation_code=None,
                access_code=None,
                starts_at=None,
                ends_at=None,
                access_code_id=None,
                status=None,
            )
            for x in range(self.seam_manager.max_sensor_count)
        ]

    async def update_sensors(self):
        """Update the sensors."""
        access_codes = await self.seam_manager.get_access_code_by_lock(self.seam_device)
        access_codes.sort(key=lambda x: x.starts_at)
        _LOGGER.info('='*20)
        _LOGGER.info(access_codes)
        for idx in range(self.seam_manager.max_sensor_count):
            if idx < len(access_codes):
                self.access_code_sensors[idx].update_sensor(idx, access_codes[idx])
            else:
                self.access_code_sensors[idx].update_sensor(idx, None)

    async def update_access_code(
        self,
    ):
        """Update the sensors."""
        access_codes = await self.seam_manager.get_access_code_by_lock(self.seam_device)
        access_codes.sort(key=lambda x: x.starts_at)
        for idx in range(self.seam_manager.max_sensor_count):
            if idx < len(access_codes):
                self.access_code_sensors[idx].update_sensor(idx, access_codes[idx])
            else:
                self.access_code_sensors[idx].update_sensor(idx, None)

    async def async_set_lock_access_code(
        self,
        access_code: str,
        reservation_code: str,
        starts_at: str,  # "2023-05-01T16:00:00-0600"
        ends_at: str,
    ) -> None:
        """Set the access_code to index X on the lock."""
        _LOGGER.info("Function triggered async_set_lock_access_code")

        for sensor in self.access_code_sensors:
            if sensor.access_code is None:
                # use the first empty slot
                try:
                    await sensor.create_code(
                        access_code,
                        reservation_code,
                        starts_at,
                        ends_at,
                    )
                    _LOGGER.debug("User code '%s' set", access_code)
                    return True
                except Exception as exc:  # pylint: disable=broad-except
                    _LOGGER.error("Failed to set user code '%s': %s", access_code, exc)
                return False
        _LOGGER.error("Out of slots for lock %s", self.name)
        return False

    async def async_sync_lock_access_code(self) -> None:
        """Sync the access codes with the lock."""
        _LOGGER.info("Function triggered async_sync_lock_access_code")
        await self.update_sensors()

    async def async_update_lock_access_code(
        self,
        access_code: str,
        reservation_code: str,
        starts_at: str,  # "2023-05-01T16:00:00-0600"
        ends_at: str,
    ) -> None:
        """Set the access_code to index X on the lock."""
        _LOGGER.info("Function triggered async_update_lock_access_code")
        for sensor in self.access_code_sensors:
            if sensor.reservation_code == reservation_code:
                # use the first empty slot
                try:
                    await sensor.update_code(
                        access_code,
                        reservation_code,
                        starts_at,
                        ends_at,
                    )
                    _LOGGER.debug("User code '%s' updated", access_code)
                    await self.update_sensors()
                    return True
                except Exception as exc:  # pylint: disable=broad-except
                    _LOGGER.error("Failed to set user code '%s': %s", access_code, exc)
                return False
        _LOGGER.error("Reservation not found %s", self.name)
        return False

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
