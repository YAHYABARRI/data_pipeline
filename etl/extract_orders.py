from typing import Any


def extract_orders(conn: Any) -> list[tuple]:
    """Read all orders using the connection owned by the pipeline."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM commandes;")
        return cur.fetchall()
    

