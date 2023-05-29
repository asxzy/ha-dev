"""Support for August lock."""
import logging
from typing import TYPE_CHECKING, Any

from dateutil import parser as dt_parser
from seamapi.types import Device as SeamDevice
import voluptuous as vol

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_ACCESS_CODE,
    ATTR_ENDS_AT,
    ATTR_GUEST_NAME,
    ATTR_STARTS_AT,
    DOMAIN,
    LOCK_ICON,
    SERVICE_CLEAR_LOCK_ACCESS_CODE,
    SERVICE_SET_LOCK_ACCESS_CODE,
)
from .sensor import SeamAccessCodeSensor

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
            vol.Required(ATTR_GUEST_NAME): cv.string,
            vol.Required(ATTR_STARTS_AT): cv.string,
            vol.Required(ATTR_ENDS_AT): cv.string,
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


class SeamLock(LockEntity):
    """Representation of a Seam lock."""

    _attr_should_poll = False
    _attr_has_entity_name = True

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
        self._attr_name = self.seam_device.properties.name
        self._attr_unique_id = self.seam_device.device_id
        self._attr_icon = LOCK_ICON

        self.access_code_sensors = []

    async def init_sensors(self):
        """Initialize the sensors."""
        _LOGGER.info("Initializing %s sensors", self.seam_manager.max_sensor_count)
        self.access_code_sensors = [
            SeamAccessCodeSensor(
                seam_manager=self.seam_manager,
                device=self,
                lock=self.seam_device,
                access_code_slot_idx=x,
                guest_name=None,
                access_code=None,
                starts_at=None,
                ends_at=None,
                access_code_id=None,
            )
            for x in range(self.seam_manager.max_sensor_count)
        ]

    async def update_sensors(self):
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
        guest_name: str ,
        starts_at: str , # "2023-05-01T16:00:00-0600"
        ends_at: str ,
    ) -> None:
        """Set the access_code to index X on the lock."""
        _LOGGER.info("Function triggered async_set_lock_access_code")

        # starts_at_dt = datetime.strptime(starts_at, '%Y-%m-%dT%H:%M:%S%z')
        # starts_at = starts_at_dt.format('YYYY-MM-DDTHH:mm:ss.SSS') + 'Z'


        for sensor in self.access_code_sensors:
            if sensor.access_code == access_code:
                _LOGGER.info("User code '%s' already set", access_code)
                # check if the code details are the same
                # show a warning if they are not
                if sensor.guest_name != guest_name:
                    _LOGGER.error("User code '%s' already set with different guest name. Request '%s' but existing '%s'", access_code, guest_name, sensor.guest_name)
                    return False
                if dt_parser.isoparse(sensor.starts_at) != dt_parser.isoparse(starts_at):
                    _LOGGER.error("User code '%s' already set with different start time. Request '%s' but existing '%s'", access_code, starts_at, sensor.starts_at)
                    return False
                if dt_parser.isoparse(sensor.ends_at) != dt_parser.isoparse(ends_at):
                    _LOGGER.error("User code '%s' already set with different end time. Request '%s' but existing '%s'", access_code, ends_at, sensor.ends_at)
                    return False
                return True
            elif sensor.access_code is None:
                # use the first empty slot
                try:
                    await sensor.create_code(
                        access_code,
                        guest_name,
                        starts_at,
                        ends_at,
                    )
                    _LOGGER.debug("User code '%s' set", access_code)
                    return True
                except Exception as exc: # pylint: disable=broad-except
                    _LOGGER.error("Failed to set user code '%s': %s", access_code, exc)
                return False
        _LOGGER.error("Out of slots")
        return False

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
