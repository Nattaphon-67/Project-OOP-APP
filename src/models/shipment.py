"""
Shipment, ShipmentStatus, and TrackingEvent Models
Demonstrating Composition, State Management, and OOP Design.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .customer import Customer
from .item import Item
from .vehicle import Vehicle
from ..strategies.pricing import PricingStrategy, StandardPricingStrategy


class ShipmentStatus(str, Enum):
    """สถานะของพัสดุในขั้นตอนการจัดส่ง (State Lifecycle)"""
    PENDING = "PENDING"                    # สร้างรายการแล้ว รอยืนยัน/จัดสรรรถ
    CONFIRMED = "CONFIRMED"                # ยืนยันรายการและรับเงินแล้ว
    VEHICLE_ASSIGNED = "VEHICLE_ASSIGNED"  # จัดสรรรถขนส่งเรียบร้อย
    IN_TRANSIT = "IN_TRANSIT"              # อยู่ระหว่างการขนส่งข้ามศูนย์คัดแยก
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"  # กำลังนำส่งให้ผู้รับ (พนักงานออกส่ง)
    DELIVERED = "DELIVERED"                # นำส่งสำเร็จเรียบร้อย
    CANCELLED = "CANCELLED"                # ยกเลิกรายการ


class TrackingEvent:
    """ประวัติการเคลื่อนไหวของพัสดุในแต่ละจุดตรวจ (Tracking Milestone)"""

    def __init__(self, status: ShipmentStatus, location: str, message: str, timestamp: Optional[str] = None):
        self._status = status
        self._location = location.strip()
        self._message = message.strip()
        self._timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def status(self) -> ShipmentStatus:
        return self._status

    @property
    def location(self) -> str:
        return self._location

    @property
    def message(self) -> str:
        return self._message

    @property
    def timestamp(self) -> str:
        return self._timestamp

    def to_dict(self) -> Dict[str, str]:
        return {
            "timestamp": self._timestamp,
            "status": self._status.value,
            "location": self._location,
            "message": self._message,
        }

    def __str__(self) -> str:
        return f"[{self._timestamp}] {self._status.value} @ {self._location}: {self._message}"


class Shipment:
    """
    คลาสรายการจัดส่งพัสดุ (Aggregate Root ในเชิง OOAD)
    รวบรวม Item, Customer (Sender/Receiver), Vehicle, และ PricingStrategy
    """

    def __init__(
        self,
        item: Item,
        sender: Customer,
        receiver: Customer,
        distance_km: float,
        pricing_strategy: Optional[PricingStrategy] = None,
        tracking_number: Optional[str] = None,
    ):
        self._tracking_number = tracking_number or f"TH{uuid.uuid4().hex[:10].upper()}"
        self._item = item
        self._sender = sender
        self._receiver = receiver
        self._distance_km = max(1.0, float(distance_km))
        self._pricing_strategy: PricingStrategy = pricing_strategy or StandardPricingStrategy()
        self._status = ShipmentStatus.PENDING
        self._assigned_vehicle: Optional[Vehicle] = None
        self._tracking_history: List[TrackingEvent] = []
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # บันทึกสถานะเริ่มต้น
        self.add_tracking_event(
            ShipmentStatus.PENDING,
            location="ศูนย์กระจายสินค้าต้นทาง",
            message=f"สร้างรายการพัสดุ {self._item.name} เข้าระบบ",
        )

    # --- Properties ---

    @property
    def tracking_number(self) -> str:
        return self._tracking_number

    @property
    def item(self) -> Item:
        return self._item

    @property
    def sender(self) -> Customer:
        return self._sender

    @property
    def receiver(self) -> Customer:
        return self._receiver

    @property
    def distance_km(self) -> float:
        return self._distance_km

    @property
    def pricing_strategy(self) -> PricingStrategy:
        return self._pricing_strategy

    @pricing_strategy.setter
    def pricing_strategy(self, strategy: PricingStrategy):
        self._pricing_strategy = strategy

    @property
    def status(self) -> ShipmentStatus:
        return self._status

    @property
    def assigned_vehicle(self) -> Optional[Vehicle]:
        return self._assigned_vehicle

    @property
    def tracking_history(self) -> List[TrackingEvent]:
        return list(self._tracking_history)

    @property
    def created_at(self) -> str:
        return self._created_at

    # --- Price Calculation (Strategy Pattern) ---

    def calculate_total_cost(self) -> float:
        """คำนวณราคาสุทธิโดยเรียกใช้ Strategy Pattern"""
        return self._pricing_strategy.calculate_cost(self._item, self._distance_km)

    def get_pricing_breakdown(self) -> Dict[str, Any]:
        """ดึงรายละเอียดการคิดเงิน"""
        return self._pricing_strategy.get_breakdown(self._item, self._distance_km)

    # --- Vehicle Assignment & Status Lifecycle ---

    def assign_vehicle(self, vehicle: Vehicle) -> Tuple[bool, str]:
        """
        จัดสรรและนำพัสดุขึ้นยานพาหนะ
        ตรวจสอบความเข้ากันได้ผ่านกฎ OOP ของยานพาหนะนั้นๆ
        """
        success, reason = vehicle.load_item(self._item)
        if not success:
            return False, reason

        self._assigned_vehicle = vehicle
        self.update_status(
            ShipmentStatus.VEHICLE_ASSIGNED,
            location=f"คลังสินค้า (ยานพาหนะทะเบียน {vehicle.license_plate})",
            message=f"จัดสรรขึ้นรถ [{vehicle.get_vehicle_type().value}] คนขับ: {vehicle.driver_name}",
        )
        return True, "จัดสรรยานพาหนะสำเร็จ"

    def update_status(self, new_status: ShipmentStatus, location: str, message: str) -> None:
        """อัปเดตสถานะพัสดุและบันทึกประวัติการติดตาม"""
        self._status = new_status
        self.add_tracking_event(new_status, location, message)

        # หากส่งสำเร็จ ให้นำของออกจากยานพาหนะ
        if new_status == ShipmentStatus.DELIVERED and self._assigned_vehicle:
            self._assigned_vehicle.unload_item(self._item.item_id)

    def add_tracking_event(self, status: ShipmentStatus, location: str, message: str) -> TrackingEvent:
        event = TrackingEvent(status, location, message)
        self._tracking_history.append(event)
        return event

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tracking_number": self._tracking_number,
            "status": self._status.value,
            "created_at": self._created_at,
            "distance_km": self._distance_km,
            "total_cost_thb": self.calculate_total_cost(),
            "service_type": self._pricing_strategy.get_strategy_name(),
            "estimated_delivery": self._pricing_strategy.get_estimated_delivery_time(),
            "item": self._item.to_dict(),
            "sender": self._sender.to_dict(),
            "receiver": self._receiver.to_dict(),
            "assigned_vehicle": self._assigned_vehicle.to_dict() if self._assigned_vehicle else None,
            "tracking_history": [event.to_dict() for event in self._tracking_history],
        }

    def __str__(self) -> str:
        return f"Shipment[{self._tracking_number}] - {self._item.name} -> {self._status.value}"
