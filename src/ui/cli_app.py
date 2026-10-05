"""
Interactive Console / CLI Menu for Logistics System
Provides complete terminal interface for managing items, vehicles, and shipments.
"""

import sys
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from ..models.item import ItemType, CushioningLevel
from ..models.customer import Customer, Address
from ..services.logistics_service import LogisticsService
from ..factory.item_factory import ItemFactory


class LogisticsCLIApp:
    """
    เมนูคอนโซลแบบโต้ตอบ (Interactive Terminal UI)
    สำหรับผู้ใช้งานผ่าน Terminal หรือการนำเสนอการทำงานแบบ CLI
    """

    def __init__(self, service: Optional[LogisticsService] = None):
        self.service = service or LogisticsService()
        self.service.seed_initial_data()

    def run(self):
        while True:
            self._print_header()
            print("1. ➕ สร้างรายการพัสดุและจัดสรรยานพาหนะ (New Shipment)")
            print("2. 📋 ดูรายการพัสดุทั้งหมดในระบบ (List All Shipments)")
            print("3. 🔍 ค้นหาและติดตามสถานะพัสดุ (Track Shipment)")
            print("4. ⏩ ปรับเลื่อนสถานะพัสดุสู่จุดถัดไป (Advance Status)")
            print("5. 🚚 ดูสถานะกองยานพาหนะและการบรรทุก (Fleet Status)")
            print("6. 📊 ดูสถิติและภาพรวมระบบ (Analytics & Dashboard)")
            print("7. 💾 ส่งออกข้อมูลสำรองเป็นไฟล์ JSON (Export Data)")
            print("0. 🚪 ออกจากโปรแกรม (Exit)")
            print("-" * 65)

            choice = input("กรุณาเลือกเมนู (0-7): ").strip()
            if choice == "1":
                self._handle_create_shipment()
            elif choice == "2":
                self._handle_list_shipments()
            elif choice == "3":
                self._handle_track_shipment()
            elif choice == "4":
                self._handle_advance_status()
            elif choice == "5":
                self._handle_fleet_status()
            elif choice == "6":
                self._handle_analytics()
            elif choice == "7":
                self._handle_export()
            elif choice == "0":
                print("\nขอบคุณที่ใช้งานระบบ Logistics Management System สวัสดีครับ! 🙏\n")
                break
            else:
                print("❌ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")

    def _print_header(self):
        print("\n" + "=" * 65)
        print("     📦 ระบบบริหารจัดการขนส่งและพัสดุ (Logistics Management)     ")
        print("          [OOP & OOAD Architecture Implementation]          ")
        print("=" * 65)

    def _handle_create_shipment(self):
        print("\n--- สร้างรายการพัสดุใหม่ ---")
        print("เลือกประเภทสินค้า:")
        print("  1. STANDARD   - พัสดุทั่วไป (เอกสาร, เสื้อผ้า)")
        print("  2. FRAGILE    - สินค้าแตกหักง่าย (แก้ว, อุปกรณ์อิเล็กทรอนิกส์)")
        print("  3. PERISHABLE - สินค้าเน่าเสียง่าย/ควบคุมอุณหภูมิ (อาหารสด, ยา)")
        print("  4. HAZARDOUS  - วัตถุอันตราย/สารเคมี")
        type_choice = input("เลือกประเภท (1-4): ").strip()

        type_map = {
            "1": ItemType.STANDARD,
            "2": ItemType.FRAGILE,
            "3": ItemType.PERISHABLE,
            "4": ItemType.HAZARDOUS,
        }
        item_type = type_map.get(type_choice, ItemType.STANDARD)

        name = input("ชื่อสินค้า: ").strip() or "พัสดุไม่มีชื่อ"
        try:
            weight = float(input("น้ำหนัก (กก.): ").strip() or "1.0")
            volume = float(input("ปริมาตร (m³): ").strip() or "0.01")
            value = float(input("มูลค่าสินค้า (บาท): ").strip() or "500")
        except ValueError:
            print("❌ ข้อมูลตัวเลขไม่ถูกต้อง ยกเลิกการสร้าง")
            return

        kwargs = {
            "name": name,
            "weight": weight,
            "volume": volume,
            "declared_value": value,
        }

        if item_type == ItemType.FRAGILE:
            print("ระดับกันกระแทก: 1. Standard  2. Double Layer  3. Wooden Crate")
            c_choice = input("เลือกระดับ (1-3): ").strip()
            c_map = {"1": CushioningLevel.STANDARD, "2": CushioningLevel.DOUBLE_LAYER, "3": CushioningLevel.WOODEN_CRATE}
            kwargs["cushioning_level"] = c_map.get(c_choice, CushioningLevel.DOUBLE_LAYER)
            ins_input = input("ทำประกันคุ้มครองสินค้าหรือไม่? (y/n): ").strip().lower()
            kwargs["requires_insurance"] = ins_input != "n"

        elif item_type == ItemType.PERISHABLE:
            try:
                temp = float(input("อุณหภูมิควบคุมที่ต้องการ (°C): ").strip() or "4.0")
                exp = int(input("อายุสินค้าก่อนหมดอายุ (ชม.): ").strip() or "24")
                kwargs["target_temperature_celsius"] = temp
                kwargs["expiry_hours"] = exp
            except ValueError:
                kwargs["target_temperature_celsius"] = 4.0
                kwargs["expiry_hours"] = 24

        elif item_type == ItemType.HAZARDOUS:
            kwargs["hazard_class"] = input("คลาสอันตราย (เช่น Class 3): ").strip() or "Class 3"
            kwargs["safety_license_id"] = input("เลขที่ใบอนุญาตความปลอดภัย: ").strip() or "HAZ-CLI-01"

        item = ItemFactory.create_item(item_type, **kwargs)

        print("\n--- ข้อมูลผู้ส่งและผู้รับ ---")
        s_name = input("ชื่อผู้ส่ง: ").strip() or "ผู้ส่งไม่ระบุชื่อ"
        s_phone = input("เบอร์โทรผู้ส่ง: ").strip() or "080-000-0000"
        r_name = input("ชื่อผู้รับ: ").strip() or "ผู้รับไม่ระบุชื่อ"
        r_phone = input("เบอร์โทรผู้รับ: ").strip() or "089-999-9999"
        r_addr = input("ที่อยู่ปลายทาง: ").strip() or "กรุงเทพมหานคร"

        try:
            dist = float(input("ระยะทางจัดส่ง (กม.): ").strip() or "15.0")
        except ValueError:
            dist = 15.0

        print("ระดับบริการ: 1. STANDARD (2-3 วัน)  2. EXPRESS (24 ชม.)  3. SAME_DAY (วันเดียว)")
        tier_choice = input("เลือกระดับ (1-3): ").strip()
        tier_map = {"1": "STANDARD", "2": "EXPRESS", "3": "SAME_DAY"}
        service_tier = tier_map.get(tier_choice, "STANDARD")

        sender = Customer("SND-CLI", s_name, s_phone, "sender@mail.com", Address("ต้นทาง", "เขตกลาง", "กรุงเทพฯ", "10100"))
        receiver = Customer("RCV-CLI", r_name, r_phone, "receiver@mail.com", Address(r_addr, "ปลายทาง", "จังหวัด", "10200"))

        shipment, msg = self.service.create_shipment(
            item=item,
            sender=sender,
            receiver=receiver,
            distance_km=dist,
            service_tier=service_tier,
            auto_assign_vehicle=True,
        )

        print("\n✅ บันทึกรายการสำเร็จ!")
        print(f"หมายเลขพัสดุ (Tracking Number): {shipment.tracking_number}")
        print(f"ค่าส่งรวม: ฿{shipment.calculate_total_cost():,.2f}")
        print(f"ผลการจัดสรรรถ: {msg}")

    def _handle_list_shipments(self):
        print("\n--- รายการพัสดุทั้งหมดในระบบ ---")
        shipments = self.service.repository.get_all_shipments()
        if not shipments:
            print("ไม่มีพัสดุในระบบ")
            return

        header = f"{'Tracking #':<16} | {'ชื่อสินค้า':<24} | {'ประเภท':<12} | {'ค่าส่ง (บาท)':<12} | {'สถานะ':<15}"
        print(header)
        print("-" * len(header))
        for s in shipments:
            print(
                f"{s.tracking_number:<16} | {s.item.name[:22]:<24} | {s.item.get_item_type().value:<12} | "
                f"{s.calculate_total_cost():>10,.2f} | {s.status.value:<15}"
            )

    def _handle_track_shipment(self):
        track_no = input("\nกรอกหมายเลขพัสดุที่ต้องการค้นหา: ").strip().upper()
        shipment = self.service.repository.get_shipment(track_no)
        if not shipment:
            print(f"❌ ไม่พบพัสดุหมายเลข {track_no}")
            return

        print("\n" + "=" * 55)
        print(f"📦 รายละเอียดพัสดุ: {shipment.tracking_number}")
        print(f"   สถานะปัจจุบัน: {shipment.status.value}")
        print(f"   สินค้า: {shipment.item.name} ({shipment.item.get_item_type().value})")
        print(f"   น้ำหนัก: {shipment.item.weight} กก. | ปริมาตร: {shipment.item.volume} m³")
        print(f"   ข้อกำหนดพิเศษ: {shipment.item.get_special_requirements()}")
        print(f"   บริการ: {shipment.pricing_strategy.get_strategy_name()}")
        print(f"   ค่าจัดส่ง: ฿{shipment.calculate_total_cost():,.2f}")
        print(f"   ผู้รับ: {shipment.receiver.name} ({shipment.receiver.phone})")
        print(f"   ที่อยู่: {shipment.receiver.address}")
        if shipment.assigned_vehicle:
            v = shipment.assigned_vehicle
            print(f"   ยานพาหนะ: [{v.get_vehicle_type().value}] ทะเบียน {v.license_plate} (คนขับ: {v.driver_name})")
        else:
            print("   ยานพาหนะ: ยังไม่จัดสรร")

        print("\n📍 ไทม์ไลน์การเดินทาง:")
        for i, ev in enumerate(shipment.tracking_history, 1):
            print(f"   {i}. [{ev.timestamp}] {ev.status.value} @ {ev.location} - {ev.message}")
        print("=" * 55)

    def _handle_advance_status(self):
        track_no = input("\nกรอกหมายเลขพัสดุที่ต้องการเลื่อนสถานะ: ").strip().upper()
        loc = input("สถานที่ปัจจุบัน (Enter เพื่อใช้ค่ามาตรฐาน): ").strip() or "ศูนย์กระจายสินค้าปลายทาง"
        msg = input("หมายเหตุ/ข้อความ (Enter เพื่อใช้ค่ามาตรฐาน): ").strip() or "ผ่านการตรวจสอบและอยู่ระหว่างขั้นตอนถัดไป"

        success, res_msg = self.service.advance_shipment_status(track_no, loc, msg)
        if success:
            print(f"✅ {res_msg}")
        else:
            print(f"❌ {res_msg}")

    def _handle_fleet_status(self):
        print("\n--- สถานะกองยานพาหนะและการบรรทุก ---")
        vehicles = self.service.fleet.get_all_vehicles()
        for v in vehicles:
            print(
                f"• [{v.get_vehicle_type().value}] ทะเบียน: {v.license_plate} | คนขับ: {v.driver_name} | "
                f"บรรทุก: {v.current_weight_load():.1f}/{v.max_weight:.1f} กก. ({v.get_utilization_percentage()}%) | "
                f"จำนวนพัสดุ: {len(v.loaded_items)} ชิ้น"
            )
            if v.loaded_items:
                for it in v.loaded_items:
                    print(f"    - {it.name} ({it.get_item_type().value}, {it.weight}kg)")

    def _handle_analytics(self):
        metrics = self.service.get_dashboard_metrics()
        print("\n--- แดชบอร์ดสรุปผลภาพรวม ---")
        print(f"📦 จำนวนพัสดุทั้งหมด: {metrics['total_shipments']} ชิ้น")
        print(f"💰 รายได้ค่าจัดส่งรวม: ฿{metrics['total_revenue_thb']:,.2f}")

        print("\n🏷️ การกระจายตัวตามประเภทสินค้า:")
        for cat, cnt in metrics["by_category"].items():
            print(f"   • {cat:<12}: {cnt} ชิ้น")

        print("\n📌 การกระจายตัวตามสถานะ:")
        for st, cnt in metrics["by_status"].items():
            print(f"   • {st:<16}: {cnt} ชิ้น")

        fleet = metrics["fleet_stats"]
        print(f"\n🚚 อัตราบรรทุกกองยานพาหนะเฉลี่ย: {fleet['avg_utilization_pct']}%")

    def _handle_export(self):
        try:
            path = self.service.repository.export_to_json("shipments_data.json")
            print(f"✅ ส่งออกข้อมูลไปยังไฟล์ {path} เรียบร้อยแล้ว")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
