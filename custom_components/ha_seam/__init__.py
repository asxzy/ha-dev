"""The Seam Integeration for Home Assistant integration."""
from __future__ import annotations

import logging

import seamapi

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_APIKEY, DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]


class SeamManager:
    """Manages a single Seam account."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize."""
        self.hass = hass
        self.api_client = seamapi.Seam(api_key)
        self.lock2device = {}
        self.device2lock = {}

    def get_locks(self):
        """Get all locks."""
        return self.api_client.locks.list()

    def get_access_codes(self, lock):
        """Get all access codes for a lock."""
        return self.api_client.access_codes.list(device=lock)

    def add_device(self, lock, device: dr.DeviceEntry):
        """Add a lock to the device registry."""
        self.lock2device[lock.device_id] = device
        self.device2lock[device.id] = lock

    async def create_code(
        self,
        device,
        code: str = "8888",
        name: str = "test",
        starts_at: str = "2023-05-01T16:00:00-0600",
        ends_at: str = "2033-12-31T11:15:00-0600",
    ):
        """Create a new access code."""
        def _create_code(device, code, name, starts_at, ends_at):
            return self.api_client.access_codes.create(
                device=device,
                code=code,
                name=name,
                starts_at=starts_at,
                ends_at=ends_at,
            )

        try:
            await self.hass.async_add_executor_job(
                _create_code,
                device,
                code,
                name,
                starts_at,
                ends_at,
            )
            _LOGGER.info("Successfully created code")
            return True
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Failed to create code: %s", exc)
            return False


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Seam Integeration for Home Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # TODO 1. Create API instance
    api_key = entry.data[CONF_APIKEY]
    seam_manager = SeamManager(hass, api_key)

    # TODO 2. Validate the API connection (and authentication)
    locks = await hass.async_add_executor_job(seam_manager.get_locks)

    # TODO 3. Store an API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = seam_manager
    device_registry = dr.async_get(hass)

    for lock in locks:
        # support august lock only
        if lock.device_type == "august_lock":
            # we can use lock.device_id as the identifier if we want to
            lock_id = lock.device_id
            device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, lock_id)},
                manufacturer=lock.properties.manufacturer,
                name=lock.properties.name,
                model="august_lock",
                sw_version="unknown",
            )
            seam_manager.add_device(lock, device)
        else:
            _LOGGER.error("Unsupported lock type: %s", lock.device_type)
            continue

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload
