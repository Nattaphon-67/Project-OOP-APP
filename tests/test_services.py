"""
Integration tests for LogisticsService (Facade, Observers, Fleet).
"""

import unittest
from src.services.logistics_service import LogisticsService
from src.factory.item_factory import ItemFactory
from src.models.item import ItemType
from src.models.customer import Customer, Address
from src.models.shipment import ShipmentStatus
from src.models.vehicle import VehicleType


class TestLogisticsServiceIntegration(unittest.TestCase):

    def setUp(self):
        self.service = LogisticsService()
        self.service.seed_initial_data()

    def test_auto_fleet_allocation_perishable(self):
        # Perishable goods MUST be allocated to REFRIGERATED_TRUCK
        cold_item = ItemFactory.create_item(
            ItemType.PERISHABLE,
            name="ยาควบคุมความเย็น",
            weight=5.0,
            volume=0.02,
            target_temperature_celsius=3.0,
        )
        sender = Customer("S-01", "Lab", "081-111-1111", "s@lab.com", Address("A", "B", "C", "10100"))
        receiver = Customer("R-01", "Clinic", "089-222-2222", "r@clinic.com", Address("D", "E", "F", "10200"))

        shipment, _ = self.service.create_shipment(
            item=cold_item,
            sender=sender,
            receiver=receiver,
            distance_km=20.0,
            service_tier="EXPRESS",
            auto_assign_vehicle=True,
        )

        self.assertIsNotNone(shipment.assigned_vehicle)
        self.assertEqual(shipment.assigned_vehicle.get_vehicle_type(), VehicleType.REFRIGERATED_TRUCK)

    def test_observer_receives_status_updates(self):
        item = ItemFactory.create_item(ItemType.STANDARD, name="หนังสือ", weight=1.0, volume=0.005)
        sender = Customer("S-02", "Shop", "081-333-3333", "s@shop.com", Address("A", "B", "C", "10100"))
        receiver = Customer("R-02", "Customer", "089-444-4444", "r@cust.com", Address("D", "E", "F", "10200"))

        shipment, _ = self.service.create_shipment(item, sender, receiver, distance_km=5.0)
        track_no = shipment.tracking_number

        initial_sms_count = len(self.service.sms_notifier.sent_messages)

        # Advance status
        success, _ = self.service.advance_shipment_status(track_no, "ศูนย์แยก", "กำลังเดินทาง")
        self.assertTrue(success)

        # Check observer triggered
        new_sms_count = len(self.service.sms_notifier.sent_messages)
        self.assertGreater(new_sms_count, initial_sms_count)

    def test_dashboard_metrics(self):
        metrics = self.service.get_dashboard_metrics()
        self.assertGreaterEqual(metrics["total_shipments"], 4)
        self.assertGreater(metrics["total_revenue_thb"], 0)
        self.assertIn("STANDARD", metrics["by_category"])
        self.assertIn("FRAGILE", metrics["by_category"])
        self.assertIn("PERISHABLE", metrics["by_category"])
        self.assertIn("HAZARDOUS", metrics["by_category"])


if __name__ == "__main__":
    unittest.main()
