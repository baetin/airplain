from datetime import datetime, timedelta

from datetime import datetime, timedelta

def generate_date_range(base_date_str: str, days: int = 7):
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
    today = datetime.today().date()
    return [
        base_date + timedelta(days=offset)
        for offset in range(-days, days + 1)
        if base_date + timedelta(days=offset) >= today  # 과거 제외
    ]
