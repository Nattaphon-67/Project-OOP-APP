"""
Tests for Item models and subclasses.
Testing Encapsulation, Validation, and Polymorphic fee calculations.
"""

import unittest
from src.models.item import (
    Item,
    ItemType,
    StandardParcel,
    FragileParcel,
    PerishableParcel,
    HazardousParcel,
    CushioningLevel,
)
from src.factory.item_factory import ItemFactory


class TestItemModels(unittest.TestCase):

    def test_standard_parcel_creation_and_fee(self):
        item = StandardParcel("ITM-001", "เอกสารสัญญา", weight=1.5, volume=0.005, declared_value=300)
        self.assertEqual(item.get_item_type(), ItemType.STANDARD)
        self.assertEqual(item.weight, 1.5)
        self.assertEqual(item.name, "เอกสารสัญญา")
        # Fee: weight * 10 = 15, but minimum is 20
        self.assertEqual(item.calculate_handling_fee(), 20.0)

        # Standard with heavier weight: 5.0 kg * 10 = 50.0
        heavy_std = StandardParcel("ITM-002", "กล่องหนังสือ", weight=5.0, volume=0.02)
        self.assertEqual(heavy_std.calculate_handling_fee(), 50.0)

    def test_fragile_parcel_with_insurance(self):
        item = FragileParcel(
            item_id="FRG-001",
            name="จอคอมพิวเตอร์ OLED",
            weight=6.0,
            volume=0.08,
            declared_value=20000.0,
            cushioning_level=CushioningLevel.DOUBLE_LAYER,
            requires_insurance=True,
        )
        self.assertEqual(item.get_item_type(), ItemType.FRAGILE)
        # Base: 50 + Double Layer: 70 + Insurance 1.5% of 20000 = 300 -> Total: 420.0
        self.assertEqual(item.calculate_handling_fee(), 420.0)
        self.assertIn("ระวังแตกหัก", item.get_special_requirements())

    def test_perishable_parcel_frozen_and_urgent(self):
        item = PerishableParcel(
            item_id="PRS-001",
            name="เนื้อวากิวแช่แข็ง",
            weight=3.0,
            volume=0.015,
            declared_value=4500.0,
            target_temperature_celsius=-18.0,
            expiry_hours=12,
        )
        self.assertEqual(item.get_item_type(), ItemType.PERISHABLE)
        # Base: 120 + Frozen (<0): 80 + Urgency (<=24h): 50 -> Total: 250.0
        self.assertEqual(item.calculate_handling_fee(), 250.0)
        self.assertIn("แช่แข็ง", item.get_special_requirements())

    def test_hazardous_parcel(self):
        item = HazardousParcel(
            item_id="HAZ-001",
            name="กรดซัลฟิวริกบริสุทธิ์",
            weight=10.0,
            volume=0.03,
            declared_value=5000.0,
            hazard_class="Class 8 (Corrosive)",
            safety_license_id="LIC-HAZ-99",
        )
        self.assertEqual(item.get_item_type(), ItemType.HAZARDOUS)
        # Base: 150 + 10kg * 25 = 400.0
        self.assertEqual(item.calculate_handling_fee(), 400.0)
        self.assertIn("LIC-HAZ-99", item.get_special_requirements())

    def test_encapsulation_validation_errors(self):
        # Negative weight
        with self.assertRaises(ValueError):
            StandardParcel("ITM-X", "สินค้า", weight=-5.0, volume=0.01)

        # Zero volume
        with self.assertRaises(ValueError):
            StandardParcel("ITM-X", "สินค้า", weight=1.0, volume=0.0)

        # Empty name
        with self.assertRaises(ValueError):
            StandardParcel("ITM-X", "   ", weight=1.0, volume=0.01)

    def test_item_factory_creation(self):
        item = ItemFactory.create_item(
            ItemType.FRAGILE,
            name="แจกันโบราณ",
            weight=2.0,
            volume=0.02,
            declared_value=8000.0,
            cushioning_level="Wooden Crate",
            requires_insurance=True,
        )
        self.assertIsInstance(item, FragileParcel)
        self.assertEqual(item.cushioning_level, CushioningLevel.WOODEN_CRATE)


if __name__ == "__main__":
    unittest.main()
