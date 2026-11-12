from datetime import date
from decimal import Decimal
import hashlib, io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import get_db, init_db
from .models import SourceFile, ReconciliationRun, Break, BreakComment, AuditEvent, TransactionRecord, PositionSnapshot, ReconciliationResult
from .reconciliation import reconcile_transactions, reconcile_positions, validate_rows, normalize_transaction, normalize_position

app=FastAPI(title="Custody Reconciliation API",version="2.0.0",description="Custodian versus internal books reconciliation API")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup(): init_db()

@app.get("/health")
def health(): return {"status":"ok","version":"2.0.0"}

@app.post("/api/reconcile")
async def reconcile(custodian_file: UploadFile=File(...), internal_file: UploadFile=File(...), record_type: str=Form(...), business_date: date=Form(...), config_json: str=Form("{}"), db: Session=Depends(get_db)):
    rt=record_type.upper()
    if rt not in {"TRANSACTION","POSITION"}: raise HTTPException(400,"record_type must be TRANSACTION or POSITION")
    try: config=__import__('json').loads(config_json)
    except Exception: raise HTTPException(400,"config_json must be valid JSON")
    cbytes,ibytes=await custodian_file.read(),await internal_file.read()
    try:
        cdf=pd.read_csv(io.BytesIO(cbytes),dtype=str,keep_default_na=False); idf=pd.read_csv(io.BytesIO(ibytes),dtype=str,keep_default_na=False)
    except Exception as e: raise HTTPException(400,f"CSV parsing failed: {e}")
    crows, irows=cdf.to_dict("records"),idf.to_dict("records")
    for side,rows in [("custodian",crows),("internal",irows)]:
        errors=validate_rows(rows,rt)
        if errors: raise HTTPException(422,{"side":side,"validation_errors":errors[:100]})
    fn=[]
    for name,side,content,rows in [(custodian_file.filename,"CUSTODIAN",cbytes,crows),(internal_file.filename,"INTERNAL",ibytes,irows)]:
        sf=SourceFile(filename=name or "upload.csv",source_side=side,record_type=rt,sha256=hashlib.sha256(content).hexdigest(),row_count=len(rows));db.add(sf);db.flush();fn.append(sf)
    # Persist normalized source records/snapshots so imported data survives browser sessions.
    if rt == "TRANSACTION":
        for side, rows, sf in [("CUSTODIAN", crows, fn[0]), ("INTERNAL", irows, fn[1])]:
            for raw in rows:
                n = normalize_transaction(raw)
                db.add(TransactionRecord(source_file_id=sf.id, side=side, account_code=n["account"], transaction_id=n["transaction_id"], security_code=n["security"], transaction_type=n["transaction_type"] or None, trade_date=pd.to_datetime(n["trade_date"]).date() if n["trade_date"] else None, settlement_date=pd.to_datetime(n["settlement_date"]).date() if n["settlement_date"] else None, quantity=n["quantity"], price=n["price"], net_amount=n["net_amount"], currency=n["currency"], raw_data=n["raw"]))
        results=reconcile_transactions(crows,irows,config)
    else:
        for side, rows, sf in [("CUSTODIAN", crows, fn[0]), ("INTERNAL", irows, fn[1])]:
            for raw in rows:
                n = normalize_position(raw)
                db.add(PositionSnapshot(source_file_id=sf.id, side=side, business_date=business_date, account_code=n["account"], security_code=n["security"], currency=n["currency"], quantity=n["quantity"], price=n["price"], market_value=n["market_value"], raw_data=n["raw"]))
        results=reconcile_positions(crows,irows,config)
    run=ReconciliationRun(record_type=rt,business_date=business_date,config=config,total_count=len(results),matched_count=sum(x['status']=='MATCHED' for x in results),break_count=sum(x['status']=='BREAK' for x in results));db.add(run);db.flush()
    for r in results:
        db.add(ReconciliationResult(run_id=run.id, record_type=rt, match_key=r['match_key'], account_code=r.get('account'), security_code=r.get('security'), status=r['status'], break_types=r['break_types'], result_data=_json_safe(r)))
        if r['status']=='BREAK':
            db.add(Break(run_id=run.id,record_type=rt,match_key=r['match_key'],account_code=r.get('account'),security_code=r.get('security'),break_types=r['break_types'],difference_data={"custodian":_json_safe(r.get('custodian')),"internal":_json_safe(r.get('internal')),"quantity_difference":str(r.get('quantity_difference')) if r.get('quantity_difference') is not None else None,"market_value_difference":str(r.get('market_value_difference')) if r.get('market_value_difference') is not None else None},root_cause="Pending investigation",status="OPEN"))
    db.add(AuditEvent(entity_type="RECONCILIATION_RUN",entity_id=str(run.id),action="CREATED",after_data={"record_type":rt,"business_date":business_date.isoformat(),"count":len(results)}));db.commit()
    return {"run_id":run.id,"record_type":rt,"business_date":business_date.isoformat(),"total_count":run.total_count,"matched_count":run.matched_count,"break_count":run.break_count,"results":_json_safe(results)}

