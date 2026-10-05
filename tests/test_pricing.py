"""
Tests for Pricing Strategies (Strategy Pattern).
"""

import unittest
from src.models.item import StandardParcel
from src.strategies.pricing import (
    StandardPricingStrategy,
    ExpressPricingStrategy,
    SameDayPricingStrategy,
)


class TestPricingStrategies(unittest.TestCase):

    def setUp(self):
        # 2 kg standard item -> handling fee: 20.0 THB (minimum)
        self.item = StandardParcel("I-P01", "สินค้าทดสอบ", weight=2.0, volume=0.01)

    def test_standard_pricing(self):
        strat = StandardPricingStrategy()
        # Distance = 10 km -> 40.0 + (10 * 3.5 = 35) + 20 (handling) = 95.0
        cost = strat.calculate_cost(self.item, distance_km=10.0)
        self.assertEqual(cost, 95.0)

    def test_express_pricing(self):
        strat = ExpressPricingStrategy()
        # Distance = 10 km -> 70.0 + (10 * 6.0 = 60) + 50 (urgent) + 20 (handling) = 200.0
        cost = strat.calculate_cost(self.item, distance_km=10.0)
        self.assertEqual(cost, 200.0)

    def test_same_day_pricing(self):
        strat = SameDayPricingStrategy()
        # Distance = 10 km -> 120.0 + (10 * 10.0 = 100) + 100 (instant) + 20 (handling) = 340.0
        cost = strat.calculate_cost(self.item, distance_km=10.0)
        self.assertEqual(cost, 340.0)

    def test_pricing_breakdown(self):
        strat = StandardPricingStrategy()
        bd = strat.get_breakdown(self.item, distance_km=20.0)
        self.assertEqual(bd["distance_km"], 20.0)
        self.assertEqual(bd["item_handling_fee_thb"], 20.0)
        # Transport fee: 40 + (20 * 3.5) = 110.0
        self.assertEqual(bd["transport_fee_thb"], 110.0)
        self.assertEqual(bd["total_cost_thb"], 130.0)


if __name__ == "__main__":
    unittest.main()
