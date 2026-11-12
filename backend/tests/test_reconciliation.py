from app.reconciliation import reconcile_transactions, reconcile_positions, validate_rows

def test_transaction_matched_and_field_breaks():
    c=[{"transaction_id":"T1","account":"A","security":"IBM","quantity":"10","net_amount":"100","currency":"USD","trade_date":"2026-01-01"}]
    i=[{"transaction_id":"T1","account":"A","security":"IBM","quantity":"9","net_amount":"100.50","currency":"EUR","trade_date":"2026-01-02"}]
    r=reconcile_transactions(c,i)[0]
    assert r["status"]=="BREAK"
    assert set(r["break_types"])=={"Quantity mismatch","Amount mismatch","Currency mismatch","Trade date mismatch"}

def test_missing_both_sides_are_reported():
    r=reconcile_transactions([{"transaction_id":"C1","account":"A","security":"X","quantity":1,"currency":"USD"}],[{"transaction_id":"I1","account":"A","security":"Y","quantity":1,"currency":"USD"}])
    assert len(r)==2
    assert {x["break_types"][0] for x in r}=={"Missing internal","Missing custodian"}

def test_position_quantity_and_market_value():
    c=[{"account":"A","security":"IBM","currency":"USD","quantity":10,"market_value":100}]
    i=[{"account":"A","security":"IBM","currency":"USD","quantity":9,"market_value":95}]
    r=reconcile_positions(c,i)[0]
    assert r["status"]=="BREAK"
    assert set(r["break_types"])=={"Quantity mismatch","Market value mismatch"}
    assert str(r["quantity_difference"])=="1"

def test_position_matched():
    row={"account":"A","security":"IBM","currency":"USD","quantity":10,"market_value":100}
    assert reconcile_positions([row],[row])[0]["status"]=="MATCHED"

def test_upload_validation():
    assert validate_rows([{"account":"A","security":"IBM","quantity":1,"currency":"USD"}],"POSITION")==[]
    assert validate_rows([{"account":"A"}],"TRANSACTION")
