"""
Tests for Vehicle models and fleet allocation rules.
Testing constraints, capacity, and polymorphism.
"""

import unittest
from src.models.item import (
    StandardParcel,
    FragileParcel,
    PerishableParcel,
    HazardousParcel,
)
from src.models.vehicle import (
    Motorcycle,
    Van,
    RefrigeratedTruck,
    HeavyTruck,
    VehicleType,
)


class TestVehicleModels(unittest.TestCase):

    def setUp(self):
        self.motorcycle = Motorcycle("V-M01", "1กก-1111 กทม.", "สมเกียรติ")
        self.van = Van("V-VAN01", "ฮฮ-2222 กทม.", "วิชัย")
        self.ref_truck = RefrigeratedTruck("V-REF01", "70-3333 กทม.", "ประสิทธิ์", min_temp_celsius=-20.0, max_temp_celsius=6.0)
        self.heavy_truck = HeavyTruck("V-HVY01", "71-4444 กทม.", "สมศักดิ์", has_hazmat_permit=True)

    def test_motorcycle_restrictions(self):
        # Motorcycle can carry standard light goods
        std_item = StandardParcel("I-01", "ซองเอกสาร", weight=1.0, volume=0.002)
        can_carry, _ = self.motorcycle.can_transport(std_item)
        self.assertTrue(can_carry)

        # Motorcycle CANNOT carry hazardous goods
        haz_item = HazardousParcel("I-02", "สารเคมี", weight=2.0, volume=0.01, declared_value=500, hazard_class="Class 3", safety_license_id="LIC-1")
        can_carry_haz, reason = self.motorcycle.can_transport(haz_item)
        self.assertFalse(can_carry_haz)
        self.assertIn("ไม่ได้รับอนุญาต", reason)

        # Motorcycle CANNOT carry perishable goods
        peri_item = PerishableParcel("I-03", "นมสด", weight=1.0, volume=0.005, declared_value=100, target_temperature_celsius=4.0)
        can_carry_peri, _ = self.motorcycle.can_transport(peri_item)
        self.assertFalse(can_carry_peri)

        # Motorcycle weight capacity limit (> 25kg total or > 15kg single)
        heavy_item = StandardParcel("I-04", "ดัมเบล", weight=18.0, volume=0.01)
        can_carry_heavy, _ = self.motorcycle.can_transport(heavy_item)
        self.assertFalse(can_carry_heavy)

    def test_van_restrictions(self):
        std_item = StandardParcel("I-05", "กล่องเสื้อผ้า", weight=50.0, volume=0.5)
        can_carry, _ = self.van.can_transport(std_item)
        self.assertTrue(can_carry)

        # Van cannot carry perishable requiring refrigeration
        peri_item = PerishableParcel("I-06", "ยาชีววัตถุ", weight=2.0, volume=0.01, declared_value=5000, target_temperature_celsius=4.0)
        can_carry_peri, reason = self.van.can_transport(peri_item)
        self.assertFalse(can_carry_peri)
        self.assertIn("ห้องเย็น", reason)

    def test_refrigerated_truck_rules(self):
        peri_item = PerishableParcel("I-07", "วัคซีน", weight=5.0, volume=0.02, declared_value=20000, target_temperature_celsius=2.0)
        can_carry, _ = self.ref_truck.can_transport(peri_item)
        self.assertTrue(can_carry)

        # Refrigerated truck CANNOT carry hazardous goods to prevent food/med contamination
        haz_item = HazardousParcel("I-08", "น้ำมันก๊าด", weight=10.0, volume=0.02, declared_value=1000, hazard_class="Class 3", safety_license_id="LIC-2")
        can_carry_haz, _ = self.ref_truck.can_transport(haz_item)
        self.assertFalse(can_carry_haz)

    def test_loading_and_capacity_tracking(self):
        item1 = StandardParcel("I-09", "เครื่องพิมพ์", weight=10.0, volume=0.02)
        success, _ = self.van.load_item(item1)
        self.assertTrue(success)
        self.assertEqual(self.van.current_weight_load(), 10.0)
        self.assertEqual(len(self.van.loaded_items), 1)

        # Unload
        unloaded = self.van.unload_item("I-09")
        self.assertTrue(unloaded)
        self.assertEqual(self.van.current_weight_load(), 0.0)
        self.assertEqual(len(self.van.loaded_items), 0)


if __name__ == "__main__":
    unittest.main()
