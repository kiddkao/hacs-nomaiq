from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for device in coordinator.data:
        if device._device_model_number == "AY028MHA1":
            entities.append(IndoorHumiditySensor(coordinator, device))

    async_add_entities(entities)


class IndoorHumiditySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._dsn = device._dsn
        self._attr_name = f"{device._name} Indoor Humidity"
        self._attr_unique_id = f"{device._dsn}_indoor_humidity"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = "humidity"

    @property
    def native_value(self) -> int | None:
        return self._device.get_property_value("indoor_humidity")

    def _rebind_device(self) -> None:
        for dev in self.coordinator.data:
            if getattr(dev, "_dsn", None) == self._dsn:
                self._device = dev
                return

    @callback
    def _handle_coordinator_update(self) -> None:
        self._rebind_device()
        self.async_write_ha_state()
