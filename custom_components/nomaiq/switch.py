from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NomaIQDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SWITCH_TYPES = {
    "power": "Power",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NomaIQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device in coordinator.devices_by_serial.values():
        if device._device_model_number == "AY028MHA1":
            for prop, name in SWITCH_TYPES.items():
                if prop in device.property_values:
                    entities.append(NomaIQSwitch(coordinator, device, prop, name))

    async_add_entities(entities)


class NomaIQSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, device, prop: str, name: str):
        super().__init__(coordinator)
        self._device = device
        self._dsn = device._dsn
        self._prop = prop
        self._name = name

    @property
    def name(self):
        return f"{self._device._name} {self._name}"

    @property
    def unique_id(self):
        return f"{self._dsn}_{self._prop}_switch"

    @property
    def is_on(self):
        return bool(self._device.get_property_value(self._prop))

    async def async_turn_on(self, **kwargs):
        await self._device.async_set_property_value(self._prop, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._device.async_set_property_value(self._prop, False)
        await self.coordinator.async_request_refresh()

    @property
    def available(self):
        return self._device is not None

    def _rebind_device(self) -> None:
        # Prefer devices_by_serial if present
        if hasattr(self.coordinator, "devices_by_serial"):
            dev = self.coordinator.devices_by_serial.get(self._dsn)
            if dev:
                self._device = dev
                return

        # Fallback to coordinator.data
        for dev in self.coordinator.data:
            if getattr(dev, "_dsn", None) == self._dsn:
                self._device = dev
                return

    @callback
    def _handle_coordinator_update(self) -> None:
        self._rebind_device()
        self.async_write_ha_state()
