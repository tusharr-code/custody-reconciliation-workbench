"""Deterministic, configurable custody reconciliation engine."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Any
import pandas as pd


def _s(v: Any) -> str:
    return "" if pd.isna(v) else str(v).strip()

def _n(v: Any) -> Decimal | None:
    if v is None or pd.isna(v) or str(v).strip() == "": return None
    try: return Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError): return None

def _date(v: Any) -> str:
    if v is None or pd.isna(v) or str(v).strip() == "": return ""
    try: return pd.to_datetime(v, errors="raise").date().isoformat()
    except Exception: return _s(v)

def _get(row: dict, *names: str) -> Any:
    normalized = {''.join(ch for ch in str(k).lower() if ch.isalnum()): v for k, v in row.items()}
    for name in names:
        key = ''.join(ch for ch in name.lower() if ch.isalnum())
        if key in normalized: return normalized[key]
    return None

def normalize_transaction(row: dict) -> dict:
    return {
        "account": _s(_get(row, "account", "account_id")).upper(),
        "transaction_id": _s(_get(row, "transaction_id", "trade_id", "transactionid")).upper(),
        "security": _s(_get(row, "security", "security_name", "ticker")).upper(),
        "transaction_type": _s(_get(row, "transaction_type", "type")).upper(),
        "trade_date": _date(_get(row, "trade_date")),
        "settlement_date": _date(_get(row, "settlement_date", "settle_date")),
        "quantity": _n(_get(row, "quantity", "qty")),
        "price": _n(_get(row, "price", "trade_price")),
        "net_amount": _n(_get(row, "net_amount", "netamount", "amount")),
        "currency": _s(_get(row, "currency", "ccy")).upper(),
        "raw": {k: _s(v) for k, v in row.items()},
    }

def normalize_position(row: dict) -> dict:
    return {
        "account": _s(_get(row, "account", "account_id")).upper(),
        "security": _s(_get(row, "security", "security_name", "ticker", "cusip", "isin")).upper(),
        "currency": _s(_get(row, "currency", "ccy")).upper(),
        "quantity": _n(_get(row, "quantity", "qty")),
        "market_value": _n(_get(row, "market_value", "marketvalue", "value")),
        "price": _n(_get(row, "price", "last_price")),
        "raw": {k: _s(v) for k, v in row.items()},
    }

def _diff(a: Decimal | None, b: Decimal | None, tolerance: Decimal) -> bool:
    if a is None or b is None: return a != b
    return abs(a - b) > tolerance

def reconcile_transactions(custodian: list[dict], internal: list[dict], config: dict | None = None) -> list[dict]:
    """Match transaction IDs; report missing-side and field-level exceptions."""
    cfg = config or {}
    keys = cfg.get("transaction_keys", ["account", "transaction_id"])
    qty_tol = Decimal(str(cfg.get("quantity_tolerance", "0.000001")))
    amt_tol = Decimal(str(cfg.get("amount_tolerance", "0.01")))
    price_tol = Decimal(str(cfg.get("price_tolerance", "0.0001")))
    date_tol = int(cfg.get("date_tolerance_days", 0))
    crows = [normalize_transaction(x) for x in custodian]
    irows = [normalize_transaction(x) for x in internal]
    def key(r): return tuple(r.get(k, "") for k in keys)
    imap: dict[tuple, list] = {}
    for r in irows: imap.setdefault(key(r), []).append(r)
    results, used = [], set()
    for c in crows:
        k = key(c); candidates = imap.get(k, [])
        i = next((x for x in candidates if id(x) not in used), None)
        if i: used.add(id(i))
        issues = []
        if not i: issues.append("Missing internal")
        else:
            for field, tol, label in [("quantity", qty_tol, "Quantity mismatch"), ("net_amount", amt_tol, "Amount mismatch"), ("price", price_tol, "Price mismatch")]:
                if c[field] is not None or i[field] is not None:
                    if _diff(c[field], i[field], tol): issues.append(label)
            if c["currency"] != i["currency"]: issues.append("Currency mismatch")
            for field, label in [("trade_date", "Trade date mismatch"), ("settlement_date", "Settlement date mismatch")]:
                if c[field] and i[field] and c[field] != i[field]:
                    if date_tol == 0 or abs((pd.Timestamp(c[field])-pd.Timestamp(i[field])).days) > date_tol: issues.append(label)
        results.append({"record_type":"TRANSACTION", "match_key":"|".join(k), "account":c["account"], "security":c["security"], "transaction_id":c["transaction_id"], "custodian":c, "internal":i, "status":"MATCHED" if not issues else "BREAK", "break_types":issues})
    for i in irows:
        if id(i) not in used:
            results.append({"record_type":"TRANSACTION", "match_key":"|".join(key(i)), "account":i["account"], "security":i["security"], "transaction_id":i["transaction_id"], "custodian":None, "internal":i, "status":"BREAK", "break_types":["Missing custodian"]})
    return results

def reconcile_positions(custodian: list[dict], internal: list[dict], config: dict | None = None) -> list[dict]:
    cfg = config or {}
    keys = cfg.get("position_keys", ["account", "security", "currency"])
    qty_tol = Decimal(str(cfg.get("quantity_tolerance", "0.000001")))
    mv_tol = Decimal(str(cfg.get("market_value_tolerance", "0.01")))
    crows = [normalize_position(x) for x in custodian]
    irows = [normalize_position(x) for x in internal]
    def key(r): return tuple(r.get(k, "") for k in keys)
    imap: dict[tuple, list] = {}
    for r in irows: imap.setdefault(key(r), []).append(r)
    results, used = [], set()
    for c in crows:
        k=key(c); candidates=imap.get(k,[]); i=next((x for x in candidates if id(x) not in used),None)
        if i: used.add(id(i))
        issues=[]
        if not i: issues.append("Missing internal")
        else:
            if _diff(c["quantity"],i["quantity"],qty_tol): issues.append("Quantity mismatch")
            if _diff(c["market_value"],i["market_value"],mv_tol): issues.append("Market value mismatch")
        results.append({"record_type":"POSITION","match_key":"|".join(k),"account":c["account"],"security":c["security"],"currency":c["currency"],"custodian":c,"internal":i,"quantity_difference":(c["quantity"]-i["quantity"]) if i and c["quantity"] is not None and i["quantity"] is not None else None,"market_value_difference":(c["market_value"]-i["market_value"]) if i and c["market_value"] is not None and i["market_value"] is not None else None,"status":"MATCHED" if not issues else "BREAK","break_types":issues})
    for i in irows:
        if id(i) not in used:
            results.append({"record_type":"POSITION","match_key":"|".join(key(i)),"account":i["account"],"security":i["security"],"currency":i["currency"],"custodian":None,"internal":i,"quantity_difference":None,"market_value_difference":None,"status":"BREAK","break_types":["Missing custodian"]})
    return results

def validate_rows(rows: list[dict], record_type: str) -> list[str]:
    errors=[]
    if not rows: return ["The uploaded file contains no data rows."]
    required = ["account", "security", "quantity", "currency"]
    if record_type == "TRANSACTION": required += ["transaction_id"]
    for idx,row in enumerate(rows, start=2):
        n={''.join(ch for ch in str(k).lower() if ch.isalnum()):v for k,v in row.items()}
        aliases={"account":"account_id","security":"security_name","quantity":"qty","currency":"ccy","transaction_id":"trade_id"}
        for field in required:
            names=[field,aliases.get(field,"_")]
            if not any(_s(n.get(''.join(ch for ch in x if ch.isalnum()))) for x in names): errors.append(f"Row {idx}: missing {field}.")
    return errors
