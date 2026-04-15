from backend.config import DEFAULT_BUDGET

def parse_budget(value: Any, default: int = DEFAULT_BUDGET) -> int:
    try:
        budget = int(value)
    except (TypeError, ValueError):
        return default
    return max(500, budget)