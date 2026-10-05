"""
Modern, Beautiful Desktop GUI for Logistics & Parcel Management System
Implemented using standard Tkinter & TTK with a modern card-based theme and clean typography.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

from ..models.item import ItemType, CushioningLevel
from ..models.customer import Customer, Address
from ..models.shipment import ShipmentStatus
from ..services.logistics_service import LogisticsService
from ..factory.item_factory import ItemFactory


class LogisticsGUIApp:
    """
    หน้าต่างโปรแกรม Desktop GUI ระบบบริหารจัดการโลจิสติกส์และการขนส่งสินค้า
    ออกแบบ UI ให้สวยงาม อ่านง่าย แยกหมวดหมู่สินค้าชัดเจน
    """

    def __init__(self, root: tk.Tk, service: Optional[LogisticsService] = None):
        self.root = root
        self.service = service or LogisticsService()
        self.service.seed_initial_data()  # เตรียมข้อมูลตัวอย่างให้พร้อมใช้งานทันที

        self._setup_window()
        self._setup_styles()
        self._build_header()
        self._build_notebook()

    def _setup_window(self):
        self.root.title("ระบบบริหารจัดการขนส่งและพัสดุภัณฑ์ (Logistics & Parcel Management)")
        self.root.geometry("1180x780")
        self.root.minsize(1050, 700)
        self.root.configure(bg="#f1f5f9")

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # กำหนด Palette สไตล์ Modern Dashboard
        self.COLOR_BG = "#f1f5f9"
        self.COLOR_CARD = "#ffffff"
        self.COLOR_PRIMARY = "#2563eb"
        self.COLOR_PRIMARY_HOVER = "#1d4ed8"
        self.COLOR_TEXT = "#0f172a"
        self.COLOR_TEXT_MUTED = "#64748b"
        self.COLOR_BORDER = "#cbd5e1"

        # Fonts
        self.FONT_HEADER = ("Segoe UI", 16, "bold")
        self.FONT_SUBHEADER = ("Segoe UI", 12, "bold")
        self.FONT_BODY = ("Segoe UI", 10)
        self.FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
        self.FONT_SMALL = ("Segoe UI", 9)
        self.FONT_BADGE = ("Segoe UI", 9, "bold")

        # Config ttk widget styles
        style.configure("TNotebook", background=self.COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[16, 8], background="#e2e8f0")
        style.map("TNotebook.Tab",
                  background=[("selected", self.COLOR_PRIMARY), ("active", "#93c5fd")],
                  foreground=[("selected", "#ffffff"), ("active", "#0f172a")])

        style.configure("Card.TFrame", background=self.COLOR_CARD, relief="flat")
        style.configure("Treeview", font=self.FONT_BODY, rowheight=28)
        style.configure("Treeview.Heading", font=self.FONT_BODY_BOLD, background="#e2e8f0")
        style.map("Treeview", background=[("selected", "#bfdbfe")], foreground=[("selected", "#1e3a8a")])

        style.configure("Primary.TButton", font=self.FONT_BODY_BOLD, background=self.COLOR_PRIMARY, foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", self.COLOR_PRIMARY_HOVER)])

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg="#1e293b", height=70)
        header_frame.pack(fill="x", side="top")

        title_label = tk.Label(
            header_frame,
            text="📦 LOGISTICS & PARCEL MANAGEMENT SYSTEM",
            font=self.FONT_HEADER,
            fg="#ffffff",
            bg="#1e293b",
        )
        title_label.pack(side="left", padx=24, pady=14)

        subtitle_label = tk.Label(
            header_frame,
            text="ระบบบริหารจัดการพัสดุและขนส่งแยกประเภท (OOP & OOAD Architecture)",
            font=self.FONT_SMALL,
            fg="#94a3b8",
            bg="#1e293b",
        )
        subtitle_label.pack(side="left", padx=4, pady=18)

        # ปุ่ม Export JSON สำรองข้อมูล
        export_btn = tk.Button(
            header_frame,
            text="💾 ส่งออกข้อมูล JSON",
            font=self.FONT_SMALL,
            bg="#334155",
            fg="#ffffff",
            relief="flat",
            activebackground="#475569",
            activeforeground="#ffffff",
            padx=12,
            pady=4,
            command=self._export_data,
        )
        export_btn.pack(side="right", padx=24, pady=16)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=12)

        # Tab 1: สร้างพัสดุใหม่ (New Shipment)
        self.tab_new = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_new, text="  ➕ สร้างรายการพัสดุ  ")
        self._build_tab_new_shipment()

        # Tab 2: ตารางพัสดุทั้งหมด (Shipment List)
        self.tab_list = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_list, text="  📋 รายการพัสดุในระบบ  ")
        self._build_tab_shipment_list()

        # Tab 3: ติดตามพัสดุ (Tracking & Status)
        self.tab_track = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_track, text="  🔍 ติดตามสถานะ (Tracking)  ")
        self._build_tab_tracking()

        # Tab 4: ข้อมูลยานพาหนะ (Fleet Management)
        self.tab_fleet = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fleet, text="  🚚 คลังยานพาหนะ (Fleet)  ")
        self._build_tab_fleet()

        # Tab 5: แดชบอร์ดสรุปผล (Analytics)
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="  📊 สรุปภาพรวมและสถิติ  ")
        self._build_tab_analytics()

        # Event เมื่อสลับแท็บให้อัปเดตข้อมูลอัตโนมัติ
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    # -------------------------------------------------------------
    # TAB 1: สร้างรายการพัสดุใหม่ (New Shipment)
    # -------------------------------------------------------------
    def _build_tab_new_shipment(self):
        container = tk.Frame(self.tab_new, bg=self.COLOR_BG)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # 2 Columns Layout
        left_col = tk.Frame(container, bg=self.COLOR_BG)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right_col = tk.Frame(container, bg=self.COLOR_BG)
        right_col.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # --- กล่องที่ 1: ข้อมูลลูกค้า (Sender & Receiver) ---
        cust_card = tk.LabelFrame(
            left_col, text=" 👤 ข้อมูลผู้ส่งและผู้รับ ",
            font=self.FONT_SUBHEADER, bg=self.COLOR_CARD, fg=self.COLOR_TEXT, padx=14, pady=10
        )
        cust_card.pack(fill="x", pady=(0, 10))

        # ผู้ส่ง
        tk.Label(cust_card, text="ชื่อผู้ส่ง:", font=self.FONT_BODY_BOLD, bg=self.COLOR_CARD).grid(row=0, column=0, sticky="w", pady=3)
        self.ent_sender_name = ttk.Entry(cust_card, width=28)
        self.ent_sender_name.insert(0, "บริษัท นวัตกรรมไทย จำกัด")
        self.ent_sender_name.grid(row=0, column=1, sticky="w", pady=3)

        tk.Label(cust_card, text="เบอร์ผู้ส่ง:", font=self.FONT_BODY, bg=self.COLOR_CARD).grid(row=0, column=2, sticky="w", padx=(10, 0), pady=3)
        self.ent_sender_phone = ttk.Entry(cust_card, width=16)
        self.ent_sender_phone.insert(0, "081-999-8877")
        self.ent_sender_phone.grid(row=0, column=3, sticky="w", pady=3)

        # ผู้รับ
        tk.Label(cust_card, text="ชื่อผู้รับ:", font=self.FONT_BODY_BOLD, bg=self.COLOR_CARD).grid(row=1, column=0, sticky="w", pady=3)
        self.ent_receiver_name = ttk.Entry(cust_card, width=28)
        self.ent_receiver_name.insert(0, "สมศรี วิเศษการ")
        self.ent_receiver_name.grid(row=1, column=1, sticky="w", pady=3)

        tk.Label(cust_card, text="เบอร์ผู้รับ:", font=self.FONT_BODY, bg=self.COLOR_CARD).grid(row=1, column=2, sticky="w", padx=(10, 0), pady=3)
        self.ent_receiver_phone = ttk.Entry(cust_card, width=16)
        self.ent_receiver_phone.insert(0, "089-123-4567")
        self.ent_receiver_phone.grid(row=1, column=3, sticky="w", pady=3)

        # ที่อยู่จัดส่งปลายทาง
        tk.Label(cust_card, text="ที่อยู่ปลายทาง:", font=self.FONT_BODY, bg=self.COLOR_CARD).grid(row=2, column=0, sticky="w", pady=3)
        self.ent_receiver_addr = ttk.Entry(cust_card, width=54)
        self.ent_receiver_addr.insert(0, "456 ถ.มิตรภาพ อ.เมือง จ.นครราชสีมา 30000")
        self.ent_receiver_addr.grid(row=2, column=1, columnspan=3, sticky="w", pady=3)

        # --- กล่องที่ 2: บริการจัดส่งและระยะทาง ---
        deliv_card = tk.LabelFrame(
            left_col, text=" 🚀 ระดับบริการจัดส่ง & ระยะทาง (Strategy Pattern) ",
            font=self.FONT_SUBHEADER, bg=self.COLOR_CARD, fg=self.COLOR_TEXT, padx=14, pady=10
        )
        deliv_card.pack(fill="x", pady=(0, 10))

        tk.Label(deliv_card, text="ระยะทางขนส่ง (กม.):", font=self.FONT_BODY_BOLD, bg=self.COLOR_CARD).grid(row=0, column=0, sticky="w", pady=4)
        self.ent_distance = ttk.Entry(deliv_card, width=12)
        self.ent_distance.insert(0, "35.0")
        self.ent_distance.grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(deliv_card, text="ประเภทความเร็ว:", font=self.FONT_BODY_BOLD, bg=self.COLOR_CARD).grid(row=1, column=0, sticky="w", pady=4)
        self.combo_service = ttk.Combobox(
            deliv_card,
            values=["STANDARD (ส่งธรรมดา 2-3 วัน)", "EXPRESS (ส่งด่วนภายใน 24 ชม.)", "SAME_DAY (ส่งด่วนทันทีวันเดียว)"],
            state="readonly",
            width=32,
        )
        self.combo_service.current(1)
        self.combo_service.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)
        self.combo_service.bind("<<ComboboxSelected>>", lambda e: self._update_price_preview())
        self.ent_distance.bind("<KeyRelease>", lambda e: self._update_price_preview())

        # --- กล่องที่ 3 (ฝั่งขวา): รายละเอียดและคุณสมบัติสินค้า (Item & Classification) ---
        item_card = tk.LabelFrame(
            right_col, text=" 📦 การจำแนกประเภทสินค้า (Item Classification) ",
            font=self.FONT_SUBHEADER, bg=self.COLOR_CARD, fg=self.COLOR_TEXT, padx=14, pady=10
        )
        item_card.pack(fill="both", expand=True)

        tk.Label(item_card, text="เลือกประเภทสินค้า:", font=self.FONT_BODY_BOLD, bg=self.COLOR_CARD, fg=self.COLOR_PRIMARY).grid(row=0, column=0, sticky="w", pady=4)
        self.combo_item_type = ttk.Combobox(
            item_card,
            values=[
                "STANDARD (สินค้าทั่วไป เช่น เอกสาร เสื้อผ้า)",
                "FRAGILE (แตกหักง่าย เช่น แก้ว เซรามิก อิเล็กทรอนิกส์)",
                "PERISHABLE (ควบคุมอุณหภูมิ เช่น อาหารสด ยา เวชภัณฑ์)",
                "HAZARDOUS (วัตถุอันตราย เช่น สารเคมี แบตเตอรี่)",
            ],
            state="readonly",
            width=42,
        )
        self.combo_item_type.current(0)
        self.combo_item_type.grid(row=0, column=1, sticky="w", pady=4)
        self.combo_item_type.bind("<<ComboboxSelected>>", self._on_item_type_changed)

        # ฟิลด์ทั่วไป
        tk.Label(item_card, text="ชื่อสินค้า/พัสดุ:", font=self.FONT_BODY, bg=self.COLOR_CARD).grid(row=1, column=0, sticky="w", pady=3)
        self.ent_item_name = ttk.Entry(item_card, width=32)
        self.ent_item_name.insert(0, "กล่องพัสดุอุปกรณ์สำนักงาน")
        self.ent_item_name.grid(row=1, column=1, sticky="w", pady=3)

        tk.Label(item_card, text="น้ำหนัก (กก.):", font=self.FONT_BODY, bg=self.COLOR_CARD).grid(row=2, column=0, sticky="w", pady=3)
        self.ent_item_weight = ttk.Entry(item_card, width=14)
        self.ent_item_weight.insert(0, "3.5")
        self.ent_item_weight.grid(row=2, column=1, sticky="w", pady=3)
        self.ent_item_weight.bind("<KeyRelease>", lambda e: self._update_price_preview())

        tk.Label(item_card, text="ปริมาตร (m³):", font=self.FONT_BODY, bg=self.COLOR_CARD).grid(row=3, column=0, sticky="w", pady=3)
        self.ent_item_volume = ttk.Entry(item_card, width=14)
        self.ent_item_volume.insert(0, "0.015")
        self.ent_item_volume.grid(row=3, column=1, sticky="w", pady=3)

        tk.Label(item_card, text="มูลค่าสินค้า (บาท):", font=self.FONT_BODY, bg=self.COLOR_CARD).grid(row=4, column=0, sticky="w", pady=3)
        self.ent_item_value = ttk.Entry(item_card, width=14)
        self.ent_item_value.insert(0, "1500.0")
        self.ent_item_value.grid(row=4, column=1, sticky="w", pady=3)
        self.ent_item_value.bind("<KeyRelease>", lambda e: self._update_price_preview())

        # กรอบข้อมูลเฉพาะตามประเภทสินค้า (Dynamic Form Frame)
        self.dynamic_frame = tk.LabelFrame(
            item_card, text=" คุณสมบัติเฉพาะตามประเภทสินค้า ",
            font=self.FONT_BODY_BOLD, bg="#f8fafc", fg="#334155", padx=10, pady=8
        )
        self.dynamic_frame.grid(row=5, column=0, columnspan=2, sticky="we", pady=10)

        # กล่องสรุปค่าธรรมเนียมประมาณการ & จัดสรรยานพาหนะ
        preview_box = tk.Frame(item_card, bg="#eff6ff", highlightbackground="#93c5fd", highlightthickness=1, padx=12, pady=8)
        preview_box.grid(row=6, column=0, columnspan=2, sticky="we", pady=(6, 10))

        self.lbl_price_preview = tk.Label(
            preview_box,
            text="ประมาณการค่าส่ง: คำนวณอัตโนมัติ",
            font=self.FONT_SUBHEADER,
            fg=self.COLOR_PRIMARY,
            bg="#eff6ff",
        )
        self.lbl_price_preview.pack(anchor="w")

        self.lbl_vehicle_preview = tk.Label(
            preview_box,
            text="ยานพาหนะที่เหมาะสม: กำลังประเมิน...",
            font=self.FONT_SMALL,
            fg="#1e40af",
            bg="#eff6ff",
        )
        self.lbl_vehicle_preview.pack(anchor="w")

        # ปุ่มบันทึกรายการ
        btn_submit = tk.Button(
            item_card,
            text="📦 สร้างรายการพัสดุและจัดสรรรถทันที",
            font=self.FONT_SUBHEADER,
            bg=self.COLOR_PRIMARY,
            fg="#ffffff",
            activebackground=self.COLOR_PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=8,
            command=self._create_shipment_submit,
        )
        btn_submit.grid(row=7, column=0, columnspan=2, pady=10)

        self._render_dynamic_fields(ItemType.STANDARD)
        self._update_price_preview()

    def _on_item_type_changed(self, event=None):
        raw = self.combo_item_type.get()
        if "FRAGILE" in raw:
            cat = ItemType.FRAGILE
        elif "PERISHABLE" in raw:
            cat = ItemType.PERISHABLE
        elif "HAZARDOUS" in raw:
            cat = ItemType.HAZARDOUS
        else:
            cat = ItemType.STANDARD
        self._render_dynamic_fields(cat)
        self._update_price_preview()

    def _render_dynamic_fields(self, item_type: ItemType):
        # ล้าง widget เดิมใน dynamic_frame
        for w in self.dynamic_frame.winfo_children():
            w.destroy()

        if item_type == ItemType.STANDARD:
            tk.Label(self.dynamic_frame, text="✅ พัสดุทั่วไป ไม่มีข้อกำหนดพิเศษด้านอุณหภูมิหรือสารเคมี",
                     font=self.FONT_BODY, bg="#f8fafc", fg="#16a34a").pack(anchor="w", pady=4)

        elif item_type == ItemType.FRAGILE:
            tk.Label(self.dynamic_frame, text="ระดับการห่อหุ้มกันกระแทก:", font=self.FONT_BODY_BOLD, bg="#f8fafc").grid(row=0, column=0, sticky="w", pady=2)
            self.combo_cushion = ttk.Combobox(
                self.dynamic_frame,
                values=["Standard (แอร์บับเบิ้ล)", "Double Layer (บับเบิ้ล 2 ชั้น + โฟม)", "Wooden Crate (ตีลังไม้พิเศษ)"],
                state="readonly",
                width=30,
            )
            self.combo_cushion.current(1)
            self.combo_cushion.grid(row=0, column=1, sticky="w", pady=2)
            self.combo_cushion.bind("<<ComboboxSelected>>", lambda e: self._update_price_preview())

            self.var_insurance = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.dynamic_frame, text="ทำประกันคุ้มครองสินค้าแตกหัก (1.5% ของมูลค่าสินค้า)",
                                  variable=self.var_insurance, command=self._update_price_preview)
            chk.grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        elif item_type == ItemType.PERISHABLE:
            tk.Label(self.dynamic_frame, text="อุณหภูมิเป้าหมาย (°C):", font=self.FONT_BODY_BOLD, bg="#f8fafc").grid(row=0, column=0, sticky="w", pady=2)
            self.ent_target_temp = ttk.Entry(self.dynamic_frame, width=12)
            self.ent_target_temp.insert(0, "4.0")
            self.ent_target_temp.grid(row=0, column=1, sticky="w", pady=2)
            self.ent_target_temp.bind("<KeyRelease>", lambda e: self._update_price_preview())

            tk.Label(self.dynamic_frame, text="อายุสินค้าก่อนหมดอายุ (ชม.):", font=self.FONT_BODY_BOLD, bg="#f8fafc").grid(row=1, column=0, sticky="w", pady=2)
            self.ent_expiry_hours = ttk.Entry(self.dynamic_frame, width=12)
            self.ent_expiry_hours.insert(0, "36")
            self.ent_expiry_hours.grid(row=1, column=1, sticky="w", pady=2)

        elif item_type == ItemType.HAZARDOUS:
            tk.Label(self.dynamic_frame, text="คลาสวัตถุอันตราย (UN Hazard):", font=self.FONT_BODY_BOLD, bg="#f8fafc").grid(row=0, column=0, sticky="w", pady=2)
            self.combo_hazard_class = ttk.Combobox(
                self.dynamic_frame,
                values=[
                    "Class 3 (Flammable Liquids - ของเหลวไวไฟ)",
                    "Class 8 (Corrosive Substances - สารกัดกร่อน)",
                    "Class 9 (Miscellaneous Hazardous - แบตเตอรี่ลิเธียม)",
                ],
                state="readonly",
                width=34,
            )
            self.combo_hazard_class.current(0)
            self.combo_hazard_class.grid(row=0, column=1, sticky="w", pady=2)

            tk.Label(self.dynamic_frame, text="เลขที่ใบอนุญาตความปลอดภัย:", font=self.FONT_BODY_BOLD, bg="#f8fafc").grid(row=1, column=0, sticky="w", pady=2)
            self.ent_license_id = ttk.Entry(self.dynamic_frame, width=24)
            self.ent_license_id.insert(0, "HAZ-LIC-2026-99")
            self.ent_license_id.grid(row=1, column=1, sticky="w", pady=2)

    def _get_current_item_instance(self):
        """สร้าง Item ชั่วคราวเพื่อคำนวณราคาและประเมินรถ"""
        raw_type = self.combo_item_type.get()
        if "FRAGILE" in raw_type:
            item_type = ItemType.FRAGILE
        elif "PERISHABLE" in raw_type:
            item_type = ItemType.PERISHABLE
        elif "HAZARDOUS" in raw_type:
            item_type = ItemType.HAZARDOUS
        else:
            item_type = ItemType.STANDARD

        name = self.ent_item_name.get().strip() or "Sample Item"
        try:
            weight = float(self.ent_item_weight.get())
        except ValueError:
            weight = 1.0

        try:
            volume = float(self.ent_item_volume.get())
        except ValueError:
            volume = 0.01

        try:
            value = float(self.ent_item_value.get())
        except ValueError:
            value = 100.0

        kwargs: Dict[str, Any] = {
            "name": name,
            "weight": weight,
            "volume": volume,
            "declared_value": value,
        }

        if item_type == ItemType.FRAGILE:
            cushion_str = getattr(self, "combo_cushion", None)
            cushion_val = CushioningLevel.DOUBLE_LAYER
            if cushion_str:
                raw_c = cushion_str.get()
                if "Wood" in raw_c:
                    cushion_val = CushioningLevel.WOODEN_CRATE
                elif "Standard" in raw_c:
                    cushion_val = CushioningLevel.STANDARD

            insurance = getattr(self, "var_insurance", None)
            kwargs["cushioning_level"] = cushion_val
            kwargs["requires_insurance"] = insurance.get() if insurance else True

        elif item_type == ItemType.PERISHABLE:
            temp_ent = getattr(self, "ent_target_temp", None)
            exp_ent = getattr(self, "ent_expiry_hours", None)
            kwargs["target_temperature_celsius"] = float(temp_ent.get()) if temp_ent and temp_ent.get() else 4.0
            kwargs["expiry_hours"] = int(exp_ent.get()) if exp_ent and exp_ent.get() else 24

        elif item_type == ItemType.HAZARDOUS:
            haz_cb = getattr(self, "combo_hazard_class", None)
            lic_ent = getattr(self, "ent_license_id", None)
            kwargs["hazard_class"] = haz_cb.get() if haz_cb else "Class 3"
            kwargs["safety_license_id"] = lic_ent.get() if lic_ent else "HAZ-DEFAULT"

        return ItemFactory.create_item(item_type, **kwargs)

    def _update_price_preview(self):
        try:
            item = self._get_current_item_instance()
            try:
                dist = float(self.ent_distance.get())
            except ValueError:
                dist = 10.0

            service_str = self.combo_service.get()
            handling_fee = item.calculate_handling_fee()

            # คำนวณตาม Strategy
            if "EXPRESS" in service_str:
                total = 70.0 + (dist * 6.0) + 50.0 + handling_fee
                tier = "Express (24 ชม.)"
            elif "SAME" in service_str:
                total = 120.0 + (dist * 10.0) + 100.0 + handling_fee
                tier = "Same-Day (วันเดียว)"
            else:
                total = 40.0 + (dist * 3.5) + handling_fee
                tier = "Standard (2-3 วัน)"

            self.lbl_price_preview.config(
                text=f"ประมาณการค่าส่ง ({tier}): ฿{total:,.2f}  (ค่าขนส่ง + ค่าดูแลเฉพาะสินค้า ฿{handling_fee:,.2f})"
            )

            # ค้นหายานพาหนะที่เหมาะ
            vehicle, reason = self.service.fleet.find_best_vehicle(item)
            if vehicle:
                self.lbl_vehicle_preview.config(
                    text=f"ยานพาหนะแนะนำ: [{vehicle.get_vehicle_type().value}] ทะเบียน {vehicle.license_plate} (คนขับ: {vehicle.driver_name})",
                    fg="#16a34a"
                )
            else:
                self.lbl_vehicle_preview.config(
                    text=f"คำเตือน: {reason}",
                    fg="#dc2626"
                )
        except Exception:
            pass

    def _create_shipment_submit(self):
        try:
            item = self._get_current_item_instance()
            dist = float(self.ent_distance.get())
            if dist <= 0:
                messagebox.showerror("ข้อผิดพลาด", "ระยะทางต้องมากกว่า 0 กม.")
                return

            s_name = self.ent_sender_name.get().strip()
            s_phone = self.ent_sender_phone.get().strip()
            r_name = self.ent_receiver_name.get().strip()
            r_phone = self.ent_receiver_phone.get().strip()
            r_addr = self.ent_receiver_addr.get().strip()

            if not s_name or not r_name:
                messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกชื่อผู้ส่งและผู้รับให้ครบถ้วน")
                return

            sender = Customer("SND-" + s_phone[-4:], s_name, s_phone, "sender@example.com",
                              Address("ต้นทาง", "เขตหลัก", "กรุงเทพฯ", "10110"))
            receiver = Customer("RCV-" + r_phone[-4:], r_name, r_phone, "receiver@example.com",
                                Address(r_addr, "ปลายทาง", "ต่างจังหวัด", "30000"))

            service_raw = self.combo_service.get()
            shipment, msg = self.service.create_shipment(
                item=item,
                sender=sender,
                receiver=receiver,
                distance_km=dist,
                service_tier=service_raw,
                auto_assign_vehicle=True,
            )

            messagebox.showinfo("สำเร็จ 🎉", f"บันทึกพัสดุสำเร็จ!\n\nหมายเลขพัสดุ: {shipment.tracking_number}\nยอดรวม: ฿{shipment.calculate_total_cost():,.2f}\n{msg}")

            # สลับไปยังหน้าติดตามพัสดุ
            self.ent_track_search.delete(0, tk.END)
            self.ent_track_search.insert(0, shipment.tracking_number)
            self._search_tracking()
            self.notebook.select(self.tab_track)

        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาด", str(e))

    # -------------------------------------------------------------
    # TAB 2: รายการพัสดุทั้งหมด (Shipment List)
    # -------------------------------------------------------------
    def _build_tab_shipment_list(self):
        container = tk.Frame(self.tab_list, bg=self.COLOR_BG)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # แถบ Filter & Search
        filter_bar = tk.Frame(container, bg=self.COLOR_CARD, padx=12, pady=8)
        filter_bar.pack(fill="x", pady=(0, 10))

        tk.Label(filter_bar, text="ค้นหา:", font=self.FONT_BODY_BOLD, bg=self.COLOR_CARD).pack(side="left", padx=(0, 4))
        self.ent_list_search = ttk.Entry(filter_bar, width=24)
        self.ent_list_search.pack(side="left", padx=(0, 12))
        self.ent_list_search.bind("<KeyRelease>", lambda e: self._refresh_shipment_table())

        tk.Label(filter_bar, text="ประเภทสินค้า:", font=self.FONT_BODY_BOLD, bg=self.COLOR_CARD).pack(side="left", padx=(10, 4))
        self.combo_filter_cat = ttk.Combobox(
            filter_bar,
            values=["ทั้งหมด (All)", "STANDARD", "FRAGILE", "PERISHABLE", "HAZARDOUS"],
            state="readonly",
            width=16,
        )
        self.combo_filter_cat.current(0)
        self.combo_filter_cat.pack(side="left", padx=(0, 12))
        self.combo_filter_cat.bind("<<ComboboxSelected>>", lambda e: self._refresh_shipment_table())

        btn_refresh = tk.Button(
            filter_bar, text="🔄 รีเฟรช", font=self.FONT_SMALL, bg="#e2e8f0", relief="flat", padx=10, pady=2,
            command=self._refresh_shipment_table
        )
        btn_refresh.pack(side="right")

        # ตาราง Treeview
        columns = ("tracking", "name", "category", "sender", "receiver", "vehicle", "cost", "status")
        self.tree_shipments = ttk.Treeview(container, columns=columns, show="headings", height=15)

        self.tree_shipments.heading("tracking", text="หมายเลขติดตาม (Tracking #)")
        self.tree_shipments.heading("name", text="ชื่อพัสดุ/สินค้า")
        self.tree_shipments.heading("category", text="ประเภทสินค้า")
        self.tree_shipments.heading("sender", text="ผู้ส่ง")
        self.tree_shipments.heading("receiver", text="ผู้รับ")
        self.tree_shipments.heading("vehicle", text="ยานพาหนะที่รับผิดชอบ")
        self.tree_shipments.heading("cost", text="ค่าส่งสุทธิ (บาท)")
        self.tree_shipments.heading("status", text="สถานะปัจจุบัน")

        self.tree_shipments.column("tracking", width=140, anchor="center")
        self.tree_shipments.column("name", width=200, anchor="w")
        self.tree_shipments.column("category", width=110, anchor="center")
        self.tree_shipments.column("sender", width=140, anchor="w")
        self.tree_shipments.column("receiver", width=140, anchor="w")
        self.tree_shipments.column("vehicle", width=160, anchor="w")
        self.tree_shipments.column("cost", width=100, anchor="e")
        self.tree_shipments.column("status", width=130, anchor="center")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree_shipments.yview)
        self.tree_shipments.configure(yscrollcommand=scrollbar.set)

        self.tree_shipments.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree_shipments.bind("<Double-1>", self._on_shipment_double_click)

    def _refresh_shipment_table(self):
        for row in self.tree_shipments.get_children():
            self.tree_shipments.delete(row)

        search_query = self.ent_list_search.get().strip().lower()
        cat_filter = self.combo_filter_cat.get()

        for s in self.service.repository.get_all_shipments():
            cat = s.item.get_item_type().value
            if cat_filter != "ทั้งหมด (All)" and cat != cat_filter:
                continue

            match_text = f"{s.tracking_number} {s.item.name} {s.sender.name} {s.receiver.name}".lower()
            if search_query and search_query not in match_text:
                continue

            veh_str = s.assigned_vehicle.license_plate if s.assigned_vehicle else "ยังไม่จัดสรร"

            self.tree_shipments.insert(
                "",
                "end",
                values=(
                    s.tracking_number,
                    s.item.name,
                    cat,
                    s.sender.name,
                    s.receiver.name,
                    veh_str,
                    f"฿{s.calculate_total_cost():,.2f}",
                    s.status.value,
                ),
            )

    def _on_shipment_double_click(self, event):
        selected = self.tree_shipments.selection()
        if not selected:
            return
        item_data = self.tree_shipments.item(selected[0], "values")
        tracking_num = item_data[0]

        self.ent_track_search.delete(0, tk.END)
        self.ent_track_search.insert(0, tracking_num)
        self._search_tracking()
        self.notebook.select(self.tab_track)

    # -------------------------------------------------------------
    # TAB 3: ติดตามสถานะและไทม์ไลน์ (Tracking & Events)
    # -------------------------------------------------------------
    def _build_tab_tracking(self):
        container = tk.Frame(self.tab_track, bg=self.COLOR_BG)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # Search Box
        search_card = tk.Frame(container, bg=self.COLOR_CARD, padx=14, pady=10)
        search_card.pack(fill="x", pady=(0, 10))

        tk.Label(search_card, text="🔍 หมายเลขติดตามพัสดุ (Tracking Number):", font=self.FONT_SUBHEADER, bg=self.COLOR_CARD).pack(side="left", padx=(0, 8))
        self.ent_track_search = ttk.Entry(search_card, width=28, font=("Segoe UI", 11))
        self.ent_track_search.pack(side="left", padx=(0, 8))
        self.ent_track_search.bind("<Return>", lambda e: self._search_tracking())

        btn_search = tk.Button(
            search_card, text="ค้นหาพัสดุ", font=self.FONT_BODY_BOLD, bg=self.COLOR_PRIMARY, fg="#ffffff",
            relief="flat", padx=14, pady=4, command=self._search_tracking
        )
        btn_search.pack(side="left")

        # รายละเอียดพัสดุและการก้าวหน้าสถานะ
        content_frame = tk.Frame(container, bg=self.COLOR_BG)
        content_frame.pack(fill="both", expand=True)

        # Left Info Card
        self.card_info = tk.LabelFrame(
            content_frame, text=" 📦 สรุปข้อมูลพัสดุและข้อกำหนดเฉพาะ ",
            font=self.FONT_SUBHEADER, bg=self.COLOR_CARD, padx=14, pady=10, width=420
        )
        self.card_info.pack(side="left", fill="both", padx=(0, 8))
        self.card_info.pack_propagate(False)

        self.lbl_info_details = tk.Label(
            self.card_info, text="กรุณาค้นหาหมายเลขพัสดุ...", font=self.FONT_BODY, bg=self.COLOR_CARD, justify="left", wraplength=380
        )
        self.lbl_info_details.pack(anchor="nw", fill="both", expand=True)

        # ปุ่ม Advance Status
        btn_box = tk.Frame(self.card_info, bg=self.COLOR_CARD)
        btn_box.pack(fill="x", side="bottom", pady=8)

        self.btn_advance = tk.Button(
            btn_box, text="⏩ เลื่อนสถานะพัสดุสู่ขั้นตอนถัดไป",
            font=self.FONT_BODY_BOLD, bg="#059669", fg="#ffffff", relief="flat", padx=12, pady=6,
            command=self._advance_status_click
        )
        self.btn_advance.pack(fill="x")

        # Right Timeline Card
        card_timeline = tk.LabelFrame(
            content_frame, text=" 📍 ไทม์ไลน์การเดินทาง (Tracking Timeline & Observer Notifier) ",
            font=self.FONT_SUBHEADER, bg=self.COLOR_CARD, padx=14, pady=10
        )
        card_timeline.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # Text Area สำหรับแสดง Timeline และการแจ้งเตือน
        self.txt_timeline = tk.Text(card_timeline, font=("Consolas", 10), bg="#f8fafc", relief="flat", padx=10, pady=10)
        scroll_time = ttk.Scrollbar(card_timeline, orient="vertical", command=self.txt_timeline.yview)
        self.txt_timeline.configure(yscrollcommand=scroll_time.set)

        self.txt_timeline.pack(side="left", fill="both", expand=True)
        scroll_time.pack(side="right", fill="y")

    def _search_tracking(self):
        tracking_num = self.ent_track_search.get().strip().upper()
        if not tracking_num:
            return

        shipment = self.service.repository.get_shipment(tracking_num)
        if not shipment:
            messagebox.showwarning("ไม่พบข้อมูล", f"ไม่พบพัสดุหมายเลข {tracking_num}")
            return

        self._current_tracked_shipment = shipment

        # Render Left Info Card
        item = shipment.item
        veh = shipment.assigned_vehicle
        veh_info = f"ทะเบียน {veh.license_plate} ({veh.get_vehicle_type().value})\nคนขับ: {veh.driver_name}" if veh else "ยังไม่มีการจัดสรรรถ"

        info_text = (
            f"หมายเลขพัสดุ:  {shipment.tracking_number}\n"
            f"สถานะปัจจุบัน:  [{shipment.status.value}]\n"
            f"-----------------------------------------------\n"
            f"สินค้า:         {item.name}\n"
            f"ประเภท:         {item.get_item_type().value}\n"
            f"น้ำหนัก/ปริมาตร: {item.weight} กก. | {item.volume} m³\n"
            f"มูลค่าสินค้า:    ฿{item.declared_value:,.2f}\n"
            f"ข้อกำหนดพิเศษ:   {item.get_special_requirements()}\n"
            f"-----------------------------------------------\n"
            f"บริการ:         {shipment.pricing_strategy.get_strategy_name()}\n"
            f"ระยะทาง:        {shipment.distance_km} กม.\n"
            f"ค่าส่งรวม:       ฿{shipment.calculate_total_cost():,.2f}\n"
            f"-----------------------------------------------\n"
            f"ผู้ส่ง:          {shipment.sender.name} ({shipment.sender.phone})\n"
            f"ผู้รับ:          {shipment.receiver.name} ({shipment.receiver.phone})\n"
            f"ที่อยู่ส่งมอบ:   {shipment.receiver.address}\n"
            f"-----------------------------------------------\n"
            f"ยานพาหนะ:       {veh_info}\n"
        )
        self.lbl_info_details.config(text=info_text)

        # Render Timeline
        self.txt_timeline.delete("1.0", tk.END)
        self.txt_timeline.insert(tk.END, f"=== ไทม์ไลน์สถานะพัสดุ: {shipment.tracking_number} ===\n\n")

        for i, event in enumerate(shipment.tracking_history, 1):
            badge = "🟢" if event.status == ShipmentStatus.DELIVERED else "🔹"
            entry = f"{badge} จุดที่ {i}: [{event.timestamp}]\n"
            entry += f"   สถานะ: {event.status.value}\n"
            entry += f"   สถานที่: {event.location}\n"
            entry += f"   รายละเอียด: {event.message}\n"
            entry += "   " + "-" * 55 + "\n"
            self.txt_timeline.insert(tk.END, entry)

        self.txt_timeline.insert(tk.END, "\n=== 🔔 บันทึกการส่งข้อความแจ้งเตือน (Observer Alerts) ===\n")
        for sms in self.service.sms_notifier.sent_messages:
            if shipment.tracking_number in sms["message"]:
                self.txt_timeline.insert(tk.END, f"📱 SMS ผู้รับ ({sms['to_recipient']}): {sms['message']}\n")

    def _advance_status_click(self):
        shipment = getattr(self, "_current_tracked_shipment", None)
        if not shipment:
            messagebox.showinfo("แจ้งเตือน", "กรุณาค้นหาพัสดุก่อน")
            return

        locations = {
            ShipmentStatus.PENDING: "ศูนย์คัดแยกหลัก",
            ShipmentStatus.CONFIRMED: "ศูนย์คัดแยกต้นทาง",
            ShipmentStatus.VEHICLE_ASSIGNED: "ระหว่างเส้นทางขนส่งข้ามจังหวัด",
            ShipmentStatus.IN_TRANSIT: "ศูนย์กระจายสินค้าปลายทาง",
            ShipmentStatus.OUT_FOR_DELIVERY: "บ้าน/สำนักงานผู้รับ",
        }
        loc = locations.get(shipment.status, "สถานีปลายทาง")
        msg = f"ดำเนินการตรวจสอบและส่งต่อตามมาตรฐาน {shipment.item.get_item_type().value}"

        success, result_msg = self.service.advance_shipment_status(shipment.tracking_number, loc, msg)
        if success:
            messagebox.showinfo("สำเร็จ", result_msg)
            self._search_tracking()
            self._refresh_shipment_table()
        else:
            messagebox.showwarning("ไม่สามารถเลื่อนสถานะ", result_msg)

    # -------------------------------------------------------------
    # TAB 4: ข้อมูลยานพาหนะ (Fleet Management)
    # -------------------------------------------------------------
    def _build_tab_fleet(self):
        container = tk.Frame(self.tab_fleet, bg=self.COLOR_BG)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        header_box = tk.Frame(container, bg=self.COLOR_CARD, padx=14, pady=10)
        header_box.pack(fill="x", pady=(0, 10))

        tk.Label(
            header_box,
            text="🚚 กองยานพาหนะและการจำแนกประเภทยานยนต์ขนส่ง",
            font=self.FONT_SUBHEADER,
            bg=self.COLOR_CARD,
        ).pack(side="left")

        btn_refresh = tk.Button(
            header_box, text="🔄 รีเฟรชข้อมูลยานพาหนะ", font=self.FONT_SMALL, bg="#e2e8f0", relief="flat", padx=10, pady=2,
            command=self._refresh_fleet_cards
        )
        btn_refresh.pack(side="right")

        # Scrollable Area for Vehicle Cards
        self.canvas_fleet = tk.Canvas(container, bg=self.COLOR_BG, highlightthickness=0)
        scroll_fleet = ttk.Scrollbar(container, orient="vertical", command=self.canvas_fleet.yview)
        self.frame_fleet_cards = tk.Frame(self.canvas_fleet, bg=self.COLOR_BG)

        self.frame_fleet_cards.bind(
            "<Configure>",
            lambda e: self.canvas_fleet.configure(scrollregion=self.canvas_fleet.bbox("all")),
        )
        self.canvas_fleet.create_window((0, 0), window=self.frame_fleet_cards, anchor="nw")
        self.canvas_fleet.configure(yscrollcommand=scroll_fleet.set)

        self.canvas_fleet.pack(side="left", fill="both", expand=True)
        scroll_fleet.pack(side="right", fill="y")

        self._refresh_fleet_cards()

    def _refresh_fleet_cards(self):
        for w in self.frame_fleet_cards.winfo_children():
            w.destroy()

        vehicles = self.service.fleet.get_all_vehicles()
        for idx, veh in enumerate(vehicles):
            card = tk.LabelFrame(
                self.frame_fleet_cards,
                text=f" 🚛 {veh.get_vehicle_type().value} - ทะเบียน: {veh.license_plate} ",
                font=self.FONT_SUBHEADER,
                bg=self.COLOR_CARD,
                padx=14,
                pady=10,
            )
            card.pack(fill="x", expand=True, pady=6, padx=6)

            # Details
            cur_w = veh.current_weight_load()
            max_w = veh.max_weight
            pct_w = veh.get_utilization_percentage()
            cur_v = veh.current_volume_load()
            max_v = veh.max_volume

            info_str = (
                f"รหัสรถ: {veh.vehicle_id}  |  พนักงานขับ: {veh.driver_name}  |  สถานะ: {'🟢 พร้อมใช้งาน' if veh.is_active else '🔴 หยุดปฏิบัติการ'}\n"
                f"ความจุน้ำหนัก: {cur_w:.1f} / {max_w:.1f} กก. (ใช้งานไป {pct_w}%)  |  ความจุปริมาตร: {cur_v:.3f} / {max_v:.2f} m³\n"
                f"จำนวนพัสดุบนรถ: {len(veh.loaded_items)} ชิ้น"
            )
            tk.Label(card, text=info_str, font=self.FONT_BODY, bg=self.COLOR_CARD, justify="left").pack(anchor="w", pady=(0, 6))

            # Progress Bar for load
            prog = ttk.Progressbar(card, orient="horizontal", length=400, mode="determinate")
            prog["value"] = min(100.0, pct_w)
            prog.pack(anchor="w", pady=(0, 6))

            # Items on vehicle list
            if veh.loaded_items:
                items_str = "พัสดุบนรถ: " + ", ".join([f"{it.name} ({it.get_item_type().value}, {it.weight}kg)" for it in veh.loaded_items])
                tk.Label(card, text=items_str, font=self.FONT_SMALL, fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_CARD).pack(anchor="w")

    # -------------------------------------------------------------
    # TAB 5: แดชบอร์ดสรุปผล (Analytics Dashboard)
    # -------------------------------------------------------------
    def _build_tab_analytics(self):
        container = tk.Frame(self.tab_stats, bg=self.COLOR_BG)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # 4 Metric Cards in a row
        metrics_row = tk.Frame(container, bg=self.COLOR_BG)
        metrics_row.pack(fill="x", pady=(0, 14))

        self.card_total_shipments = self._create_metric_card(metrics_row, "📦 พัสดุทั้งหมดในระบบ", "0 ชิ้น", "#2563eb")
        self.card_revenue = self._create_metric_card(metrics_row, "💰 รายได้ค่าจัดส่งรวม", "฿0.00", "#059669")
        self.card_fleet_active = self._create_metric_card(metrics_row, "🚚 กองยานพาหนะพร้อมใช้", "0 คัน", "#d97706")
        self.card_utilization = self._create_metric_card(metrics_row, "📈 อัตราบรรทุกเฉลี่ย", "0.0%", "#7c3aed")

        # Two Large Sections: Parcel Distribution & System Audit Log
        bottom_frame = tk.Frame(container, bg=self.COLOR_BG)
        bottom_frame.pack(fill="both", expand=True)

        # Left: Category & Status Breakdown
        box_breakdown = tk.LabelFrame(
            bottom_frame, text=" 📊 สถิติจำแนกตามประเภทสินค้าและสถานะ ",
            font=self.FONT_SUBHEADER, bg=self.COLOR_CARD, padx=14, pady=10
        )
        box_breakdown.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.lbl_stats_breakdown = tk.Label(
            box_breakdown, text="", font=self.FONT_BODY, bg=self.COLOR_CARD, justify="left"
        )
        self.lbl_stats_breakdown.pack(anchor="nw", fill="both", expand=True)

        # Right: Audit Logs (Observer Pattern Live Output)
        box_audit = tk.LabelFrame(
            bottom_frame, text=" 🛡️ บันทึกการทำงานระบบ (System Audit Log) ",
            font=self.FONT_SUBHEADER, bg=self.COLOR_CARD, padx=14, pady=10
        )
        box_audit.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self.txt_audit = tk.Text(box_audit, font=("Consolas", 9), bg="#f8fafc", relief="flat", padx=8, pady=8)
        scroll_audit = ttk.Scrollbar(box_audit, orient="vertical", command=self.txt_audit.yview)
        self.txt_audit.configure(yscrollcommand=scroll_audit.set)

        self.txt_audit.pack(side="left", fill="both", expand=True)
        scroll_audit.pack(side="right", fill="y")

    def _create_metric_card(self, parent, title: str, initial_value: str, color: str):
        card = tk.Frame(parent, bg=self.COLOR_CARD, padx=16, pady=12, highlightbackground="#e2e8f0", highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=4)

        tk.Label(card, text=title, font=self.FONT_SMALL, fg=self.COLOR_TEXT_MUTED, bg=self.COLOR_CARD).pack(anchor="w")
        val_label = tk.Label(card, text=initial_value, font=("Segoe UI", 18, "bold"), fg=color, bg=self.COLOR_CARD)
        val_label.pack(anchor="w", pady=(4, 0))
        return val_label

    def _refresh_analytics(self):
        metrics = self.service.get_dashboard_metrics()

        self.card_total_shipments.config(text=f"{metrics['total_shipments']} รายการ")
        self.card_revenue.config(text=f"฿{metrics['total_revenue_thb']:,.2f}")

        fleet = metrics["fleet_stats"]
        self.card_fleet_active.config(text=f"{fleet['active_vehicles']} / {fleet['total_vehicles']} คัน")
        self.card_utilization.config(text=f"{fleet['avg_utilization_pct']}%")

        # Category Breakdown
        cats = metrics["by_category"]
        statuses = metrics["by_status"]

        text = (
            "🏷️ การกระจายตัวตามประเภทสินค้า (Parcel Classification):\n"
            f"  • STANDARD (สินค้าทั่วไป):       {cats.get('STANDARD', 0)} ชิ้น\n"
            f"  • FRAGILE (สินค้าแตกหักง่าย):      {cats.get('FRAGILE', 0)} ชิ้น\n"
            f"  • PERISHABLE (ควบคุมอุณหภูมิ):   {cats.get('PERISHABLE', 0)} ชิ้น\n"
            f"  • HAZARDOUS (วัตถุอันตราย):      {cats.get('HAZARDOUS', 0)} ชิ้น\n\n"
            "📌 การกระจายตัวตามสถานะการจัดส่ง (Status Lifecycle):\n"
        )
        for st_name, count in statuses.items():
            text += f"  • {st_name}: {count} รายการ\n"

        text += (
            f"\n🚚 รายละเอียดการใช้ทรัพยากรยานพาหนะ:\n"
            f"  • น้ำหนักบรรทุกรวมขณะนี้: {fleet['total_weight_loaded_kg']} กก.\n"
            f"  • พัสดุที่อยู่บนรถขณะนี้: {fleet['total_items_loaded']} ชิ้น\n"
        )
        self.lbl_stats_breakdown.config(text=text)

        # Audit Log
        self.txt_audit.delete("1.0", tk.END)
        for log in self.service.audit_logger.logs[-50:]:
            self.txt_audit.insert(tk.END, log + "\n")

    def _on_tab_change(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 1:
            self._refresh_shipment_table()
        elif selected_tab == 3:
            self._refresh_fleet_cards()
        elif selected_tab == 4:
            self._refresh_analytics()

    def _export_data(self):
        try:
            path = self.service.repository.export_to_json("shipments_data.json")
            messagebox.showinfo("ส่งออกข้อมูลสำเร็จ", f"บันทึกข้อมูลพัสดุและยานพาหนะลงไฟล์เรียบร้อย:\n{path}")
        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาดในการบันทึก", str(e))


def run_gui():
    root = tk.Tk()
    app = LogisticsGUIApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
