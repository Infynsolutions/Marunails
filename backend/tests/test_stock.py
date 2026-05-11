"""
Unit tests for stock calculation invariants.
Pure Python — no Supabase, no DB, no HTTP.
"""


def _compute_stock(movements: list[dict]) -> int:
    """Mirror of the product_stock view logic."""
    total = 0
    for m in movements:
        t = m["type"]
        q = m["quantity"]
        if t == "entrada":
            total += q
        elif t in ("salida", "venta"):
            total -= q
        elif t == "ajuste":
            total += q  # quantity is signed for ajuste
    return total


def test_stock_formula_basic():
    movements = [
        {"type": "entrada", "quantity": 10},
        {"type": "venta",   "quantity": 3},
        {"type": "salida",  "quantity": 2},
    ]
    assert _compute_stock(movements) == 5


def test_stock_ajuste_negativo():
    movements = [
        {"type": "entrada", "quantity": 10},
        {"type": "ajuste",  "quantity": -4},  # pérdida/merma
    ]
    assert _compute_stock(movements) == 6


def test_sheets_enabled_guard():
    def is_sheets_allowed(tenant: dict) -> bool:
        return (tenant.get("config") or {}).get("sheets_enabled", False)

    assert is_sheets_allowed({"config": {"sheets_enabled": True}}) is True
    assert is_sheets_allowed({"config": {"sheets_enabled": False}}) is False
    assert is_sheets_allowed({"config": {}}) is False
    assert is_sheets_allowed({}) is False
