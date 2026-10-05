"""
API Route Tests for Vercel Web Application
"""

import unittest
from api.index import app, index_page, get_shipments, get_analytics_api, calculate_estimate, CalculateRequest, ItemInput


class TestAPIEndpoints(unittest.TestCase):

    def test_index_page_returns_html(self):
        res = index_page()
        self.assertEqual(res.status_code, 200)
        self.assertIn("LOGISTICS & PARCEL SYSTEM", res.body.decode("utf-8"))

    def test_get_shipments_returns_list(self):
        res = get_shipments()
        self.assertIsInstance(res, list)
        self.assertGreaterEqual(len(res), 4)

    def test_get_analytics(self):
        res = get_analytics_api()
        self.assertIn("metrics", res)
        self.assertIn("total_shipments", res["metrics"])
        self.assertGreaterEqual(res["metrics"]["total_shipments"], 4)

    def test_calculate_estimate_endpoint(self):
        req = CalculateRequest(
            item=ItemInput(
                item_type="PERISHABLE",
                name="นมสดพาสเจอร์ไรส์",
                weight=2.0,
                volume=0.005,
                declared_value=120.0,
                target_temperature_celsius=4.0,
                expiry_hours=48,
            ),
            distance_km=15.0,
            service_tier="EXPRESS",
        )
        res = calculate_estimate(req)
        self.assertIn("pricing", res)
        self.assertIn("recommended_vehicle", res)
        self.assertEqual(res["recommended_vehicle"]["vehicle_type"], "REFRIGERATED_TRUCK")


if __name__ == "__main__":
    unittest.main()
