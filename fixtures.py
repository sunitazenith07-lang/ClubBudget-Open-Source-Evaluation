"""Deterministic fixtures for ClubBudget."""
from copy import deepcopy
from models import RECORD_CLASS
_SAMPLE = [
{"id":1,"title":"Projector Cable Purchase","club":"Club A","category":"Supplies","amount":50.0,"status":"Pending","description":"HDMI cables","budget_limit":500.0,"vendor":"Campus Store","receipt_ref":"REC-001"},
{"id":2,"title":"Refreshments","club":"Club B","category":"Food","amount":150.0,"status":"Approved","description":"Club meetup refreshments","budget_limit":800.0,"vendor":"Cafe","receipt_ref":"REC-002"},
{"id":3,"title":"Auditorium Booking","club":"Club A","category":"Venue","amount":300.0,"status":"Paid","description":"Event hall booking","budget_limit":1000.0,"vendor":"University","receipt_ref":"REC-003"},
{"id":4,"title":"Taxi Reimbursement","club":"Club C","category":"Travel","amount":70.0,"status":"Rejected","description":"Local travel expense","budget_limit":400.0,"vendor":"Taxi Co","receipt_ref":"REC-004"},
{"id":5,"title":"Workshop Kit","club":"Club A","category":"Supplies","amount":120.0,"status":"Pending","description":"Components for session","budget_limit":500.0,"vendor":"Parts Hub","receipt_ref":"REC-005"},
{"id":6,"title":"Poster Printing","club":"Club B","category":"Venue","amount":40.0,"status":"Approved","description":"Promotion posters","budget_limit":1000.0,"vendor":"Print Shop","receipt_ref":"REC-006"}]
def make_records():
    return [RECORD_CLASS.from_dict(row) for row in deepcopy(_SAMPLE)]
