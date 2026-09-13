from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import PERCENTAGE

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device in coordinator.data:
        if device._device_model_number == "AY028MHA1":
            entities.append(TargetHumidityNumber(coordinator, device))

    async_add_entities(entities)


class TargetHumidityNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._dsn = device._dsn
        self._attr_name = f"{device._name} Target Humidity"
        self._attr_unique_id = f"{device._dsn}_target_humidity"
        self._attr_native_min_value = 30
        self._attr_native_max_value = 80
        self._attr_native_step = 1
        self._attr_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self):
        return self._device.get_property_value("humidity")

    async def async_set_native_value(self, value: float):
        await self._device.async_set_property_value("humidity", int(value))
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        # Re-bind device reference to avoid stale objects
        for dev in self.coordinator.data:
            if getattr(dev, "_dsn", None) == self._dsn:
                self._device = dev
                break

        self.async_write_ha_state()