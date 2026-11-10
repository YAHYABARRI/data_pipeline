from typing import Any


def load_summary(conn: Any, summary: dict[str, Any]) -> None:
    """Persist the transformed summary using the pipeline connection."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO order_summary (nbr_commandes, somme, moyenne)
            VALUES (%s, %s, %s);
            """,
            (
                summary["nbr_commandes"],
                summary["somme"],
                summary["moyenne"],
            ),
        )
    
