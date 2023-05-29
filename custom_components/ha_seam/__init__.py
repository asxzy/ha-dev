"""The Seam Integeration for Home Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_APIKEY, DOMAIN
from .seam import SeamManager

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]



async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Set up Seam Integeration for Home Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # 1. Create API instance
    api_key = config_entry.data[CONF_APIKEY]
    seam_manager = SeamManager(hass, config_entry, api_key)
    _LOGGER.info("Initializing Seam Manager")

    # 2. Validate the API connection (and authentication)
    await seam_manager.init_locks()
    _LOGGER.info("Initializing Seam Locks")

    # 3. Store an API object for your platforms to access
    hass.data[DOMAIN][config_entry.entry_id] = seam_manager
    _LOGGER.info("Storing Seam Manager")

    # 4. Create devices for each lock
    device_registry = dr.async_get(hass)
    for lock in seam_manager.locks.values():
        _LOGGER.info("Creating device for lock: %s", lock.unique_id)
        _LOGGER.info("Creating device for lock identifiers: %s", lock.device_info["identifiers"])
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers=lock.device_info["identifiers"],
            manufacturer="August",
            name=lock.name,
            model="August Lock",
            sw_version="1.0",
        )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload
