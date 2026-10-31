def new_account(account_id: str) -> dict:
    return {'account_id':account_id,'points_balance':0,'processed_event_ids':[],'transactions':{},'ledger':[]}
