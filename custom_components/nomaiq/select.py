from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

FAN_SPEED_MAP = {
    "Auto": "Smart",
    "Low": "Low",
    "High": "High",
}

AYLA_TO_HASS_FAN = {v: k for k, v in FAN_SPEED_MAP.items()}

MODE_MAP = {
    "Manual": "Normal",
    "Continuous": "Persistent",
    "Auto Dry": "Auto",
}

AYLA_TO_HASS_MODE = {v: k for k, v in MODE_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device in coordinator.data:
        if device._device_model_number == "AY028MHA1":
            entities.append(DehumidifierModeSelect(coordinator, device))
            entities.append(DehumidifierFanSpeedSelect(coordinator, device))

    async_add_entities(entities)


class _NomaIQDeviceRebindSelect(CoordinatorEntity, SelectEntity):
    """Select entity that re-binds its device reference on every coordinator update."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._dsn = device._dsn

    def _rebind_device(self) -> None:
        for dev in self.coordinator.data:
            if getattr(dev, "_dsn", None) == self._dsn:
                self._device = dev
                return

    @callback
    def _handle_coordinator_update(self) -> None:
        self._rebind_device()
        self.async_write_ha_state()


class DehumidifierModeSelect(_NomaIQDeviceRebindSelect):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)
        self._attr_name = f"{device._name} Mode"
        self._attr_unique_id = f"{device._dsn}_mode"
        self._attr_options = list(MODE_MAP.keys())

    @property
    def current_option(self):
        raw_mode = self._device.get_property_value("mode")
        return AYLA_TO_HASS_MODE.get(raw_mode, "Manual")

    async def async_select_option(self, option: str):
        if option in MODE_MAP:
            _LOGGER.debug("Setting mode to %s (%s)", option, MODE_MAP[option])
            await self._device.async_set_property_value("mode", MODE_MAP[option])
            await self.coordinator.async_request_refresh()


class DehumidifierFanSpeedSelect(_NomaIQDeviceRebindSelect):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device)
        self._attr_name = f"{device._name} Fan Speed"
        self._attr_unique_id = f"{device._dsn}_fan_speed"
        self._attr_options = list(FAN_SPEED_MAP.keys())

    @property
    def current_option(self):
        raw_speed = self._device.get_property_value("fan_speed")
        return AYLA_TO_HASS_FAN.get(raw_speed, "Auto")

    async def async_select_option(self, option: str):
        if option in FAN_SPEED_MAP:
            _LOGGER.debug("Setting fan speed to %s (%s)", option, FAN_SPEED_MAP[option])
            await self._device.async_set_property_value("fan_speed", FAN_SPEED_MAP[option])
            await self.coordinator.async_request_refresh()
