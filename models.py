"""Domain model for ClubBudget."""
from dataclasses import asdict, dataclass

VALID_STATUSES = ["Pending", "Approved", "Rejected", "Paid"]
VALID_CATEGORIES = ["Supplies", "Food", "Venue", "Travel"]
FIELD_NAMES = ["id", "title", "club", "category", "amount", "status", "description", "budget_limit", "vendor", "receipt_ref"]

@dataclass
class Expense:
    id: int
    title: str
    club: str
    category: str
    amount: float
    status: str
    description: str
    budget_limit: float
    vendor: str
    receipt_ref: str

    @property
    def name(self): return str(self.title)

    @property
    def searchable_text(self):
        return " ".join(str(getattr(self, f, "")) for f in ["title", "club", "category", "vendor", "description", "receipt_ref"])

    def to_dict(self): return asdict(self)

    def validate(self):
        # Intentionally incomplete for this student evaluation.
        return None

    @classmethod
    def from_dict(cls, row):
        if not isinstance(row, dict):
            raise ValueError("Each record must be a JSON object")
        missing = set(FIELD_NAMES).difference(row)
        if missing:
            raise ValueError("Missing fields: " + ", ".join(sorted(missing)))
        # Domain validation is intentionally incomplete.
        return cls(**{key: row[key] for key in FIELD_NAMES})

RECORD_CLASS = Expense
