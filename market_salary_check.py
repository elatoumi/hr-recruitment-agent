SALARY_RANGES = {
    "software_engineer": {"min": 60000, "max": 150000},
    "senior_software_engineer": {"min": 90000, "max": 180000},
    "data_scientist": {"min": 70000, "max": 160000},
    "product_manager": {"min": 80000, "max": 170000},
    "designer": {"min": 55000, "max": 130000},
    "marketing_manager": {"min": 60000, "max": 140000},
    "sales_representative": {"min": 45000, "max": 120000},
    "devops_engineer": {"min": 75000, "max": 155000},
    "project_manager": {"min": 65000, "max": 145000},
    "qa_engineer": {"min": 50000, "max": 110000},
}


def check_salary(position, offered_salary):
    position_key = position.lower().replace(" ", "_")
    
    if position_key not in SALARY_RANGES:
        return {
            "valid": True,
            "message": f"No market data available for {position}",
            "position": position,
            "offered_salary": offered_salary
        }
    
    range_data = SALARY_RANGES[position_key]
    min_salary = range_data["min"]
    max_salary = range_data["max"]
    
    if offered_salary < min_salary:
        return {
            "valid": False,
            "flagged": True,
            "message": f"Salary too low for {position}. Offered: ${offered_salary:,}, Market min: ${min_salary:,}",
            "position": position,
            "offered_salary": offered_salary,
            "market_min": min_salary,
            "market_max": max_salary,
            "difference": min_salary - offered_salary
        }
    
    if offered_salary > max_salary:
        return {
            "valid": True,
            "flagged": False,
            "message": f"Salary above market range for {position}. Offered: ${offered_salary:,}, Market max: ${max_salary:,}",
            "position": position,
            "offered_salary": offered_salary,
            "market_min": min_salary,
            "market_max": max_salary
        }
    
    return {
        "valid": True,
        "flagged": False,
        "message": f"Salary within market range for {position}",
        "position": position,
        "offered_salary": offered_salary,
        "market_min": min_salary,
        "market_max": max_salary
    }


def batch_check(offers):
    results = []
    for offer in offers:
        result = check_salary(offer["position"], offer["salary"])
        results.append(result)
    return results


if __name__ == "__main__":
    test_offers = [
        {"position": "Software Engineer", "salary": 75000},
        {"position": "Software Engineer", "salary": 45000},
        {"position": "Senior Software Engineer", "salary": 120000},
        {"position": "Data Scientist", "salary": 60000},
    ]
    
    print("Market Salary Check Results:\n")
    for offer in test_offers:
        result = check_salary(offer["position"], offer["salary"])
        print(f"{result['message']}")
        if result.get("flagged"):
            print(f"  ⚠ FLAGGED - Below market by ${result['difference']:,}")
        print()
