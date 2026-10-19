"""Command-line preview for ClubBudget."""
from service import list_records, summary, filter_records

def main():
    rows = list_records()
    print("ClubBudget — Student Starter")
    print(f"Loaded {len(rows)} expenses")
    for row in rows:
        print(f"#{row.id} | {row.title} | {row.category} | {row.status} | {row.amount}")
    query = input("Search (Enter to skip): ").strip()
    category = input("Category filter (Enter to skip): ").strip() or None
    status = input("Status filter (Enter to skip): ").strip() or None
    try: results = filter_records(rows, query, category, status)
    except ValueError as exc:
        print(f"Invalid filter: {exc}")
        return
    if not results: print("No expenses match your filters.")
    else:
        for row in results: print(f"#{row.id} | {row.title} | {row.status} | {row.amount}")
    print("Summary:", summary(rows))

if __name__ == "__main__": main()
