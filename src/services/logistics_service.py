"""
Logistics Service (Facade Pattern)
Central coordinator combining items, vehicles, shipments, pricing, and notification events.
"""

from typing import List, Optional, Tuple, Dict, Any
from ..models.item import Item, ItemType, CushioningLevel
from ..models.vehicle import Motorcycle, Van, RefrigeratedTruck, HeavyTruck, Vehicle
from ..models.customer import Customer, Address
from ..models.shipment import Shipment, ShipmentStatus, TrackingEvent
from ..strategies.pricing import (
    PricingStrategy,
    StandardPricingStrategy,
    ExpressPricingStrategy,
    SameDayPricingStrategy,
)
from ..factory.item_factory import ItemFactory
from ..observers.notifier import (
    NotificationManager,
    CustomerSMSNotifier,
    CustomerEmailNotifier,
    SystemAuditLogger,
)
from ..storage.repository import LogisticsRepository
from .fleet_service import FleetService


class LogisticsService:
    """
    Facade Service รวมจุดเชื่อมต่อหลักสำหรับจัดการระบบขนส่งสินค้าทั้งหมด
    """

    def __init__(self, repository: Optional[LogisticsRepository] = None):
        self._repo = repository or LogisticsRepository()
        self._fleet = FleetService()
        self._notifier = NotificationManager()

        # สร้าง Observers เริ่มต้น
        self._sms_notifier = CustomerSMSNotifier()
        self._email_notifier = CustomerEmailNotifier()
        self._audit_logger = SystemAuditLogger()

        self._notifier.subscribe(self._sms_notifier)
        self._notifier.subscribe(self._email_notifier)
        self._notifier.subscribe(self._audit_logger)

    @property
    def fleet(self) -> FleetService:
        return self._fleet

    @property
    def repository(self) -> LogisticsRepository:
        return self._repo

    @property
    def audit_logger(self) -> SystemAuditLogger:
        return self._audit_logger

    @property
    def sms_notifier(self) -> CustomerSMSNotifier:
        return self._sms_notifier

    # --- Shipment Creation & Workflow ---

    def create_shipment(
        self,
        item: Item,
        sender: Customer,
        receiver: Customer,
        distance_km: float,
        service_tier: str = "STANDARD",
        auto_assign_vehicle: bool = True,
    ) -> Tuple[Shipment, str]:
        """
        สร้างรายการจัดส่งพัสดุใหม่ในระบบ
        """
        # เลือก Strategy ตามบริการ
        tier_upper = service_tier.upper()
        if "EXPRESS" in tier_upper:
            strategy: PricingStrategy = ExpressPricingStrategy()
        elif "SAME" in tier_upper:
            strategy = SameDayPricingStrategy()
        else:
            strategy = StandardPricingStrategy()

        shipment = Shipment(
            item=item,
            sender=sender,
            receiver=receiver,
            distance_km=distance_km,
            pricing_strategy=strategy,
        )

        self._repo.add_shipment(shipment)
        self._repo.add_customer(sender)
        self._repo.add_customer(receiver)

        msg = f"สร้างรายการพัสดุสำเร็จ หมายเลขติดตาม: {shipment.tracking_number}"

        # ส่งการแจ้งเตือนเริ่มต้น
        if shipment.tracking_history:
            self._notifier.notify(shipment, shipment.tracking_history[-1])

        # จัดสรรรถอัตโนมัติหากระบุ
        if auto_assign_vehicle:
            vehicle, assign_msg = self._fleet.find_best_vehicle(item)
            if vehicle:
                success, load_reason = shipment.assign_vehicle(vehicle)
                if success:
                    msg += f" | {assign_msg}"
                    self._notifier.notify(shipment, shipment.tracking_history[-1])
                else:
                    msg += f" | บรรทุกไม่สำเร็จ: {load_reason}"
            else:
                msg += f" | {assign_msg}"

        return shipment, msg

    def advance_shipment_status(
        self,
        tracking_number: str,
        location: str,
        message: str,
    ) -> Tuple[bool, str]:
        """
        เลื่อนสถานะพัสดุไปยังขั้นตอนถัดไปในวงจรชีวิต (Lifecycle Transition)
        """
        shipment = self._repo.get_shipment(tracking_number)
        if not shipment:
            return False, f"ไม่พบพัสดุหมายเลข {tracking_number}"

        # กำหนดลำดับสถานะ
        flow = [
            ShipmentStatus.PENDING,
            ShipmentStatus.CONFIRMED,
            ShipmentStatus.VEHICLE_ASSIGNED,
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.OUT_FOR_DELIVERY,
            ShipmentStatus.DELIVERED,
        ]

        current_idx = flow.index(shipment.status) if shipment.status in flow else -1
        if current_idx == -1 or current_idx >= len(flow) - 1:
            return False, f"พัสดุอยู่ในสถานะสุดท้ายแล้ว ({shipment.status.value})"

        # หากยังไม่ได้จัดสรรรถ และจะก้าวไป IN_TRANSIT ต้องมีรถก่อน
        next_status = flow[current_idx + 1]
        if next_status == ShipmentStatus.VEHICLE_ASSIGNED and not shipment.assigned_vehicle:
            vehicle, reason = self._fleet.find_best_vehicle(shipment.item)
            if not vehicle:
                return False, f"ไม่สามารถเลื่อนสถานะ: {reason}"
            shipment.assign_vehicle(vehicle)
            self._notifier.notify(shipment, shipment.tracking_history[-1])
            return True, f"จัดสรรรถ {vehicle.license_plate} และปรับสถานะเรียบร้อย"

        shipment.update_status(next_status, location, message)
        self._notifier.notify(shipment, shipment.tracking_history[-1])
        return True, f"อัปเดตสถานะพัสดุเป็น {next_status.value} เรียบร้อย"

    def manually_assign_vehicle(self, tracking_number: str, vehicle_id: str) -> Tuple[bool, str]:
        """มอบหมายยานพาหนะให้พัสดุด้วยตนเอง"""
        shipment = self._repo.get_shipment(tracking_number)
        if not shipment:
            return False, f"ไม่พบพัสดุ {tracking_number}"

        vehicle = self._fleet.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return False, f"ไม่พบยานพาหนะ {vehicle_id}"

        success, reason = shipment.assign_vehicle(vehicle)
        if success:
            self._notifier.notify(shipment, shipment.tracking_history[-1])
        return success, reason

    # --- Analytics & Reporting ---

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """คำนวณสถิติภาพรวมสำหรับ Dashboard"""
        all_shipments = self._repo.get_all_shipments()

        total_count = len(all_shipments)
        total_revenue = sum(s.calculate_total_cost() for s in all_shipments)

        # สถิติตามประเภทสินค้า
        by_category = {
            ItemType.STANDARD.value: 0,
            ItemType.FRAGILE.value: 0,
            ItemType.PERISHABLE.value: 0,
            ItemType.HAZARDOUS.value: 0,
        }
        for s in all_shipments:
            cat = s.item.get_item_type().value
            by_category[cat] = by_category.get(cat, 0) + 1

        # สถิติตามสถานะ
        by_status: Dict[str, int] = {}
        for s in all_shipments:
            st = s.status.value
            by_status[st] = by_status.get(st, 0) + 1

        fleet_stats = self._fleet.get_fleet_summary()

        return {
            "total_shipments": total_count,
            "total_revenue_thb": round(total_revenue, 2),
            "by_category": by_category,
            "by_status": by_status,
            "fleet_stats": fleet_stats,
        }

    # --- Seed Demo Data ---

    def seed_initial_data(self) -> None:
        """เตรียมข้อมูลจำลองสำหรับทดสอบระบบทันทีหลังเปิดโปรแกรม"""
        # 1. เพิ่มยานพาหนะประเภทต่างๆ เข้าคลัง
        v1 = Motorcycle("V-M01", "1กก-4512 กทม.", "สมชาย ว่องไว")
        v2 = Motorcycle("V-M02", "3ขข-8921 กทม.", "ประสิทธิ์ รวดเร็ว")
        v3 = Van("V-VAN01", "ฒฮ-1234 กทม.", "วิชัย ปลอดภัย")
        v4 = Van("V-VAN02", "ฒฮ-5678 กทม.", "เกรียงไกร ขนส่ง")
        v5 = RefrigeratedTruck("V-COLD01", "70-9901 นครปฐม", "ธีระพล เย็นฉ่ำ", min_temp_celsius=-20.0, max_temp_celsius=6.0)
        v6 = HeavyTruck("V-HVY01", "71-3322 ชลบุรี", "สุรศักดิ์ ทรงพลัง", has_hazmat_permit=True)

        for v in [v1, v2, v3, v4, v5, v6]:
            self._fleet.register_vehicle(v)
            self._repo.add_vehicle(v)

        # 2. ลูกค้าตัวอย่าง
        c1 = Customer("CUST-01", "บริษัท สยามเปเปอร์ จำกัด", "081-111-2233", "sender1@siampaper.co.th",
                      Address("99 ถ.สาทรใต้", "สาทร", "กรุงเทพฯ", "10120"))
        c2 = Customer("CUST-02", "คุณกานดา สุขสม", "089-444-5566", "kanda.s@gmail.com",
                      Address("12/4 ซอยอารีย์ 3", "พญาไท", "กรุงเทพฯ", "10400"))
        c3 = Customer("CUST-03", "โรงพยาบาลกรุงเทพเมดิคอล", "02-777-8899", "pharmacy@bkmedical.com",
                      Address("45 ถ.เพชรบุรีตัดใหม่", "ห้วยขวาง", "กรุงเทพฯ", "10310"))
        c4 = Customer("CUST-04", "สถาบันวิจัยเคมีอุตสาหกรรม", "038-222-333", "lab@chemresearch.or.th",
                      Address("88 นิคมฯ แหลมฉบัง", "ศรีราชา", "ชลบุรี", "20230"))

        # 3. สินค้า 4 ประเภทที่แยกคุณสมบัติชัดเจน (ผ่าน ItemFactory)
        item_std = ItemFactory.create_item(
            ItemType.STANDARD,
            name="เอกสารสัญญากฎหมายและแคตตาล็อก",
            weight=2.5,
            volume=0.005,
            declared_value=500.0,
        )

        item_fragile = ItemFactory.create_item(
            ItemType.FRAGILE,
            name="ชุดแจกันเซรามิกเบญจรงค์",
            weight=4.0,
            volume=0.035,
            declared_value=12500.0,
            cushioning_level=CushioningLevel.DOUBLE_LAYER,
            requires_insurance=True,
        )

        item_perishable = ItemFactory.create_item(
            ItemType.PERISHABLE,
            name="วัคซีนและยาควบคุมความเย็นชีววัตถุ",
            weight=3.2,
            volume=0.020,
            declared_value=35000.0,
            target_temperature_celsius=4.0,
            expiry_hours=24,
        )

        item_hazardous = ItemFactory.create_item(
            ItemType.HAZARDOUS,
            name="สารทำละลายอินทรีย์สำหรับงานวิเคราะห์ (Ethanol AR)",
            weight=18.0,
            volume=0.060,
            declared_value=8500.0,
            hazard_class="Class 3 (Flammable Liquids)",
            safety_license_id="HAZ-UN1170-BKK",
        )

        # 4. สร้าง Shipments จำลอง
        s1, _ = self.create_shipment(item_std, c1, c2, distance_km=15.0, service_tier="EXPRESS")
        s2, _ = self.create_shipment(item_fragile, c2, c1, distance_km=25.0, service_tier="STANDARD")
        s3, _ = self.create_shipment(item_perishable, c1, c3, distance_km=18.0, service_tier="SAME_DAY")
        s4, _ = self.create_shipment(item_hazardous, c4, c1, distance_km=85.0, service_tier="STANDARD")

        # ปรับสถานะบางรายการให้สมจริง
        self.advance_shipment_status(s1.tracking_number, "ศูนย์กระจายสินค้าดอนเมือง", "พัสดุกำลังขนส่งสู่สาขาปลายทาง")
        self.advance_shipment_status(s1.tracking_number, "จุดส่งมอบปลายทาง", "พนักงานนำจ่ายกำลังจัดส่งถึงบ้านผู้รับ")