def _json_safe(v):
    if isinstance(v,dict): return {k:_json_safe(x) for k,x in v.items() if k!="raw"}
    if isinstance(v,list): return [_json_safe(x) for x in v]
    if isinstance(v,Decimal): return str(v)
    if hasattr(v,"isoformat"): return v.isoformat()
    return v

@app.get("/api/runs")
def list_runs(db:Session=Depends(get_db)):
    rows=db.scalars(select(ReconciliationRun).order_by(ReconciliationRun.id.desc()).limit(100)).all()
    return [{"id":x.id,"record_type":x.record_type,"business_date":x.business_date.isoformat(),"total_count":x.total_count,"matched_count":x.matched_count,"break_count":x.break_count,"created_at":x.created_at.isoformat() if x.created_at else None} for x in rows]

@app.get("/api/runs/{run_id}/results")
def run_results(run_id:int, db:Session=Depends(get_db)):
    rows=db.scalars(select(ReconciliationResult).where(ReconciliationResult.run_id==run_id).order_by(ReconciliationResult.id)).all()
    return [{"id":x.id,"record_type":x.record_type,"match_key":x.match_key,"account":x.account_code,"security":x.security_code,"status":x.status,"break_types":x.break_types,**x.result_data} for x in rows]

@app.get("/api/positions/history")
def position_history(account: str|None=None, security: str|None=None, db:Session=Depends(get_db)):
    from .models import PositionSnapshot
    q=select(PositionSnapshot).order_by(PositionSnapshot.business_date.desc(),PositionSnapshot.id.desc())
    if account: q=q.where(PositionSnapshot.account_code.ilike(f"%{account}%"))
    if security: q=q.where(PositionSnapshot.security_code.ilike(f"%{security}%"))
    rows=db.scalars(q.limit(1000)).all()
    return [{"business_date":x.business_date.isoformat(),"side":x.side,"account":x.account_code,"security":x.security_code,"currency":x.currency,"quantity":str(x.quantity) if x.quantity is not None else None,"price":str(x.price) if x.price is not None else None,"market_value":str(x.market_value) if x.market_value is not None else None} for x in rows]

@app.get("/api/breaks")
def list_breaks(status: str|None=None, record_type: str|None=None, db:Session=Depends(get_db)):
    q=select(Break).order_by(Break.id.desc())
    if status: q=q.where(Break.status==status.upper())
    if record_type: q=q.where(Break.record_type==record_type.upper())
    return [{"id":b.id,"run_id":b.run_id,"record_type":b.record_type,"match_key":b.match_key,"account_code":b.account_code,"security_code":b.security_code,"break_types":b.break_types,"difference_data":b.difference_data,"root_cause":b.root_cause,"owner":b.owner,"status":b.status,"comment":b.comment} for b in db.scalars(q.limit(1000)).all()]

@app.patch("/api/breaks/{break_id}")
def update_break(break_id:int,payload:dict,db:Session=Depends(get_db)):
    b=db.get(Break,break_id)
    if not b: raise HTTPException(404,"Break not found")
    allowed={"root_cause","owner","status","comment"}; invalid=set(payload)-allowed
    if invalid: raise HTTPException(400,f"Unsupported fields: {sorted(invalid)}")
    before={k:getattr(b,k) for k in allowed}
    for k,v in payload.items(): setattr(b,k,v)
    if "comment" in payload and payload["comment"]: db.add(BreakComment(break_id=b.id,comment=payload["comment"]))
    db.add(AuditEvent(entity_type="BREAK",entity_id=str(b.id),action="UPDATED",before_data=before,after_data=payload));db.commit();db.refresh(b)
    return {"id":b.id,"status":b.status,"root_cause":b.root_cause,"owner":b.owner,"comment":b.comment}

@app.get("/api/reports/breaks.csv")
def export_breaks(db:Session=Depends(get_db)):
    rows=db.scalars(select(Break).order_by(Break.id)).all()
    data=[{"break_id":b.id,"run_id":b.run_id,"type":b.record_type,"account":b.account_code,"security":b.security_code,"break_types":"; ".join(b.break_types),"root_cause":b.root_cause,"owner":b.owner,"status":b.status,"comment":b.comment or ""} for b in rows]
    df=pd.DataFrame(data); buf=io.StringIO();df.to_csv(buf,index=False);buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=breaks_report.csv"})
