"""
Item Model and Specialized Parcel Classes
Demonstrating OOP Abstraction, Inheritance, Encapsulation, and Polymorphism.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any


class ItemType(str, Enum):
    """ประเภทของพัสดุ/สินค้าในระบบ"""
    STANDARD = "STANDARD"          # พัสดุทั่วไป
    FRAGILE = "FRAGILE"            # พัสดุแตกหักง่าย
    PERISHABLE = "PERISHABLE"      # พัสดุควบคุมอุณหภูมิ/เน่าเสียง่าย
    HAZARDOUS = "HAZARDOUS"        # วัตถุอันตราย/สารเคมี


class CushioningLevel(str, Enum):
    """ระดับการกันกระแทกสำหรับสินค้าแตกหักง่าย"""
    STANDARD = "Standard"
    DOUBLE_LAYER = "Double Layer"
    WOODEN_CRATE = "Wooden Crate"


class Item(ABC):
    """
    คลาสแม่แบบนามธรรม (Abstract Base Class) สำหรับสินค้าและพัสดุทุกประเภท
    แสดงหลักการ Abstraction และ Encapsulation
    """

    def __init__(self, item_id: str, name: str, weight: float, volume: float, declared_value: float):
        self._item_id = item_id
        self.name = name                # ใช้ setter ตรวจสอบความถูกต้อง
        self.weight = weight            # ใช้ setter ตรวจสอบความถูกต้อง
        self.volume = volume            # ลูกบาศก์เมตร (m³)
        self.declared_value = declared_value  # มูลค่าสินค้า (บาท)

    # --- Encapsulation: Getters & Setters พร้อม Validation ---

    @property
    def item_id(self) -> str:
        return self._item_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value or not value.strip():
            raise ValueError("ชื่อสินค้าต้องไม่เป็นค่าว่าง")
        self._name = value.strip()

    @property
    def weight(self) -> float:
        """น้ำหนักสินค้า (กิโลกรัม)"""
        return self._weight

    @weight.setter
    def weight(self, value: float):
        if value <= 0:
            raise ValueError("น้ำหนักต้องมากกว่า 0 กิโลกรัม")
        self._weight = round(float(value), 3)

    @property
    def volume(self) -> float:
        """ปริมาตรสินค้า (ลูกบาศก์เมตร)"""
        return self._volume

    @volume.setter
    def volume(self, value: float):
        if value <= 0:
            raise ValueError("ปริมาตรต้องมากกว่า 0 m³")
        self._volume = round(float(value), 4)

    @property
    def declared_value(self) -> float:
        """มูลค่าที่แจ้งไว้ของสินค้า (บาท)"""
        return self._declared_value

    @declared_value.setter
    def declared_value(self, value: float):
        if value < 0:
            raise ValueError("มูลค่าสินค้าต้องไม่ติดลบ")
        self._declared_value = round(float(value), 2)

    # --- Polymorphic Methods ---

    @abstractmethod
    def get_item_type(self) -> ItemType:
        """คืนค่าประเภทของสินค้า (Polymorphism)"""
        pass

    @abstractmethod
    def calculate_handling_fee(self) -> float:
        """คำนวณค่าธรรมเนียมการจัดการเฉพาะของประเภทสินค้านั้นๆ (Polymorphism)"""
        pass

    @abstractmethod
    def get_special_requirements(self) -> str:
        """ข้อกำหนดพิเศษในการจัดส่งและการดูแลสินค้า"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """แปลงข้อมูลสินค้าเป็น Dictionary"""
        return {
            "item_id": self._item_id,
            "name": self._name,
            "item_type": self.get_item_type().value,
            "weight_kg": self._weight,
            "volume_m3": self._volume,
            "declared_value_thb": self._declared_value,
            "handling_fee_thb": self.calculate_handling_fee(),
            "special_requirements": self.get_special_requirements(),
        }

    def __str__(self) -> str:
        return f"[{self.get_item_type().value}] {self._name} ({self._weight} kg)"


class StandardParcel(Item):
    """
    พัสดุทั่วไป (เอกสาร เสื้อผ้า อุปกรณ์สำนักงาน ฯลฯ)
    ไม่มีเงื่อนไขอุณหภูมิหรือความเสี่ยงแตกหักเป็นพิเศษ
    """

    def __init__(self, item_id: str, name: str, weight: float, volume: float, declared_value: float = 0.0):
        super().__init__(item_id, name, weight, volume, declared_value)

    def get_item_type(self) -> ItemType:
        return ItemType.STANDARD

    def calculate_handling_fee(self) -> float:
        """พัสดุทั่วไปคิดค่าจัดการพื้นฐานตามน้ำหนัก (10 บาท/กก. ขั้นต่ำ 20 บาท)"""
        fee = self.weight * 10.0
        return max(20.0, round(fee, 2))

    def get_special_requirements(self) -> str:
        return "จัดส่งตามมาตรฐานทั่วไป ไม่ต้องใช้อุปกรณ์พิเศษ"


class FragileParcel(Item):
    """
    พัสดุแตกหักง่าย (แก้ว เซรามิก อุปกรณ์อิเล็กทรอนิกส์ หน้าจอ)
    ต้องมีการกันกระแทกพิเศษ และมีตัวเลือกทำประกันคุ้มครองสินค้า
    """

    def __init__(
        self,
        item_id: str,
        name: str,
        weight: float,
        volume: float,
        declared_value: float,
        cushioning_level: CushioningLevel = CushioningLevel.STANDARD,
        requires_insurance: bool = True,
    ):
        super().__init__(item_id, name, weight, volume, declared_value)
        self._cushioning_level = cushioning_level
        self._requires_insurance = requires_insurance

    @property
    def cushioning_level(self) -> CushioningLevel:
        return self._cushioning_level

    @cushioning_level.setter
    def cushioning_level(self, level: CushioningLevel):
        self._cushioning_level = level

    @property
    def requires_insurance(self) -> bool:
        return self._requires_insurance

    def get_item_type(self) -> ItemType:
        return ItemType.FRAGILE

    def calculate_handling_fee(self) -> float:
        """
        คำนวณค่าธรรมเนียมดูแลพัสดุแตกง่าย:
        - ค่าจัดการพื้นฐาน 50 บาท
        - ค่าวัสดุกันกระแทกตามระดับ
        - ค่าเบี้ยประกัน 1.5% ของมูลค่าสินค้า (หากเลือกทำประกัน)
        """
        base_fee = 50.0

        cushion_fees = {
            CushioningLevel.STANDARD: 30.0,
            CushioningLevel.DOUBLE_LAYER: 70.0,
            CushioningLevel.WOODEN_CRATE: 200.0,
        }
        cushion_fee = cushion_fees.get(self._cushioning_level, 30.0)

        insurance_fee = 0.0
        if self._requires_insurance:
            insurance_fee = self.declared_value * 0.015

        return round(base_fee + cushion_fee + insurance_fee, 2)

    def get_special_requirements(self) -> str:
        ins_str = "มีประกันสินค้า" if self._requires_insurance else "ไม่มีประกัน"
        return f"ระวังแตกหัก! ห้ามวางทับเกิน 2 ชั้น | แพ็กเกจ: {self._cushioning_level.value} | {ins_str}"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["cushioning_level"] = self._cushioning_level.value
        data["requires_insurance"] = self._requires_insurance
        return data


class PerishableParcel(Item):
    """
    พัสดุควบคุมอุณหภูมิ / เน่าเสียง่าย (อาหารสด ยา เวชภัณฑ์ ขนมสด)
    ต้องจัดส่งด้วยยานพาหนะห้องเย็น และมีกำหนดเวลาหมดอายุ
    """

    def __init__(
        self,
        item_id: str,
        name: str,
        weight: float,
        volume: float,
        declared_value: float,
        target_temperature_celsius: float,
        expiry_hours: int = 48,
    ):
        super().__init__(item_id, name, weight, volume, declared_value)
        self._target_temp = target_temperature_celsius
        self._expiry_hours = expiry_hours

    @property
    def target_temperature_celsius(self) -> float:
        return self._target_temp

    @property
    def expiry_hours(self) -> int:
        return self._expiry_hours

    def get_item_type(self) -> ItemType:
        return ItemType.PERISHABLE

    def calculate_handling_fee(self) -> float:
        """
        คำนวณค่าห้องเย็นและการรักษาอุณหภูมิ:
        - ค่าควบคุมความเย็นคงที่ 120 บาท
        - หากเป็นสินค้าแช่แข็ง (< 0 °C) เพิ่ม 80 บาท
        - สินค้าที่มีอายุสั้นกว่า 24 ชม. คิดค่าเร่งด่วนเพิ่ม 50 บาท
        """
        fee = 120.0
        if self._target_temp < 0.0:
            fee += 80.0  # Cold Chain Frozen surcharge
        if self._expiry_hours <= 24:
            fee += 50.0  # High urgency surcharge
        return round(fee, 2)

    def get_special_requirements(self) -> str:
        temp_str = f"ควบคุมอุณหภูมิที่ {self._target_temp}°C"
        if self._target_temp < 0:
            temp_str += " (แช่แข็ง Frozen)"
        else:
            temp_str += " (แช่เย็น Chilled)"
        return f"{temp_str} | ต้องส่งมอบภายใน {self._expiry_hours} ชม."

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["target_temperature_celsius"] = self._target_temp
        data["expiry_hours"] = self._expiry_hours
        return data


class HazardousParcel(Item):
    """
    พัสดุวัตถุอันตราย / สารเคมี / แบตเตอรี่ลิเธียม (Hazardous Goods)
    ต้องระบุรหัส UN และใบอนุญาตความปลอดภัย ขนส่งได้เฉพาะรถที่ได้รับอนุญาต
    """

    def __init__(
        self,
        item_id: str,
        name: str,
        weight: float,
        volume: float,
        declared_value: float,
        hazard_class: str,
        safety_license_id: str,
    ):
        super().__init__(item_id, name, weight, volume, declared_value)
        self._hazard_class = hazard_class
        self._safety_license_id = safety_license_id

    @property
    def hazard_class(self) -> str:
        return self._hazard_class

    @property
    def safety_license_id(self) -> str:
        return self._safety_license_id

    def get_item_type(self) -> ItemType:
        return ItemType.HAZARDOUS

    def calculate_handling_fee(self) -> float:
        """
        คำนวณค่าธรรมเนียมจัดการวัตถุอันตราย:
        - ค่าตรวจสอบเอกสารความปลอดภัย 150 บาท
        - ค่าดูแลพิเศษตามน้ำหนัก 25 บาท/กก.
        """
        fee = 150.0 + (self.weight * 25.0)
        return round(fee, 2)

    def get_special_requirements(self) -> str:
        return f"วัตถุอันตราย {self._hazard_class} | เลขที่อนุญาต: {self._safety_license_id} | ต้องมีถังดับเพลิงประจำรถ"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["hazard_class"] = self._hazard_class
        data["safety_license_id"] = self._safety_license_id
        return data
