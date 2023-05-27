"""Creating sensors for upcoming events."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SeamManager
from .const import ACCESS_CODE_ICON, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SeamAccessCodeSensor(Entity):
    """Implementation of a seam code."""

    def __init__(
        self,
        hass: HomeAssistant,
        device: DeviceEntry,
        guest_name: str,
        access_code: str,
        starts_at: str,
        ends_at: str,
        seam_access_code_id: str,
    ) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._device = device
        self._guest_name = guest_name
        self._access_code = access_code
        self._starts_at = starts_at
        self._ends_at = ends_at
        self._seam_access_code_id = seam_access_code_id

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ACCESS_CODE_ICON

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
    def create(
        hass: HomeAssistant,
        device,
        guest_name,
        access_code,
        starts_at,
        ends_at,
    ) -> SeamAccessCodeSensor:
        """Create a new sensor."""
        _LOGGER.error("Creating code: %s", access_code)
        seam_manager: SeamManager = hass.data[DOMAIN]
        lock = seam_manager.device2lock[device.id]
        seam_access_code = seam_manager.api_client.access_codes.create(
            device=lock,
            code=access_code,
            name=guest_name,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        _LOGGER.error("seam_access_code: %s", seam_access_code)


        return SeamAccessCodeSensor(
            hass,
            device,
            guest_name,
            access_code,
            starts_at,
            ends_at,
            seam_access_code.access_code_id,
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
    for device in seam_manager.lock2device.values():
        lock = seam_manager.device2lock[device.id]
        access_codes = await hass.async_add_executor_job(seam_manager.get_access_codes, lock)
        for access_code in access_codes:
            _LOGGER.error("Adding sensor: %s", access_code)
            sensors.append(
                SeamAccessCodeSensor(
                    hass,
                    device,
                    access_code.name,
                    access_code.code,
                    access_code.starts_at,
                    access_code.ends_at,
                    access_code.access_code_id,
                )
            )
    if sensors:
        async_add_entities(sensors)
