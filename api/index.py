"""
Vercel Serverless Entrypoint & FastAPI Web Application
Integrates Core OOP/OOAD Logistics Services with a Modern Clean Web UI.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models.item import ItemType, CushioningLevel
from src.models.customer import Customer, Address
from src.factory.item_factory import ItemFactory
from src.services.logistics_service import LogisticsService

# Initialize FastAPI application
app = FastAPI(
    title="Logistics & Parcel Management API",
    description="ระบบบริหารจัดการขนส่งและพัสดุภัณฑ์ (OOP & OOAD Architecture) บน Vercel",
    version="1.0.0",
)

# Global Service Singleton
service = LogisticsService()
service.seed_initial_data()


# --- Pydantic Request Models ---

class ItemInput(BaseModel):
    item_type: str = Field(..., example="STANDARD")
    name: str = Field(..., example="เอกสารสัญญา")
    weight: float = Field(..., gt=0, example=2.5)
    volume: float = Field(..., gt=0, example=0.015)
    declared_value: float = Field(0.0, ge=0, example=1500.0)
    # Specific fields
    cushioning_level: Optional[str] = "Double Layer"
    requires_insurance: Optional[bool] = True
    target_temperature_celsius: Optional[float] = 4.0
    expiry_hours: Optional[int] = 24
    hazard_class: Optional[str] = "Class 3 (Flammable)"
    safety_license_id: Optional[str] = "HAZ-LIC-01"


class CreateShipmentRequest(BaseModel):
    item: ItemInput
    sender_name: str
    sender_phone: str
    sender_address: str = "กรุงเทพฯ"
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    distance_km: float = Field(..., gt=0)
    service_tier: str = "STANDARD"
    auto_assign_vehicle: bool = True


class AdvanceStatusRequest(BaseModel):
    location: Optional[str] = "ศูนย์คัดแยกปลายทาง"
    message: Optional[str] = "ตรวจสอบพัสดุและส่งต่อไปยังขั้นตอนถัดไป"


class CalculateRequest(BaseModel):
    item: ItemInput
    distance_km: float
    service_tier: str = "STANDARD"


# --- API Routes ---

@app.get("/api/shipments")
def get_shipments(category: Optional[str] = None, search: Optional[str] = None):
    shipments = service.repository.get_all_shipments()
    results = []
    for s in shipments:
        cat = s.item.get_item_type().value
        if category and category != "ALL" and cat != category:
            continue
        if search:
            query = search.strip().lower()
            text = f"{s.tracking_number} {s.item.name} {s.sender.name} {s.receiver.name}".lower()
            if query not in text:
                continue
        results.append(s.to_dict())
    return results


@app.get("/api/shipments/{tracking_number}")
def get_shipment_by_tracking(tracking_number: str):
    s = service.repository.get_shipment(tracking_number)
    if not s:
        raise HTTPException(status_code=404, detail=f"ไม่พบพัสดุหมายเลข {tracking_number}")
    return s.to_dict()


@app.post("/api/shipments")
def create_shipment_api(req: CreateShipmentRequest):
    try:
        # 1. สร้าง Item ผ่าน Factory Pattern
        item_kwargs = req.item.model_dump()
        item_type = item_kwargs.pop("item_type")
        item = ItemFactory.create_item(item_type, **item_kwargs)

        # 2. สร้าง Customer
        sender = Customer(
            customer_id=f"SND-{req.sender_phone[-4:]}",
            name=req.sender_name,
            phone=req.sender_phone,
            email=f"sender_{req.sender_phone[-4:]}@mail.com",
            address=Address(req.sender_address, "กลาง", "กรุงเทพฯ", "10110"),
        )
        receiver = Customer(
            customer_id=f"RCV-{req.receiver_phone[-4:]}",
            name=req.receiver_name,
            phone=req.receiver_phone,
            email=f"receiver_{req.receiver_phone[-4:]}@mail.com",
            address=Address(req.receiver_address, "ปลายทาง", "จังหวัด", "30000"),
        )

        # 3. สร้าง Shipment ผ่าน Facade Service
        shipment, message = service.create_shipment(
            item=item,
            sender=sender,
            receiver=receiver,
            distance_km=req.distance_km,
            service_tier=req.service_tier,
            auto_assign_vehicle=req.auto_assign_vehicle,
        )

        return {
            "success": True,
            "message": message,
            "shipment": shipment.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/shipments/{tracking_number}/advance")
def advance_status_api(tracking_number: str, req: AdvanceStatusRequest):
    success, message = service.advance_shipment_status(
        tracking_number=tracking_number,
        location=req.location or "จุดส่งมอบ",
        message=req.message or "อัปเดตสถานะอัตโนมัติ",
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    shipment = service.repository.get_shipment(tracking_number)
    return {"success": True, "message": message, "shipment": shipment.to_dict() if shipment else None}


@app.post("/api/calculate")
def calculate_estimate(req: CalculateRequest):
    try:
        item_kwargs = req.item.model_dump()
        item_type = item_kwargs.pop("item_type")
        item = ItemFactory.create_item(item_type, **item_kwargs)

        # Strategy pricing
        tier = req.service_tier.upper()
        if "EXPRESS" in tier:
            from src.strategies.pricing import ExpressPricingStrategy
            strat = ExpressPricingStrategy()
        elif "SAME" in tier:
            from src.strategies.pricing import SameDayPricingStrategy
            strat = SameDayPricingStrategy()
        else:
            from src.strategies.pricing import StandardPricingStrategy
            strat = StandardPricingStrategy()

        breakdown = strat.get_breakdown(item, req.distance_km)
        vehicle, veh_msg = service.fleet.find_best_vehicle(item)

        return {
            "pricing": breakdown,
            "recommended_vehicle": vehicle.to_dict() if vehicle else None,
            "vehicle_status": veh_msg,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/fleet")
def get_fleet_api():
    vehicles = [v.to_dict() for v in service.fleet.get_all_vehicles()]
    summary = service.fleet.get_fleet_summary()
    return {"vehicles": vehicles, "summary": summary}


@app.get("/api/analytics")
def get_analytics_api():
    metrics = service.get_dashboard_metrics()
    logs = service.audit_logger.logs[-30:]
    sms_logs = service.sms_notifier.sent_messages[-30:]
    return {"metrics": metrics, "audit_logs": logs, "sms_logs": sms_logs}


# --- Frontend Web Application (HTML5 + Tailwind CSS SPA) ---

@app.get("/", response_class=HTMLResponse)
def index_page():
    html_content = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ระบบบริหารจัดการขนส่งและพัสดุภัณฑ์ (Logistics Management)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            sans: ['Prompt', 'sans-serif'],
          },
          colors: {
            brand: {
              50: '#eff6ff',
              100: '#dbeafe',
              500: '#3b82f6',
              600: '#2563eb',
              700: '#1d4ed8',
              900: '#1e3a8a',
            }
          }
        }
      }
    }
  </script>
  <style>
    body { font-family: 'Prompt', sans-serif; }
    .badge-STANDARD { @apply bg-blue-50 text-blue-700 border border-blue-200; }
    .badge-FRAGILE { @apply bg-amber-50 text-amber-700 border border-amber-200; }
    .badge-PERISHABLE { @apply bg-emerald-50 text-emerald-700 border border-emerald-200; }
    .badge-HAZARDOUS { @apply bg-rose-50 text-rose-700 border border-rose-200; }
  </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col">

  <!-- Header Navbar -->
  <header class="bg-slate-900 text-white shadow-md sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white text-xl shadow-lg">
          📦
        </div>
        <div>
          <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            LOGISTICS & PARCEL SYSTEM
            <span class="text-xs bg-blue-500/20 text-blue-300 border border-blue-400/30 px-2 py-0.5 rounded-full font-normal">OOP & OOAD</span>
          </h1>
          <p class="text-xs text-slate-400">ระบบจำลองการบริหารจัดการขนส่งและจำแนกประเภทสินค้า</p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <a href="/docs" target="_blank" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition">
          📑 API Docs (Swagger)
        </a>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-2 border-t border-slate-800 pt-1 pb-1 overflow-x-auto text-sm">
      <button onclick="switchTab('new')" id="tab-btn-new" class="tab-btn px-4 py-2 font-medium rounded-lg text-white bg-blue-600 transition flex items-center gap-1.5">
        <span>➕</span> สร้างรายการพัสดุ
      </button>
      <button onclick="switchTab('list')" id="tab-btn-list" class="tab-btn px-4 py-2 font-medium rounded-lg text-slate-400 hover:text-white transition flex items-center gap-1.5">
        <span>📋</span> รายการพัสดุทั้งหมด
      </button>
      <button onclick="switchTab('track')" id="tab-btn-track" class="tab-btn px-4 py-2 font-medium rounded-lg text-slate-400 hover:text-white transition flex items-center gap-1.5">
        <span>🔍</span> ติดตามสถานะ (Tracking)
      </button>
      <button onclick="switchTab('fleet')" id="tab-btn-fleet" class="tab-btn px-4 py-2 font-medium rounded-lg text-slate-400 hover:text-white transition flex items-center gap-1.5">
        <span>🚚</span> คลังยานพาหนะ
      </button>
      <button onclick="switchTab('analytics')" id="tab-btn-analytics" class="tab-btn px-4 py-2 font-medium rounded-lg text-slate-400 hover:text-white transition flex items-center gap-1.5">
        <span>📊</span> สรุปสถิติ & แดชบอร์ด
      </button>
    </div>
  </header>

  <!-- Main Content Area -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">

    <!-- TAB 1: สร้างพัสดุใหม่ (New Parcel) -->
    <div id="tab-new" class="tab-content">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Left Column: ผู้ส่ง, ผู้รับ, บริการ -->
        <div class="lg:col-span-5 space-y-6">
          <!-- ผู้ส่งและผู้รับ -->
          <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <h2 class="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
              <span class="w-6 h-6 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center text-sm font-bold">1</span>
              ข้อมูลผู้ส่งและผู้รับ
            </h2>
            <div class="space-y-3 text-sm">
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">ชื่อผู้ส่ง</label>
                <input type="text" id="sender_name" value="บริษัท สยามดิจิทัลพาร์ทเนอร์ จำกัด" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">เบอร์โทรผู้ส่ง</label>
                <input type="text" id="sender_phone" value="081-888-9999" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div class="pt-2 border-t border-slate-100"></div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">ชื่อผู้รับ</label>
                <input type="text" id="receiver_name" value="คุณกานต์ เจริญสุข" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">เบอร์โทรผู้รับ</label>
                <input type="text" id="receiver_phone" value="089-777-6655" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">ที่อยู่จัดส่งปลายทาง</label>
                <textarea id="receiver_address" rows="2" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">128/9 ถ.พหลโยธิน แขวงสามเสนใน เขตพญาไท กรุงเทพฯ 10400</textarea>
              </div>
            </div>
          </div>

          <!-- บริการจัดส่ง & ระยะทาง -->
          <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <h2 class="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
              <span class="w-6 h-6 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center text-sm font-bold">2</span>
              บริการจัดส่ง (Strategy Pattern)
            </h2>
            <div class="space-y-3 text-sm">
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">ระยะทางขนส่ง (กิโลเมตร)</label>
                <input type="number" id="distance_km" value="28.5" step="0.5" min="1" oninput="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">ระดับความเร็วการจัดส่ง</label>
                <select id="service_tier" onchange="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white">
                  <option value="STANDARD">Standard (ส่งธรรมดา 2-3 วันทำการ)</option>
                  <option value="EXPRESS" selected>Express (ส่งด่วนภายใน 24 ชม.)</option>
                  <option value="SAME_DAY">Same-Day (ส่งด่วนทันทีในวันเดียว)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: การจำแนกประเภทสินค้า & ผลการคำนวณ -->
        <div class="lg:col-span-7 space-y-6">
          <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <h2 class="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
              <span class="w-6 h-6 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center text-sm font-bold">3</span>
              การจำแนกประเภทสินค้า (Item Classification)
            </h2>
            
            <!-- Type Selector Pills -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              <button type="button" onclick="selectItemType('STANDARD')" id="btn-type-STANDARD" class="type-pill py-2.5 px-3 rounded-xl border border-blue-500 bg-blue-50 text-blue-700 font-semibold text-xs flex flex-col items-center gap-1 transition">
                <span class="text-base">📄</span>
                <span>STANDARD</span>
                <span class="text-[10px] font-normal text-slate-500">พัสดุทั่วไป</span>
              </button>
              <button type="button" onclick="selectItemType('FRAGILE')" id="btn-type-FRAGILE" class="type-pill py-2.5 px-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-white text-slate-700 font-semibold text-xs flex flex-col items-center gap-1 transition">
                <span class="text-base">🏺</span>
                <span>FRAGILE</span>
                <span class="text-[10px] font-normal text-slate-500">แตกหักง่าย</span>
              </button>
              <button type="button" onclick="selectItemType('PERISHABLE')" id="btn-type-PERISHABLE" class="type-pill py-2.5 px-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-white text-slate-700 font-semibold text-xs flex flex-col items-center gap-1 transition">
                <span class="text-base">❄️</span>
                <span>PERISHABLE</span>
                <span class="text-[10px] font-normal text-slate-500">คุมอุณหภูมิ/สด</span>
              </button>
              <button type="button" onclick="selectItemType('HAZARDOUS')" id="btn-type-HAZARDOUS" class="type-pill py-2.5 px-3 rounded-xl border border-slate-200 hover:border-slate-300 bg-white text-slate-700 font-semibold text-xs flex flex-col items-center gap-1 transition">
                <span class="text-base">⚠️</span>
                <span>HAZARDOUS</span>
                <span class="text-[10px] font-normal text-slate-500">วัตถุอันตราย</span>
              </button>
            </div>

            <!-- Common Fields -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div class="sm:col-span-2">
                <label class="block text-xs font-semibold text-slate-600 mb-1">ชื่อสินค้า/พัสดุ</label>
                <input type="text" id="item_name" value="หนังสือสัญญาและกล่องแฟ้มข้อมูล" oninput="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">น้ำหนัก (กิโลกรัม)</label>
                <input type="number" id="item_weight" value="3.5" step="0.1" min="0.1" oninput="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">ปริมาตร (ลูกบาศก์เมตร m³)</label>
                <input type="number" id="item_volume" value="0.015" step="0.001" min="0.001" oninput="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
              <div class="sm:col-span-2">
                <label class="block text-xs font-semibold text-slate-600 mb-1">มูลค่าที่แจ้งไว้ (บาท)</label>
                <input type="number" id="declared_value" value="2500" step="100" min="0" oninput="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
              </div>
            </div>

            <!-- Dynamic Specific Fields Card -->
            <div id="dynamic-fields" class="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <!-- Content rendered dynamically via JS -->
            </div>
          </div>

          <!-- Real-Time Price & Fleet Preview Box -->
          <div class="bg-gradient-to-br from-blue-900 to-indigo-950 text-white p-5 rounded-2xl shadow-lg relative overflow-hidden">
            <div class="relative z-10">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs uppercase tracking-wider text-blue-300 font-semibold">สรุปค่าบริการและจัดสรรยานพาหนะอัตโนมัติ</span>
                <span id="preview-service-tag" class="text-xs bg-blue-500/30 text-blue-200 px-2 py-0.5 rounded-full border border-blue-400/30">Express (24 ชม.)</span>
              </div>
              <div class="flex items-baseline gap-2 mb-3">
                <span class="text-3xl font-extrabold" id="preview-total-cost">฿0.00</span>
                <span class="text-xs text-blue-200" id="preview-breakdown-text">(ค่าส่งพื้นฐาน + ค่าดูแลเฉพาะสินค้า)</span>
              </div>
              
              <!-- Vehicle Recommendation Info -->
              <div class="pt-3 border-t border-blue-800/80 flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                  <span class="text-lg">🚚</span>
                  <div>
                    <div class="font-medium text-white" id="preview-vehicle-name">กำลังประเมินยานพาหนะ...</div>
                    <div class="text-blue-300" id="preview-vehicle-sub">ตรวจสอบความเข้ากันได้ตามกฎความปลอดภัย</div>
                  </div>
                </div>
                <button type="button" onclick="submitNewShipment()" class="bg-blue-500 hover:bg-blue-400 text-white font-semibold px-5 py-2.5 rounded-xl shadow transition transform active:scale-95 text-sm flex items-center gap-1.5">
                  <span>🚀</span> บันทึกและจัดส่ง
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- TAB 2: รายการพัสดุทั้งหมด (Shipment List) -->
    <div id="tab-list" class="tab-content hidden space-y-4">
      <!-- Search & Filters -->
      <div class="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex items-center gap-2 w-full sm:w-auto">
          <input type="text" id="search-input" oninput="loadShipments()" placeholder="🔍 ค้นหาเลขพัสดุ, ชื่อสินค้า หรือชื่อผู้รับ..." class="w-full sm:w-80 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
          <select id="filter-category" onchange="loadShipments()" class="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none">
            <option value="ALL">ทุกประเภทสินค้า (All)</option>
            <option value="STANDARD">STANDARD</option>
            <option value="FRAGILE">FRAGILE</option>
            <option value="PERISHABLE">PERISHABLE</option>
            <option value="HAZARDOUS">HAZARDOUS</option>
          </select>
        </div>
        <button onclick="loadShipments()" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2 rounded-lg transition flex items-center gap-1">
          🔄 รีเฟรชข้อมูล
        </button>
      </div>

      <!-- Table Container -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm border-collapse">
            <thead class="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs font-semibold uppercase">
              <tr>
                <th class="py-3 px-4">หมายเลขติดตาม</th>
                <th class="py-3 px-4">ชื่อสินค้า</th>
                <th class="py-3 px-4">ประเภทสินค้า</th>
                <th class="py-3 px-4">ผู้รับ</th>
                <th class="py-3 px-4">ยานพาหนะ</th>
                <th class="py-3 px-4 text-right">ค่าส่งสุทธิ</th>
                <th class="py-3 px-4 text-center">สถานะ</th>
                <th class="py-3 px-4 text-center">จัดการ</th>
              </tr>
            </thead>
            <tbody id="shipments-table-body" class="divide-y divide-slate-100">
              <!-- Rendered via JS -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 3: ติดตามสถานะ (Tracking) -->
    <div id="tab-track" class="tab-content hidden space-y-6">
      <!-- Search Input Card -->
      <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col sm:flex-row items-center gap-3">
        <div class="w-full">
          <label class="block text-xs font-semibold text-slate-600 mb-1">ค้นหาหมายเลขพัสดุ (Tracking Number)</label>
          <div class="flex gap-2">
            <input type="text" id="track-search-input" placeholder="ตัวอย่าง: TH6BDAEB0B51" class="flex-1 px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase font-mono">
            <button onclick="searchTracking()" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2.5 rounded-xl transition text-sm flex items-center gap-1.5">
              <span>🔍</span> ค้นหา
            </button>
          </div>
        </div>
      </div>

      <!-- Tracking Results Card -->
      <div id="track-result-container" class="hidden grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Left Column: พัสดุ & ยานพาหนะ -->
        <div class="lg:col-span-5 space-y-4">
          <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <div class="flex items-center justify-between mb-4">
              <span id="track-status-badge" class="px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800">PENDING</span>
              <span id="track-created-at" class="text-xs text-slate-400">2026-10-05</span>
            </div>
            
            <h3 id="track-item-name" class="text-lg font-bold text-slate-900 mb-1">ชื่อพัสดุ</h3>
            <p id="track-category-badge" class="inline-block text-xs px-2.5 py-0.5 rounded-full font-semibold mb-3">STANDARD</p>

            <div class="space-y-2 text-xs text-slate-600 pt-3 border-t border-slate-100">
              <div class="flex justify-between"><span>น้ำหนัก / ปริมาตร:</span> <span id="track-spec" class="font-medium text-slate-800">-</span></div>
              <div class="flex justify-between"><span>มูลค่าที่แจ้งไว้:</span> <span id="track-value" class="font-medium text-slate-800">-</span></div>
              <div class="flex justify-between"><span>ค่าจัดส่งสุทธิ:</span> <span id="track-cost" class="font-bold text-blue-600">-</span></div>
              <div class="flex justify-between"><span>บริการ:</span> <span id="track-service" class="font-medium text-slate-800">-</span></div>
            </div>

            <div class="mt-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
              <div class="font-bold mb-0.5">⚠️ ข้อกำหนดการจัดส่งเฉพาะประเภท:</div>
              <div id="track-requirements">-</div>
            </div>

            <!-- Vehicle Card -->
            <div class="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div class="font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                <span>🚚</span> ยานพาหนะที่รับผิดชอบ:
              </div>
              <div id="track-vehicle-info" class="text-slate-600">-</div>
            </div>

            <!-- Advance Status Button -->
            <button onclick="advanceCurrentStatus()" class="w-full mt-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-xl transition text-sm flex items-center justify-center gap-2">
              <span>⏩</span> เลื่อนสถานะพัสดุสู่ขั้นตอนถัดไป
            </button>
          </div>
        </div>

        <!-- Right Column: ไทม์ไลน์การเดินทาง (Timeline) -->
        <div class="lg:col-span-7 space-y-4">
          <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <h3 class="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <span>📍</span> ไทม์ไลน์การจัดส่งและการแจ้งเตือน (Observer Pattern)
            </h3>
            
            <div id="track-timeline-list" class="space-y-4 border-l-2 border-blue-500 ml-3 pl-4">
              <!-- Rendered via JS -->
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- TAB 4: คลังยานพาหนะ (Fleet) -->
    <div id="tab-fleet" class="tab-content hidden space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-slate-900">คลังยานพาหนะขนส่ง (Fleet Fleet Management)</h2>
          <p class="text-xs text-slate-500">จัดการยานพาหนะตามข้อกำหนดความปลอดภัยและการใช้พื้นที่บรรทุก</p>
        </div>
        <button onclick="loadFleet()" class="text-xs bg-white border border-slate-200 hover:bg-slate-50 px-3 py-2 rounded-lg text-slate-700 transition">
          🔄 รีเฟรชข้อมูลยานพาหนะ
        </button>
      </div>

      <div id="fleet-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <!-- Rendered via JS -->
      </div>
    </div>

    <!-- TAB 5: สรุปสถิติ & แดชบอร์ด (Analytics) -->
    <div id="tab-analytics" class="tab-content hidden space-y-6">
      <!-- 4 KPI Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div class="text-xs font-semibold text-slate-500 uppercase">📦 จำนวนพัสดุทั้งหมด</div>
          <div class="text-2xl font-black text-blue-600 mt-2" id="kpi-total-shipments">0 รายการ</div>
        </div>
        <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div class="text-xs font-semibold text-slate-500 uppercase">💰 รายได้ค่าจัดส่งรวม</div>
          <div class="text-2xl font-black text-emerald-600 mt-2" id="kpi-total-revenue">฿0.00</div>
        </div>
        <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div class="text-xs font-semibold text-slate-500 uppercase">🚚 ยานพาหนะพร้อมใช้</div>
          <div class="text-2xl font-black text-amber-600 mt-2" id="kpi-active-fleet">0 คัน</div>
        </div>
        <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <div class="text-xs font-semibold text-slate-500 uppercase">📈 อัตราบรรทุกเฉลี่ย</div>
          <div class="text-2xl font-black text-indigo-600 mt-2" id="kpi-avg-utilization">0.0%</div>
        </div>
      </div>

      <!-- Breakdown & Logs -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Breakdown by Category -->
        <div class="lg:col-span-5 bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <h3 class="text-base font-bold text-slate-900 mb-3">🏷️ สัดส่วนประเภทสินค้าในระบบ</h3>
          <div id="category-breakdown-list" class="space-y-3 text-sm">
            <!-- Rendered via JS -->
          </div>
        </div>

        <!-- Audit & Notification Logs -->
        <div class="lg:col-span-7 bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
          <h3 class="text-base font-bold text-slate-900 mb-3">🛡️ บันทึกระบบ (System Audit & Alerts)</h3>
          <div id="audit-logs-box" class="h-64 overflow-y-auto space-y-1.5 text-xs font-mono bg-slate-900 text-slate-300 p-4 rounded-xl">
            <!-- Rendered via JS -->
          </div>
        </div>
      </div>
    </div>

  </main>

  <!-- Footer -->
  <footer class="bg-white border-t border-slate-200 py-4 mt-auto">
    <div class="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500">
      ระบบบริหารจัดการขนส่งและพัสดุภัณฑ์ (Logistics & Parcel Management System) • พัฒนาด้วย Python OOP & OOAD Architecture • พร้อมใช้งานบน Vercel
    </div>
  </footer>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-6 right-6 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl text-sm font-medium hidden flex items-center gap-2 z-50 transition transform translate-y-2">
    <span id="toast-icon">✅</span>
    <span id="toast-msg">ข้อความแจ้งเตือน</span>
  </div>

  <script>
    let currentItemType = 'STANDARD';
    let currentTrackedShipment = null;

    // Tab Navigation
    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('bg-blue-600', 'text-white');
        btn.classList.add('text-slate-400');
      });

      const activeContent = document.getElementById('tab-' + tabId);
      const activeBtn = document.getElementById('tab-btn-' + tabId);
      if (activeContent) activeContent.classList.remove('hidden');
      if (activeBtn) {
        activeBtn.classList.add('bg-blue-600', 'text-white');
        activeBtn.classList.remove('text-slate-400');
      }

      if (tabId === 'list') loadShipments();
      if (tabId === 'fleet') loadFleet();
      if (tabId === 'analytics') loadAnalytics();
    }

    // Select Item Type Pill
    function selectItemType(type) {
      currentItemType = type;
      document.querySelectorAll('.type-pill').forEach(btn => {
        btn.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-700');
        btn.classList.add('border-slate-200', 'bg-white', 'text-slate-700');
      });
      const activeBtn = document.getElementById('btn-type-' + type);
      if (activeBtn) {
        activeBtn.classList.remove('border-slate-200', 'bg-white', 'text-slate-700');
        activeBtn.classList.add('border-blue-500', 'bg-blue-50', 'text-blue-700');
      }
      renderDynamicFields();
      calculatePreview();
    }

    // Dynamic Fields Render
    function renderDynamicFields() {
      const container = document.getElementById('dynamic-fields');
      if (currentItemType === 'STANDARD') {
        container.innerHTML = `
          <div class="flex items-center gap-2 text-emerald-700 text-xs font-semibold">
            <span>✅</span> พัสดุมาตรฐานทั่วไป ไม่ต้องใช้อุปกรณ์ควบคุมอุณหภูมิหรือเอกสารวัตถุอันตราย
          </div>
        `;
      } else if (currentItemType === 'FRAGILE') {
        container.innerHTML = `
          <div class="space-y-3 text-xs">
            <div class="font-bold text-slate-800">คุณสมบัติเฉพาะพัสดุแตกหักง่าย (FRAGILE):</div>
            <div>
              <label class="block text-slate-600 mb-1">ระดับการห่อหุ้มกันกระแทก</label>
              <select id="cushioning_level" onchange="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-sm">
                <option value="Standard">Standard (แอร์บับเบิ้ลทั่วไป)</option>
                <option value="Double Layer" selected>Double Layer (บับเบิ้ล 2 ชั้น + โฟมกันกระแทก)</option>
                <option value="Wooden Crate">Wooden Crate (ตีลังไม้พิเศษรอบชิ้นงาน)</option>
              </select>
            </div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" id="requires_insurance" checked onchange="calculatePreview()" class="w-4 h-4 text-blue-600 rounded">
              <span class="text-slate-700 font-medium">ทำประกันคุ้มครองสินค้าแตกหัก (1.5% ของมูลค่าสินค้า)</span>
            </label>
          </div>
        `;
      } else if (currentItemType === 'PERISHABLE') {
        container.innerHTML = `
          <div class="space-y-3 text-xs">
            <div class="font-bold text-slate-800">คุณสมบัติสินค้าควบคุมอุณหภูมิ (PERISHABLE):</div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-slate-600 mb-1">อุณหภูมิเป้าหมาย (°C)</label>
                <input type="number" id="target_temp" value="4.0" step="0.5" oninput="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
              </div>
              <div>
                <label class="block text-slate-600 mb-1">อายุสินค้าก่อนหมดอายุ (ชม.)</label>
                <input type="number" id="expiry_hours" value="24" step="1" oninput="calculatePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
              </div>
            </div>
            <p class="text-[11px] text-emerald-700 font-medium">❄️ ระบบจะจัดสรรยานพาหนะที่มีตู้ห้องเย็นปรับอุณหภูมิให้โดยเฉพาะ</p>
          </div>
        `;
      } else if (currentItemType === 'HAZARDOUS') {
        container.innerHTML = `
          <div class="space-y-3 text-xs">
            <div class="font-bold text-slate-800">คุณสมบัติวัตถุอันตราย/สารเคมี (HAZARDOUS):</div>
            <div>
              <label class="block text-slate-600 mb-1">คลาสวัตถุอันตราย (UN Hazard Class)</label>
              <select id="hazard_class" class="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-sm">
                <option value="Class 3 (Flammable Liquids)">Class 3 (ของเหลวไวไฟ)</option>
                <option value="Class 8 (Corrosive Substances)">Class 8 (สารกัดกร่อน)</option>
                <option value="Class 9 (Miscellaneous Hazardous)">Class 9 (แบตเตอรี่ลิเธียม / อื่นๆ)</option>
              </select>
            </div>
            <div>
              <label class="block text-slate-600 mb-1">เลขที่ใบอนุญาตความปลอดภัย (Safety License ID)</label>
              <input type="text" id="safety_license_id" value="HAZ-LIC-2026-BKK" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
            </div>
          </div>
        `;
      }
    }

    // Build Current Item Payload
    function getItemPayload() {
      const name = document.getElementById('item_name').value.trim() || 'พัสดุทั่วไป';
      const weight = parseFloat(document.getElementById('item_weight').value) || 1.0;
      const volume = parseFloat(document.getElementById('item_volume').value) || 0.01;
      const declared_value = parseFloat(document.getElementById('declared_value').value) || 0.0;

      const payload = {
        item_type: currentItemType,
        name: name,
        weight: weight,
        volume: volume,
        declared_value: declared_value,
      };

      if (currentItemType === 'FRAGILE') {
        const cEl = document.getElementById('cushioning_level');
        const iEl = document.getElementById('requires_insurance');
        payload.cushioning_level = cEl ? cEl.value : 'Double Layer';
        payload.requires_insurance = iEl ? iEl.checked : true;
      } else if (currentItemType === 'PERISHABLE') {
        const tEl = document.getElementById('target_temp');
        const eEl = document.getElementById('expiry_hours');
        payload.target_temperature_celsius = tEl ? parseFloat(tEl.value) : 4.0;
        payload.expiry_hours = eEl ? parseInt(eEl.value) : 24;
      } else if (currentItemType === 'HAZARDOUS') {
        const hEl = document.getElementById('hazard_class');
        const lEl = document.getElementById('safety_license_id');
        payload.hazard_class = hEl ? hEl.value : 'Class 3';
        payload.safety_license_id = lEl ? lEl.value : 'HAZ-LIC-01';
      }

      return payload;
    }

    // Real-Time Price Calculation
    async function calculatePreview() {
      try {
        const item = getItemPayload();
        const dist = parseFloat(document.getElementById('distance_km').value) || 10.0;
        const tier = document.getElementById('service_tier').value;

        const res = await fetch('/api/calculate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ item, distance_km: dist, service_tier: tier })
        });
        const data = await res.json();
        if (data.pricing) {
          document.getElementById('preview-total-cost').innerText = '฿' + data.pricing.total_cost_thb.toLocaleString('th-TH', {minimumFractionDigits: 2});
          document.getElementById('preview-breakdown-text').innerText = `(ค่าส่ง ฿${data.pricing.transport_fee_thb.toFixed(2)} + ค่าดูแลพัสดุ ฿${data.pricing.item_handling_fee_thb.toFixed(2)})`;
          document.getElementById('preview-service-tag').innerText = data.pricing.strategy_name;

          if (data.recommended_vehicle) {
            document.getElementById('preview-vehicle-name').innerText = `[${data.recommended_vehicle.vehicle_type}] ทะเบียน ${data.recommended_vehicle.license_plate}`;
            document.getElementById('preview-vehicle-sub').innerText = `พนักงานขับ: ${data.recommended_vehicle.driver_name} (รับน้ำหนักได้ ${data.recommended_vehicle.max_weight_kg} กก.)`;
          } else {
            document.getElementById('preview-vehicle-name').innerText = '⚠️ ไม่มียานพาหนะที่ตรงเงื่อนไข';
            document.getElementById('preview-vehicle-sub').innerText = data.vehicle_status;
          }
        }
      } catch (err) {
        console.error(err);
      }
    }

    // Submit New Shipment
    async function submitNewShipment() {
      const item = getItemPayload();
      const dist = parseFloat(document.getElementById('distance_km').value) || 10.0;
      const tier = document.getElementById('service_tier').value;
      const s_name = document.getElementById('sender_name').value.trim();
      const s_phone = document.getElementById('sender_phone').value.trim();
      const r_name = document.getElementById('receiver_name').value.trim();
      const r_phone = document.getElementById('receiver_phone').value.trim();
      const r_addr = document.getElementById('receiver_address').value.trim();

      if (!s_name || !r_name) {
        showToast('❌ กรุณากรอกชื่อผู้ส่งและผู้รับให้ครบถ้วน');
        return;
      }

      try {
        const res = await fetch('/api/shipments', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            item,
            sender_name: s_name,
            sender_phone: s_phone,
            receiver_name: r_name,
            receiver_phone: r_phone,
            receiver_address: r_addr,
            distance_km: dist,
            service_tier: tier,
            auto_assign_vehicle: true
          })
        });
        const data = await res.json();
        if (data.success) {
          showToast('🎉 ' + data.message);
          // Navigate to tracking
          document.getElementById('track-search-input').value = data.shipment.tracking_number;
          switchTab('track');
          renderTracking(data.shipment);
        } else {
          showToast('❌ ' + (data.detail || 'เกิดข้อผิดพลาด'));
        }
      } catch (err) {
        showToast('❌ ' + err.message);
      }
    }

    // Load Shipments Table
    async function loadShipments() {
      const cat = document.getElementById('filter-category').value;
      const search = document.getElementById('search-input').value;
      const res = await fetch(`/api/shipments?category=${cat}&search=${encodeURIComponent(search)}`);
      const shipments = await res.json();

      const tbody = document.getElementById('shipments-table-body');
      tbody.innerHTML = '';

      if (shipments.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-400 text-sm">ไม่พบรายการพัสดุ</td></tr>`;
        return;
      }

      shipments.forEach(s => {
        const cat = s.item.item_type;
        const vehPlate = s.assigned_vehicle ? s.assigned_vehicle.license_plate : 'ยังไม่จัดสรร';
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50 transition border-b border-slate-100';
        tr.innerHTML = `
          <td class="py-3 px-4 font-mono font-bold text-blue-600">${s.tracking_number}</td>
          <td class="py-3 px-4 font-medium text-slate-800">${s.item.name}</td>
          <td class="py-3 px-4"><span class="px-2 py-0.5 rounded-full text-xs font-semibold badge-${cat}">${cat}</span></td>
          <td class="py-3 px-4 text-slate-600">${s.receiver.name}</td>
          <td class="py-3 px-4 text-slate-600">${vehPlate}</td>
          <td class="py-3 px-4 text-right font-semibold text-slate-900">฿${s.total_cost_thb.toLocaleString('th-TH', {minimumFractionDigits: 2})}</td>
          <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">${s.status}</span></td>
          <td class="py-3 px-4 text-center">
            <button onclick="inspectTracking('${s.tracking_number}')" class="text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 font-semibold px-2.5 py-1 rounded-lg transition">
              ดูไทม์ไลน์
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    function inspectTracking(trackNo) {
      document.getElementById('track-search-input').value = trackNo;
      switchTab('track');
      searchTracking();
    }

    // Search Tracking
    async function searchTracking() {
      const trackNo = document.getElementById('track-search-input').value.trim().toUpperCase();
      if (!trackNo) return;
      try {
        const res = await fetch(`/api/shipments/${trackNo}`);
        if (!res.ok) {
          showToast('❌ ไม่พบหมายเลขพัสดุนี้');
          return;
        }
        const s = await res.json();
        renderTracking(s);
      } catch (err) {
        showToast('❌ ' + err.message);
      }
    }

    function renderTracking(s) {
      currentTrackedShipment = s;
      document.getElementById('track-result-container').classList.remove('hidden');

      document.getElementById('track-status-badge').innerText = s.status;
      document.getElementById('track-created-at').innerText = 'สร้างเมื่อ: ' + s.created_at;
      document.getElementById('track-item-name').innerText = s.item.name;

      const catBadge = document.getElementById('track-category-badge');
      catBadge.innerText = s.item.item_type;
      catBadge.className = `inline-block text-xs px-2.5 py-0.5 rounded-full font-semibold mb-3 badge-${s.item.item_type}`;

      document.getElementById('track-spec').innerText = `${s.item.weight_kg} กก. | ${s.item.volume_m3} m³`;
      document.getElementById('track-value').innerText = `฿${s.item.declared_value_thb.toLocaleString('th-TH')}`;
      document.getElementById('track-cost').innerText = `฿${s.total_cost_thb.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
      document.getElementById('track-service').innerText = s.service_type;
      document.getElementById('track-requirements').innerText = s.item.special_requirements;

      if (s.assigned_vehicle) {
        document.getElementById('track-vehicle-info').innerHTML = `
          <strong>[${s.assigned_vehicle.vehicle_type}]</strong> ทะเบียน: ${s.assigned_vehicle.license_plate}<br>
          คนขับ: ${s.assigned_vehicle.driver_name} (บรรทุกแล้ว ${s.assigned_vehicle.current_weight_kg}/${s.assigned_vehicle.max_weight_kg} กก.)
        `;
      } else {
        document.getElementById('track-vehicle-info').innerText = 'ยังไม่ได้จัดสรรยานพาหนะ';
      }

      // Render Timeline
      const timelineList = document.getElementById('track-timeline-list');
      timelineList.innerHTML = '';
      s.tracking_history.forEach((ev, idx) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'relative';
        itemDiv.innerHTML = `
          <div class="absolute -left-[25px] top-1 w-4 h-4 rounded-full bg-blue-500 border-2 border-white"></div>
          <div class="text-xs text-slate-400 font-mono">${ev.timestamp}</div>
          <div class="text-sm font-bold text-slate-800">${ev.status} • ${ev.location}</div>
          <div class="text-xs text-slate-600 mt-0.5">${ev.message}</div>
        `;
        timelineList.appendChild(itemDiv);
      });
    }

    async function advanceCurrentStatus() {
      if (!currentTrackedShipment) return;
      try {
        const res = await fetch(`/api/shipments/${currentTrackedShipment.tracking_number}/advance`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ location: 'ศูนย์กระจายสินค้าปลายทาง', message: 'สินค้าผ่านการตรวจสอบขั้นตอนต่อไป' })
        });
        const data = await res.json();
        if (data.success) {
          showToast('✅ ' + data.message);
          renderTracking(data.shipment);
        } else {
          showToast('⚠️ ' + (data.detail || 'ไม่สามารถเลื่อนสถานะได้'));
        }
      } catch (err) {
        showToast('❌ ' + err.message);
      }
    }

    // Load Fleet
    async function loadFleet() {
      const res = await fetch('/api/fleet');
      const data = await res.json();
      const grid = document.getElementById('fleet-grid');
      grid.innerHTML = '';

      data.vehicles.forEach(v => {
        const pct = v.utilization_pct;
        const card = document.createElement('div');
        card.className = 'bg-white p-5 rounded-2xl shadow-sm border border-slate-200';
        card.innerHTML = `
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-blue-600 uppercase tracking-wide">${v.vehicle_type}</span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${v.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}">
              ${v.is_active ? '🟢 พร้อมใช้งาน' : '🔴 หยุดพัก'}
            </span>
          </div>
          <div class="text-base font-bold text-slate-900">ทะเบียน: ${v.license_plate}</div>
          <div class="text-xs text-slate-500 mb-3">พนักงานขับ: ${v.driver_name}</div>
          
          <div class="space-y-1 text-xs text-slate-600 mb-3">
            <div class="flex justify-between">
              <span>น้ำหนักบรรทุก:</span>
              <span class="font-medium">${v.current_weight_kg} / ${v.max_weight_kg} กก. (${pct}%)</span>
            </div>
            <div class="w-full bg-slate-100 rounded-full h-2">
              <div class="bg-blue-600 h-2 rounded-full" style="width: ${Math.min(100, pct)}%"></div>
            </div>
            <div class="flex justify-between pt-1">
              <span>พัสดุบนรถ:</span>
              <span class="font-bold text-slate-800">${v.loaded_items_count} ชิ้น</span>
            </div>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    // Load Analytics
    async function loadAnalytics() {
      const res = await fetch('/api/analytics');
      const data = await res.json();
      const m = data.metrics;

      document.getElementById('kpi-total-shipments').innerText = `${m.total_shipments} รายการ`;
      document.getElementById('kpi-total-revenue').innerText = '฿' + m.total_revenue_thb.toLocaleString('th-TH', {minimumFractionDigits: 2});
      document.getElementById('kpi-active-fleet').innerText = `${m.fleet_stats.active_vehicles} / ${m.fleet_stats.total_vehicles} คัน`;
      document.getElementById('kpi-avg-utilization').innerText = `${m.fleet_stats.avg_utilization_pct}%`;

      // Category Breakdown List
      const catList = document.getElementById('category-breakdown-list');
      catList.innerHTML = '';
      for (const [k, v] of Object.entries(m.by_category)) {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between p-2 rounded-lg bg-slate-50';
        row.innerHTML = `
          <span class="font-medium text-slate-700">${k}</span>
          <span class="font-bold text-slate-900">${v} ชิ้น</span>
        `;
        catList.appendChild(row);
      }

      // Audit Logs
      const auditBox = document.getElementById('audit-logs-box');
      auditBox.innerHTML = '';
      data.audit_logs.forEach(log => {
        const p = document.createElement('div');
        p.innerText = log;
        auditBox.appendChild(p);
      });
    }

    function showToast(msg) {
      const toast = document.getElementById('toast');
      document.getElementById('toast-msg').innerText = msg;
      toast.classList.remove('hidden');
      setTimeout(() => toast.classList.add('hidden'), 4000);
    }

    // Initial boot
    window.addEventListener('DOMContentLoaded', () => {
      renderDynamicFields();
      calculatePreview();
    });
  </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)


def run_web_server(host: str = "0.0.0.0", port: int = 8000):
    """รัน Web Server ในเครื่องด้วย Uvicorn"""
    import uvicorn
    print(f"\n🌐 กำลังเริ่มต้น Web Application ที่ http://localhost:{port}")
    print(f"📖 ดูเอกสาร API ได้ที่ http://localhost:{port}/docs\n")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_web_server()
