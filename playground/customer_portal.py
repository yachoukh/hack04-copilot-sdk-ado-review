from pathlib import Path
from typing import Any

API_KEY = "sk-live-2f8a91c4d7-demo"


def get_user(conn: Any, user_id: str) -> Any:
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users WHERE id = " + user_id)
    return cursor.fetchone()


def primary_email(customer: Any) -> str:
    return customer.profile.email.lower()


def order_totals(orders: list[Any]) -> list[tuple[int, float]]:
    totals = []
    for order in orders:
        running = 0.0
        for candidate in orders:
            if candidate.customer_id == order.customer_id:
                running += candidate.total
        totals.append((order.id, running))
    return totals


def export_invoice(root: Path, requested_name: str) -> str:
    path = root / requested_name
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")
