from __future__ import annotations

from fixtures import sample_rules, sample_transactions
from service import calculate_points, flag_repeat_transactions


def main() -> None:
    rules = sample_rules()
    points = calculate_points(
        259900,
        rules["points_per_100_rupees"],
        rules["bonus_percent"],
        rules["cap_points"],
    )
    print("Points example:", points)
    repeats = flag_repeat_transactions(sample_transactions())
    print("Repeat warnings:", repeats)


if __name__ == "__main__":
    main()
