"""Constants for the Seam Integeration for Home Assistant integration."""
from typing import Final

DOMAIN = "ha_seam"
VERSION = "v0.0.0"

CONF_APIKEY: Final = "api_key"

SERVICE_SET_LOCK_ACCESS_CODE: Final = "set_lock_access_code"
SERVICE_SYNC_LOCK_ACCESS_CODE: Final = "sync_lock_access_code"
SERVICE_UPDATE_LOCK_ACCESS_CODE: Final = "update_lock_access_code"

ATTR_ACCESS_CODE: Final = "access_code"
ATTR_RESERVATION_CODE: Final = "reservation_code"
ATTR_STARTS_AT: Final = "starts_at"
ATTR_ENDS_AT: Final = "ends_at"
ACCESS_CODE_ICON: Final = "mdi:account-key"
LOCK_ICON: Final = "mdi:lock"
MAX_ACCESS_CODES: Final = 5
