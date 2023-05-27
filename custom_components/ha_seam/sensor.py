"""Creating sensors for upcoming events."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from seamapi.types import Device as SeamDevice

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SeamManager
from .const import ACCESS_CODE_ICON, DOMAIN, MAX_ACCESS_CODES

if TYPE_CHECKING:
    from .lock import SeamLock

_LOGGER = logging.getLogger(__name__)


class SeamAccessCodeSensor(SensorEntity):
    """Implementation of a seam code."""

    # _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = ACCESS_CODE_ICON
    _attr_name = "Seam Access Code"

    def __init__(
        self,
        device: DeviceEntry,
        lock: SeamDevice,
        guest_name: str,
        access_code: str,
        starts_at: str,
        ends_at: str,
        seam_access_code_id: str,
        seam_access_code_slot_idx: int,
    ) -> None:
        """Initialize the sensor."""

        self._device = device
        self._lock = lock
        self._device_id = device.id
        self._guest_name = guest_name
        self._access_code = access_code
        self._access_code_slot_idx = seam_access_code_slot_idx
        self._starts_at = starts_at
        self._ends_at = ends_at
        self._seam_access_code_id = seam_access_code_id
        self._seam_access_code_slot_idx = seam_access_code_slot_idx

        # HA attributes
        self._entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = f"{device.name}_slot_{self._seam_access_code_slot_idx+1}"
        self._attr_unique_id = f"{self._device_id}_slot_{self._seam_access_code_slot_idx+1}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._lock.device_id)})

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ACCESS_CODE_ICON

    # @property
    # def device_info(self):
    #     """Return the device info block."""
    #     return self._device.device_info

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"seam_access_code_{self._device.name}_{self._guest_name}_{self._access_code}"

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
    def seam_access_code_id(self):
        """Return the unique_id."""
        return self._seam_access_code_id

    @staticmethod
    async def create(
        seam_manager: SeamManager,
        device: SeamLock,
        guest_name,
        access_code,
        starts_at,
        ends_at,
        access_code_slot_idx: int,
    ) -> SeamAccessCodeSensor:
        """Create a new sensor."""
        _LOGGER.error("Creating code: %s", access_code)
        lock = seam_manager.device2lock[device._device.id]
        seam_access_code = await seam_manager.create_code(
            device=lock,
            code=access_code,
            name=guest_name,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        _LOGGER.error("seam_access_code: %s", seam_access_code)

        return SeamAccessCodeSensor(
            device,
            lock,
            guest_name,
            access_code,
            starts_at,
            ends_at,
            seam_access_code.access_code_id,
            access_code_slot_idx,
        )


async def async_setup_platform(
    hass: HomeAssistant, config, add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Set up this integration with config flow."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up SeamAccessCode sensors."""
    _LOGGER.error("Async_setup_entry for sensor")
    _LOGGER.error("Config_entry: %s", config_entry)
    seam_manager: SeamManager = hass.data[DOMAIN][config_entry.entry_id]
    #     await seam_manager.update()
    sensors = []
    for device in seam_manager.seam2ha.values():
        lock = seam_manager.device2lock[device.id]
        access_codes = await hass.async_add_executor_job(seam_manager.get_access_codes, lock)
        for idx in range(MAX_ACCESS_CODES):
            access_code_slot_idx = idx + 1
            if idx >= len(access_codes):
                sensors.append(
                    SeamAccessCodeSensor(
                        device,
                        lock,
                        f"future_guest_{access_code_slot_idx}",
                        "unavailable",
                        "unavailable",
                        "unavailable",
                        "unavailable",
                        access_code_slot_idx,
                    )
                )
            else:
                access_code = access_codes[idx]
                _LOGGER.error("Adding sensor: %s", access_code)
                sensors.append(
                    SeamAccessCodeSensor(
                        device,
                        lock,
                        access_code.name,
                        access_code.code,
                        access_code.starts_at,
                        access_code.ends_at,
                        access_code.access_code_id,
                        access_code_slot_idx,
                    )
                )
    if sensors:
        async_add_entities(sensors)
