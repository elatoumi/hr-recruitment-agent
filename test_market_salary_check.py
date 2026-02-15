import unittest
from market_salary_check import check_salary, batch_check, SALARY_RANGES


class TestMarketSalaryCheck(unittest.TestCase):
    
    def test_salary_within_range(self):
        result = check_salary("Software Engineer", 80000)
        self.assertTrue(result["valid"])
        self.assertFalse(result["flagged"])
    
    def test_salary_too_low(self):
        result = check_salary("Software Engineer", 50000)
        self.assertFalse(result["valid"])
        self.assertTrue(result["flagged"])
        self.assertEqual(result["difference"], 10000)
    
    def test_salary_above_range(self):
        result = check_salary("Software Engineer", 160000)
        self.assertTrue(result["valid"])
        self.assertFalse(result["flagged"])
    
    def test_unknown_position(self):
        result = check_salary("Unknown Position", 70000)
        self.assertTrue(result["valid"])
        self.assertIn("No market data", result["message"])
    
    def test_case_insensitive(self):
        result1 = check_salary("Software Engineer", 80000)
        result2 = check_salary("software engineer", 80000)
        self.assertEqual(result1["valid"], result2["valid"])
    
    def test_batch_check(self):
        offers = [
            {"position": "Software Engineer", "salary": 75000},
            {"position": "Data Scientist", "salary": 60000},
        ]
        results = batch_check(offers)
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["valid"])
        self.assertFalse(results[1]["valid"])


if __name__ == "__main__":
    unittest.main()
