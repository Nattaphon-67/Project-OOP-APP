"""
Fleet Service
Manages fleet of vehicles, optimizes vehicle allocation, and enforces transportation rules.
"""

from typing import List, Optional, Tuple, Dict, Any
from ..models.item import Item
from ..models.vehicle import Vehicle, VehicleType, Motorcycle, Van, RefrigeratedTruck, HeavyTruck


class FleetService:
    """
    บริการจัดการยานพาหนะและการจัดสรรรถสำหรับพัสดุ
    """

    def __init__(self):
        self._vehicles: List[Vehicle] = []

    def register_vehicle(self, vehicle: Vehicle) -> None:
        self._vehicles.append(vehicle)

    def get_all_vehicles(self) -> List[Vehicle]:
        return list(self._vehicles)

    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        for v in self._vehicles:
            if v.vehicle_id == vehicle_id:
                return v
        return None

    def find_best_vehicle(self, item: Item) -> Tuple[Optional[Vehicle], str]:
        """
        ค้นหายานพาหนะที่เหมาะสมที่สุดสำหรับพัสดุตามลำดับ:
        1. ตรวจสอบเงื่อนไขข้อจำกัดความปลอดภัย (can_transport)
        2. ตรวจสอบพื้นที่และน้ำหนักคงเหลือ (can_fit)
        3. เลือกรถที่ขนาดพอดีที่สุดเพื่อความคุ้มค่าพลังงาน (Motorcycle -> Van -> Refrigerated/Heavy)
        """
        type_priority = {
            VehicleType.MOTORCYCLE: 1,
            VehicleType.VAN: 2,
            VehicleType.REFRIGERATED_TRUCK: 3,
            VehicleType.HEAVY_TRUCK: 4,
        }

        compatible_vehicles: List[Vehicle] = []
        reject_reasons = []

        for vehicle in self._vehicles:
            if not vehicle.is_active:
                continue

            can_carry, reason = vehicle.can_transport(item)
            if not can_carry:
                reject_reasons.append(f"{vehicle.license_plate}: {reason}")
                continue

            can_fit, fit_reason = vehicle.can_fit(item)
            if not can_fit:
                reject_reasons.append(f"{vehicle.license_plate}: {fit_reason}")
                continue

            compatible_vehicles.append(vehicle)

        if not compatible_vehicles:
            detail = " | ".join(reject_reasons) if reject_reasons else "ไม่มียานพาหนะในระบบ"
            return None, f"ไม่มียานพาหนะที่เหมาะสมในขณะนี้ ({detail})"

        # เรียงลำดับตามขนาดรถที่ประหยัดที่สุด และพื้นที่คงเหลือ
        compatible_vehicles.sort(
            key=lambda v: (
                type_priority.get(v.get_vehicle_type(), 99),
                v.get_available_weight(),
            )
        )

        selected = compatible_vehicles[0]
        return selected, f"เลือกยานพาหนะที่เหมาะสมที่สุด: ทะเบียน {selected.license_plate} ({selected.get_vehicle_type().value})"

    def get_fleet_summary(self) -> Dict[str, Any]:
        """สรุปข้อมูลกองยานพาหนะ"""
        total = len(self._vehicles)
        active = sum(1 for v in self._vehicles if v.is_active)
        total_items_loaded = sum(len(v.loaded_items) for v in self._vehicles)
        total_weight_loaded = sum(v.current_weight_load() for v in self._vehicles)
        total_capacity_weight = sum(v.max_weight for v in self._vehicles)

        avg_utilization = (
            round((total_weight_loaded / total_capacity_weight) * 100, 1)
            if total_capacity_weight > 0
            else 0.0
        )

        return {
            "total_vehicles": total,
            "active_vehicles": active,
            "total_items_loaded": total_items_loaded,
            "total_weight_loaded_kg": round(total_weight_loaded, 2),
            "total_capacity_kg": round(total_capacity_weight, 2),
            "avg_utilization_pct": avg_utilization,
        }
