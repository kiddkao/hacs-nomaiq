from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.humidifier import (
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NomaIQDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_MODES = ["Manual", "Continuous", "Auto Dry"]
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
    coordinator: NomaIQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Debug: log all devices found
    _LOGGER.debug(
        "Setting up NomaIQ humidifiers. Devices in coordinator: %s", len(coordinator.data)
    )
    for device in coordinator.data:
        _LOGGER.debug(
            "Found device: %s model=%s", device._name, getattr(device, "_device_model_number", None)
        )
        if getattr(device, "_device_model_number", None) == "AY028MHA1":
            entities.append(NomaIQDehumidifier(coordinator, device))

    if not entities:
        _LOGGER.warning("No compatible NomaIQ humidifiers found.")

    async_add_entities(entities)


class NomaIQDehumidifier(CoordinatorEntity, HumidifierEntity):
    """NomaIQ Dehumidifier entity."""

    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_min_humidity = 30
    _attr_max_humidity = 80
    _attr_available_modes = USER_MODES
    _attr_device_class = "dehumidifier"

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._attr_name = device._name or "Dehumidifier"
        self._attr_unique_id = f"{device._dsn}_humidifier"

    # -------------------------
    # State properties
    # -------------------------
    @property
    def is_on(self) -> bool:
        return bool(self._device.get_property_value("power"))

    @property
    def current_humidity(self) -> int | None:
        return self._device.get_property_value("indoor_humidity")

    @property
    def target_humidity(self) -> int:
        return self._device.get_property_value("humidity")

    @property
    def mode(self) -> str:
        raw_mode = self._device.get_property_value("mode")
        return AYLA_TO_HASS_MODE.get(raw_mode, "Manual")

    # -------------------------
    # Control actions
    # -------------------------
    async def async_set_humidity(self, humidity: int) -> None:
        await self._set_property_safe("humidity", humidity)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set_property_safe("power", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_property_safe("power", False)

    async def async_set_mode(self, mode: str) -> None:
        if mode in MODE_MAP:
            await self._set_property_safe("mode", MODE_MAP[mode])

    # -------------------------
    # Safe API call + immediate refresh
    # -------------------------
    async def _set_property_safe(self, property_name: str, value: Any) -> None:
        """Send a property update safely and refresh state."""
        # Map boolean power to correct API integer
        if property_name == "power":
            value = 1 if value else 0

        try:
            await self._device.async_set_property_value(property_name, value)
        except Exception as ex:
            _LOGGER.error(
                "Failed to set property '%s' on %s: %s",
                property_name,
                self._attr_name,
                ex,
            )
            return

        # Immediately refresh entity state
        await self.coordinator.async_request_refresh()

    # -------------------------
    # Coordinator update callback
    # -------------------------
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Re-bind the device object to the freshly updated one from coordinator
        for dev in self.coordinator.data:
            if dev._dsn == self._device._dsn:
                self._device = dev
                break

        # Push updated state to Home Assistant
        self.async_write_ha_state()