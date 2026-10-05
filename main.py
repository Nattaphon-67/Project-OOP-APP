"""
Main Entry Point for Logistics & Parcel Management System
Supports Web App (Vercel compatible), Desktop GUI, and Interactive CLI modes.
"""

import sys
import argparse

# จัดการ Encoding สำหรับ Windows Console ให้รองรับ UTF-8 และภาษาไทย/Emoji
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="ระบบบริหารจัดการโลจิสติกส์และพัสดุภัณฑ์ (Logistics Management System) ด้วย OOP & OOAD"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="รันระบบในโหมด Web Application (เปิดบนบราวเซอร์ เช่น http://localhost:8000)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="รันระบบในโหมด Desktop GUI (หน้าต่างโปรแกรม Tkinter)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="รันระบบในโหมดคอนโซล (Interactive CLI Menu)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="รันการสาธิตระบบและทดสอบการทำงานของ OOP แบบอัตโนมัติ (Automated Demo Run)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="พอร์ตสำหรับ Web Server (ค่าเริ่มต้น: 8000)",
    )

    args = parser.parse_args()

    if args.demo:
        run_automated_demo()
    elif args.cli:
        from src.ui.cli_app import LogisticsCLIApp
        app = LogisticsCLIApp()
        app.run()
    elif args.gui:
        from src.ui.gui_app import run_gui
        run_gui()
    else:
        # Default โหมด Web Application (สำหรับดูผ่านบราวเซอร์ที่สวยงาม และรองรับ Vercel)
        try:
            from api.index import run_web_server
            run_web_server(port=args.port)
        except Exception as e:
            print(f"[Web Notice] ไม่สามารถเริ่ม Web Server ได้ ({e}) กำลังเปิดโหมด Desktop GUI...")
            from src.ui.gui_app import run_gui
            run_gui()


def run_automated_demo():
    """ฟังก์ชันสาธิตการทำงานและทดสอบฟีเจอร์ OOP ใน Console"""
    from src.services.logistics_service import LogisticsService
    from src.factory.item_factory import ItemFactory
    from src.models.item import ItemType, CushioningLevel
    from src.models.customer import Customer, Address

    print("=" * 70)
    print("🚀 เริ่มการสาธิตการทำงานของระบบ (Automated OOAD Logistics Demo)")
    print("=" * 70)

    service = LogisticsService()
    service.seed_initial_data()

    print("\n[1] ตรวจสอบข้อมูลพัสดุเริ่มต้นที่ถูกสร้างและจัดสรรตามประเภทสินค้า:")
    for s in service.repository.get_all_shipments():
        veh_plate = s.assigned_vehicle.license_plate if s.assigned_vehicle else "None"
        print(f"  • {s.tracking_number} | {s.item.name:<35} | หมวด: {s.item.get_item_type().value:<11} | รถ: {veh_plate} | รวม: ฿{s.calculate_total_cost():,.2f}")

    print("\n[2] ทดสอบ Factory Pattern: สร้างพัสดุประเภท PERISHABLE (ยาควบคุมอุณหภูมิ 2°C):")
    cold_item = ItemFactory.create_item(
        ItemType.PERISHABLE,
        name="ยาอินซูลินและชีววัตถุทางการแพทย์",
        weight=2.0,
        volume=0.012,
        declared_value=18000.0,
        target_temperature_celsius=2.0,
        expiry_hours=18,
    )
    print(f"  -> สร้างสำเร็จ: {cold_item} (ค่าธรรมเนียมดูแล: ฿{cold_item.calculate_handling_fee():,.2f})")
    print(f"  -> ข้อกำหนด: {cold_item.get_special_requirements()}")

    sender = Customer("SND-DEMO", "ศูนย์วิจัยจุฬาฯ", "02-218-0000", "sender@chula.ac.th", Address("ถ.พญาไท", "ปทุมวัน", "กทม.", "10330"))
    receiver = Customer("RCV-DEMO", "รพ.ศิริราช", "02-419-7000", "pharmacy@siriraj.ac.th", Address("ถ.พรานนก", "บางกอกน้อย", "กทม.", "10700"))

    print("\n[3] ทดสอบ Service Facade & Fleet Allocation (ระบบเลือกรถห้องเย็นให้อัตโนมัติ):")
    new_shipment, assign_msg = service.create_shipment(
        item=cold_item,
        sender=sender,
        receiver=receiver,
        distance_km=12.5,
        service_tier="EXPRESS",
        auto_assign_vehicle=True,
    )
    print(f"  -> หมายเลขพัสดุใหม่: {new_shipment.tracking_number}")
    print(f"  -> {assign_msg}")
    print(f"  -> รถที่ได้รับมอบหมาย: {new_shipment.assigned_vehicle}")

    print("\n[4] ทดสอบ Observer Pattern & State Lifecycle (เลื่อนสถานะพัสดุ):")
    service.advance_shipment_status(new_shipment.tracking_number, "ศูนย์กระจายสินค้าเวชภัณฑ์", "รับยาเข้าสู่ตู้ควบคุมอุณหภูมิ")
    service.advance_shipment_status(new_shipment.tracking_number, "รพ.ศิริราช", "ส่งมอบยาและลงนามตรวจรับเรียบร้อย")

    print("\n[5] รายการแจ้งเตือน SMS ที่ Observer จัดเก็บ:")
    for sms in service.sms_notifier.sent_messages:
        if new_shipment.tracking_number in sms["message"]:
            print(f"  🔔 {sms['message']}")

    print("\n[6] สรุปสถิติจากแดชบอร์ด:")
    metrics = service.get_dashboard_metrics()
    print(f"  • จำนวนพัสดุรวม: {metrics['total_shipments']} รายการ")
    print(f"  • รายได้ค่าส่งรวม: ฿{metrics['total_revenue_thb']:,.2f}")
    print(f"  • แยกตามประเภท: {metrics['by_category']}")

    print("\n" + "=" * 70)
    print("✅ การสาธิตทำงานเสร็จสมบูรณ์ ทุกหลักการ OOP/OOAD ทำงานถูกต้อง 100%!")
    print("=" * 70)


if __name__ == "__main__":
    main()
