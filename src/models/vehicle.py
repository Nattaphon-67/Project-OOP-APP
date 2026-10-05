"""
Vehicle Models for Fleet and Transport
Demonstrating OOP Abstraction, Inheritance, Encapsulation, and Polymorphism.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Dict, Any
from .item import Item, ItemType


class VehicleType(str, Enum):
    """ประเภทยานพาหนะขนส่ง"""
    MOTORCYCLE = "MOTORCYCLE"          # รถจักรยานยนต์
    VAN = "VAN"                        # รถตู้ทึบ
    REFRIGERATED_TRUCK = "REFRIGERATED_TRUCK"  # รถห้องเย็น
    HEAVY_TRUCK = "HEAVY_TRUCK"        # รถบรรทุกใหญ่


class Vehicle(ABC):
    """
    คลาสแม่แบบนามธรรม (Abstract Base Class) สำหรับยานพาหนะขนส่งทุกประเภท
    """

    def __init__(
        self,
        vehicle_id: str,
        license_plate: str,
        max_weight: float,
        max_volume: float,
        driver_name: str,
    ):
        self._vehicle_id = vehicle_id
        self._license_plate = license_plate
        self._max_weight = float(max_weight)
        self._max_volume = float(max_volume)
        self._driver_name = driver_name
        self._loaded_items: List[Item] = []
        self._is_active = True

    # --- Encapsulation: Getters ---

    @property
    def vehicle_id(self) -> str:
        return self._vehicle_id

    @property
    def license_plate(self) -> str:
        return self._license_plate

    @property
    def max_weight(self) -> float:
        return self._max_weight

    @property
    def max_volume(self) -> float:
        return self._max_volume

    @property
    def driver_name(self) -> str:
        return self._driver_name

    @driver_name.setter
    def driver_name(self, name: str):
        if not name or not name.strip():
            raise ValueError("ชื่อพนักงานขับรถต้องไม่ว่าง")
        self._driver_name = name.strip()

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, status: bool):
        self._is_active = status

    @property
    def loaded_items(self) -> List[Item]:
        # คืนค่าสำเนาเพื่อป้องกันการแก้ไขตรงภายนอก (Encapsulation)
        return list(self._loaded_items)

    # --- Capacity Calculation Methods ---

    def current_weight_load(self) -> float:
        """คำนวณน้ำหนักรวมของพัสดุที่บรรทุกอยู่ขณะนี้ (กก.)"""
        return sum(item.weight for item in self._loaded_items)

    def current_volume_load(self) -> float:
        """คำนวณปริมาตรรวมของพัสดุที่บรรทุกอยู่ขณะนี้ (m³)"""
        return sum(item.volume for item in self._loaded_items)

    def get_available_weight(self) -> float:
        """น้ำหนักที่ยังสามารถบรรทุกได้อีก (กก.)"""
        return max(0.0, self._max_weight - self.current_weight_load())

    def get_available_volume(self) -> float:
        """ปริมาตรที่ยังสามารถบรรทุกได้อีก (m³)"""
        return max(0.0, self._max_volume - self.current_volume_load())

    def get_utilization_percentage(self) -> float:
        """อัตราส่วนการใช้พื้นที่บรรทุกตามน้ำหนัก (%)"""
        if self._max_weight == 0:
            return 0.0
        return round((self.current_weight_load() / self._max_weight) * 100, 1)

    # --- Loading & Compatibility ---

    def can_fit(self, item: Item) -> Tuple[bool, str]:
        """ตรวจสอบว่าน้ำหนักและปริมาตรไม่เกินความจุที่เหลืออยู่"""
        if item.weight > self.get_available_weight():
            return False, f"น้ำหนักเกินความจุที่เหลือ (ต้องการ {item.weight} กก. เหลือ {self.get_available_weight():.2f} กก.)"
        if item.volume > self.get_available_volume():
            return False, f"ปริมาตรเกินความจุที่เหลือ (ต้องการ {item.volume} m³ เหลือ {self.get_available_volume():.3f} m³)"
        return True, "ความจุเพียงพอ"

    @abstractmethod
    def can_transport(self, item: Item) -> Tuple[bool, str]:
        """
        ตรวจสอบว่ายานพาหนะนี้สามารถบรรทุกพัสดุประเภทนี้ได้ตามข้อกำหนดหรือไม่
        (Polymorphic method)
        """
        pass

    @abstractmethod
    def get_vehicle_type(self) -> VehicleType:
        """คืนค่าประเภทยานพาหนะ"""
        pass

    def load_item(self, item: Item) -> Tuple[bool, str]:
        """นำพัสดุขึ้นบรรทุกบนยานพาหนะ"""
        if not self._is_active:
            return False, f"ยานพาหนะ {self._vehicle_id} ไม่พร้อมใช้งาน"

        can_deliver, reason = self.can_transport(item)
        if not can_deliver:
            return False, f"ไม่สามารถบรรทุกได้: {reason}"

        fits, fit_reason = self.can_fit(item)
        if not fits:
            return False, f"พื้นที่ไม่เพียงพอ: {fit_reason}"

        self._loaded_items.append(item)
        return True, f"นำพัสดุ {item.item_id} ขึ้นยานพาหนะ {self._license_plate} สำเร็จ"

    def unload_item(self, item_id: str) -> bool:
        """นำพัสดุออกจากยานพาหนะเมื่อส่งมอบสำเร็จ"""
        for i, item in enumerate(self._loaded_items):
            if item.item_id == item_id:
                self._loaded_items.pop(i)
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vehicle_id": self._vehicle_id,
            "license_plate": self._license_plate,
            "vehicle_type": self.get_vehicle_type().value,
            "driver_name": self._driver_name,
            "max_weight_kg": self._max_weight,
            "max_volume_m3": self._max_volume,
            "current_weight_kg": round(self.current_weight_load(), 2),
            "current_volume_m3": round(self.current_volume_load(), 3),
            "utilization_pct": self.get_utilization_percentage(),
            "loaded_items_count": len(self._loaded_items),
            "is_active": self._is_active,
        }

    def __str__(self) -> str:
        return (
            f"[{self.get_vehicle_type().value}] ทะเบียน: {self._license_plate} "
            f"(รับได้ {self._max_weight}kg, บรรทุกแล้ว {self.current_weight_load():.1f}kg)"
        )


class Motorcycle(Vehicle):
    """
    รถจักรยานยนต์ส่งด่วน
    - น้ำหนักจำกัดไม่เกิน 25 กก.
    - รับได้เฉพาะ STANDARD และ FRAGILE (ขนาดเล็ก)
    - ห้ามรับ PERISHABLE (ไม่มีห้องเย็น) หรือ HAZARDOUS
    """

    def __init__(self, vehicle_id: str, license_plate: str, driver_name: str):
        super().__init__(
            vehicle_id=vehicle_id,
            license_plate=license_plate,
            max_weight=25.0,
            max_volume=0.08,
            driver_name=driver_name,
        )

    def get_vehicle_type(self) -> VehicleType:
        return VehicleType.MOTORCYCLE

    def can_transport(self, item: Item) -> Tuple[bool, str]:
        if item.get_item_type() == ItemType.HAZARDOUS:
            return False, "รถจักรยานยนต์ไม่ได้รับอนุญาตให้บรรทุกวัตถุอันตราย"
        if item.get_item_type() == ItemType.PERISHABLE:
            return False, "รถจักรยานยนต์ไม่มีระบบควบคุมอุณหภูมิสำหรับสินค้าเน่าเสียง่าย"
        if item.weight > 15.0:
            return False, "ชิ้นเดียวหนักเกิน 15 กก. เกินความปลอดภัยสำหรับรถจักรยานยนต์"
        return True, "สามารถจัดส่งด้วยรถจักรยานยนต์ได้"


class Van(Vehicle):
    """
    รถตู้ทึบขนส่งทั่วไป
    - น้ำหนักไม่เกิน 800 กก., ปริมาตร 5.0 m³
    - รับ STANDARD และ FRAGILE ได้ดีเยี่ยม
    - ไม่รับ PERISHABLE (ไม่มีระบบทำความเย็น) หรือ HAZARDOUS วัตถุอันตรายสูง
    """

    def __init__(self, vehicle_id: str, license_plate: str, driver_name: str):
        super().__init__(
            vehicle_id=vehicle_id,
            license_plate=license_plate,
            max_weight=800.0,
            max_volume=5.0,
            driver_name=driver_name,
        )

    def get_vehicle_type(self) -> VehicleType:
        return VehicleType.VAN

    def can_transport(self, item: Item) -> Tuple[bool, str]:
        if item.get_item_type() == ItemType.PERISHABLE:
            return False, "รถตู้ทั่วไปไม่มีระบบควบคุมความเย็น ต้องใช้รถห้องเย็น (Refrigerated Truck)"
        if item.get_item_type() == ItemType.HAZARDOUS:
            return False, "รถตู้ทั่วไปไม่มีใบอนุญาตและอุปกรณ์ระงับภัยสารเคมี ต้องใช้รถบรรทุกที่ได้รับอนุญาต"
        return True, "สามารถจัดส่งด้วยรถตู้ทึบได้"


class RefrigeratedTruck(Vehicle):
    """
    รถบรรทุกห้องเย็น (Cold-Chain Logistics)
    - มีระบบควบคุมอุณหภูมิ (-25°C ถึง 10°C)
    - ออกแบบสำหรับ PERISHABLE โดยเฉพาะ และสามารถบรรทุก STANDARD ได้ด้วย
    - ไม่รับ HAZARDOUS เพื่อสุขอนามัย
    """

    def __init__(
        self,
        vehicle_id: str,
        license_plate: str,
        driver_name: str,
        min_temp_celsius: float = -20.0,
        max_temp_celsius: float = 8.0,
    ):
        super().__init__(
            vehicle_id=vehicle_id,
            license_plate=license_plate,
            max_weight=3500.0,
            max_volume=14.0,
            driver_name=driver_name,
        )
        self._min_temp = min_temp_celsius
        self._max_temp = max_temp_celsius

    @property
    def temperature_range(self) -> Tuple[float, float]:
        return (self._min_temp, self._max_temp)

    def get_vehicle_type(self) -> VehicleType:
        return VehicleType.REFRIGERATED_TRUCK

    def can_transport(self, item: Item) -> Tuple[bool, str]:
        if item.get_item_type() == ItemType.HAZARDOUS:
            return False, "ห้ามบรรทุกวัตถุอันตรายปะปนในรถห้องเย็นสำหรับอาหาร/ยา"

        if item.get_item_type() == ItemType.PERISHABLE:
            # ตรวจสอบอุณหภูมิที่สินค้าต้องการ
            req_temp = getattr(item, "target_temperature_celsius", 0.0)
            if req_temp < self._min_temp or req_temp > self._max_temp:
                return False, f"อุณหภูมิที่สินค้าต้องการ ({req_temp}°C) อยู่นอกช่วงที่รถทำได้ ({self._min_temp} ถึง {self._max_temp}°C)"

        return True, "สามารถจัดส่งด้วยรถห้องเย็นได้"


class HeavyTruck(Vehicle):
    """
    รถบรรทุกขนาดใหญ่ (10 ล้อ / ตู้คอนเทนเนอร์)
    - บรรทุกได้สูงสุด 15,000 กก., ปริมาตร 45.0 m³
    - ได้รับใบอนุญาตขนส่ง HAZARDOUS พร้อมอุปกรณ์นิรภัยครบถ้วน
    - บรรทุก STANDARD, FRAGILE (ขนาดใหญ่), HAZARDOUS ได้
    - ไม่แนะนำสำหรับ PERISHABLE เว้นแต่มีตู้แช่เฉพาะ
    """

    def __init__(self, vehicle_id: str, license_plate: str, driver_name: str, has_hazmat_permit: bool = True):
        super().__init__(
            vehicle_id=vehicle_id,
            license_plate=license_plate,
            max_weight=15000.0,
            max_volume=45.0,
            driver_name=driver_name,
        )
        self._has_hazmat_permit = has_hazmat_permit

    def get_vehicle_type(self) -> VehicleType:
        return VehicleType.HEAVY_TRUCK

    def can_transport(self, item: Item) -> Tuple[bool, str]:
        if item.get_item_type() == ItemType.HAZARDOUS:
            if not self._has_hazmat_permit:
                return False, "รถบรรทุกคันนี้ไม่มีใบอนุญาตขนส่งวัตถุอันตราย (Hazmat Permit)"
            return True, "รถบรรทุกคันนี้มีใบอนุญาตและอุปกรณ์นิรภัยสำหรับวัตถุอันตราย"

        if item.get_item_type() == ItemType.PERISHABLE:
            return False, "รถบรรทุกใหญ่คันนี้ไม่มีห้องเย็นควบคุมอุณหภูมิ"

        return True, "สามารถจัดส่งด้วยรถบรรทุกหนักได้"
