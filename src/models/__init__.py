"""
Domain Models for Logistics Management System
"""

from .item import (
    Item,
    ItemType,
    StandardParcel,
    FragileParcel,
    PerishableParcel,
    HazardousParcel,
)
from .vehicle import (
    Vehicle,
    VehicleType,
    Motorcycle,
    Van,
    RefrigeratedTruck,
    HeavyTruck,
)
from .customer import Address, Customer
from .shipment import (
    Shipment,
    ShipmentStatus,
    TrackingEvent,
)

__all__ = [
    "Item",
    "ItemType",
    "StandardParcel",
    "FragileParcel",
    "PerishableParcel",
    "HazardousParcel",
    "Vehicle",
    "VehicleType",
    "Motorcycle",
    "Van",
    "RefrigeratedTruck",
    "HeavyTruck",
    "Address",
    "Customer",
    "Shipment",
    "ShipmentStatus",
    "TrackingEvent",
]
