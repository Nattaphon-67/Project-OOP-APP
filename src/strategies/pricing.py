"""
Pricing Strategy Pattern Implementation
Enables dynamic shipping price calculation based on service speed, distance, and item type.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models.item import Item


class PricingStrategy(ABC):
    """
    คลาสแม่แบบนามธรรมสำหรับกลยุทธ์การคำนวณราคา (Strategy Pattern)
    """

    @abstractmethod
    def calculate_cost(self, item: Item, distance_km: float) -> float:
        """คำนวณราคาสุทธิ (บาท) ตามประเภทสินค้าและระยะทาง"""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """ชื่อของประเภทบริการจัดส่ง"""
        pass

    @abstractmethod
    def get_estimated_delivery_time(self) -> str:
        """ระยะเวลาโดยประมาณในการจัดส่ง"""
        pass

    def get_breakdown(self, item: Item, distance_km: float) -> Dict[str, Any]:
        """สรุปแจกแจงรายละเอียดค่าบริการ"""
        handling_fee = item.calculate_handling_fee()
        total = self.calculate_cost(item, distance_km)
        transport_fee = round(total - handling_fee, 2)
        return {
            "strategy_name": self.get_strategy_name(),
            "estimated_delivery": self.get_estimated_delivery_time(),
            "distance_km": distance_km,
            "transport_fee_thb": transport_fee,
            "item_handling_fee_thb": handling_fee,
            "total_cost_thb": total,
        }


class StandardPricingStrategy(PricingStrategy):
    """
    บริการจัดส่งแบบธรรมดา (Standard Delivery)
    - ค่าส่งเริ่มต้น 40 บาท
    - อัตราค่าระยะทาง 3.50 บาท/กม.
    - ระยะเวลาจัดส่ง 2-3 วันทำการ
    """

    BASE_FEE = 40.0
    RATE_PER_KM = 3.5

    def calculate_cost(self, item: Item, distance_km: float) -> float:
        dist = max(1.0, float(distance_km))
        transport_fee = self.BASE_FEE + (dist * self.RATE_PER_KM)
        total = transport_fee + item.calculate_handling_fee()
        return round(total, 2)

    def get_strategy_name(self) -> str:
        return "Standard (ส่งธรรมดา 2-3 วัน)"

    def get_estimated_delivery_time(self) -> str:
        return "2 - 3 วันทำการ"


class ExpressPricingStrategy(PricingStrategy):
    """
    บริการจัดส่งแบบด่วนพิเศษ (Express Delivery)
    - ค่าส่งเริ่มต้น 70 บาท
    - อัตราค่าระยะทาง 6.00 บาท/กม.
    - ค่าบริการเร่งด่วน 50 บาท
    - ระยะเวลาจัดส่งภายใน 24 ชั่วโมง
    """

    BASE_FEE = 70.0
    RATE_PER_KM = 6.0
    PRIORITY_FEE = 50.0

    def calculate_cost(self, item: Item, distance_km: float) -> float:
        dist = max(1.0, float(distance_km))
        transport_fee = self.BASE_FEE + (dist * self.RATE_PER_KM) + self.PRIORITY_FEE
        total = transport_fee + item.calculate_handling_fee()
        return round(total, 2)

    def get_strategy_name(self) -> str:
        return "Express (ส่งด่วนภายใน 24 ชม.)"

    def get_estimated_delivery_time(self) -> str:
        return "ภายใน 24 ชั่วโมง (Next-Day)"


class SameDayPricingStrategy(PricingStrategy):
    """
    บริการจัดส่งด่วนพิเศษภายในวันเดียวกัน (Same-Day Delivery)
    - ค่าส่งเริ่มต้น 120 บาท
    - อัตราค่าระยะทาง 10.00 บาท/กม.
    - ค่าจัดสรรรอบรถทันที 100 บาท
    - ระยะเวลาจัดส่ง ภายใน 3 - 6 ชั่วโมง
    """

    BASE_FEE = 120.0
    RATE_PER_KM = 10.0
    INSTANT_DISPATCH_FEE = 100.0

    def calculate_cost(self, item: Item, distance_km: float) -> float:
        dist = max(1.0, float(distance_km))
        transport_fee = self.BASE_FEE + (dist * self.RATE_PER_KM) + self.INSTANT_DISPATCH_FEE
        total = transport_fee + item.calculate_handling_fee()
        return round(total, 2)

    def get_strategy_name(self) -> str:
        return "Same-Day (ส่งด่วนทันทีในวันเดียว)"

    def get_estimated_delivery_time(self) -> str:
        return "ภายใน 3 - 6 ชั่วโมง"
