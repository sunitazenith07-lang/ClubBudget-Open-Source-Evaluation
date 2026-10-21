from models import new_account


def sample_account():
    return new_account('ACCT-1001')


def sample_transactions():
    return [{'transaction_id':'TX-1','account_id':'ACCT-1001','date':'2026-10-21','amount_paise':259900},{'transaction_id':'TX-2','account_id':'ACCT-1001','date':'2026-10-21','amount_paise':259900},{'transaction_id':'TX-3','account_id':'ACCT-2002','date':'2026-10-21','amount_paise':259900}]


def sample_rules():
    return {'points_per_100_rupees':1,'bonus_percent':10,'cap_points':100}
