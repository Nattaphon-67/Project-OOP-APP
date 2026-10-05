"""
Repository Pattern for Data Storage and Persistence
Provides an in-memory data store with JSON export and import capabilities.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from ..models.shipment import Shipment
from ..models.vehicle import Vehicle
from ..models.customer import Customer


class LogisticsRepository:
    """
    Data Repository สำหรับจัดเก็บข้อมูล Shipments, Vehicles และ Customers
    """

    def __init__(self, data_file_path: Optional[str] = None):
        self._data_file_path = data_file_path
        self._shipments: Dict[str, Shipment] = {}
        self._vehicles: Dict[str, Vehicle] = {}
        self._customers: Dict[str, Customer] = {}

    # --- Shipment Methods ---

    def add_shipment(self, shipment: Shipment) -> None:
        self._shipments[shipment.tracking_number] = shipment

    def get_shipment(self, tracking_number: str) -> Optional[Shipment]:
        return self._shipments.get(tracking_number.strip().upper())

    def get_all_shipments(self) -> List[Shipment]:
        return list(self._shipments.values())

    # --- Vehicle Methods ---

    def add_vehicle(self, vehicle: Vehicle) -> None:
        self._vehicles[vehicle.vehicle_id] = vehicle

    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        return self._vehicles.get(vehicle_id)

    def get_all_vehicles(self) -> List[Vehicle]:
        return list(self._vehicles.values())

    # --- Customer Methods ---

    def add_customer(self, customer: Customer) -> None:
        self._customers[customer.customer_id] = customer

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self._customers.get(customer_id)

    def get_all_customers(self) -> List[Customer]:
        return list(self._customers.values())

    # --- Persistence ---

    def export_to_json(self, target_path: Optional[str] = None) -> str:
        """ส่งออกข้อมูลทั้งหมดเป็น JSON เพื่อเก็บประวัติ"""
        path = target_path or self._data_file_path or "shipments_data.json"
        data = {
            "shipments": [s.to_dict() for s in self._shipments.values()],
            "vehicles": [v.to_dict() for v in self._vehicles.values()],
            "customers": [c.to_dict() for c in self._customers.values()],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path
