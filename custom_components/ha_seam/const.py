"""Constants for the Seam Integeration for Home Assistant integration."""
from typing import Final

DOMAIN = "ha_seam"
VERSION = "v0.0.0"

CONF_APIKEY: Final = "api_key"
CONF_DEVICE_ID: Final = "device_id"
CONF_DOMAIN: Final = "domain"
CONF_TYPE: Final = "type"
CONF_ENTITY_ID: Final = "entity_id"

SERVICE_CLEAR_LOCK_ACCESS_CODE: Final = "clear_lock_access_code"
SERVICE_SET_LOCK_ACCESS_CODE: Final = "set_lock_access_code"
SERVICE_SET_VALUE: Final = "set_value"

ATTR_ACCESS_CODE: Final = "access_code"
ACCESS_CODE_ICON: Final = "mdi:account-key"
