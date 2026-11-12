from sqlalchemy import String, Date, DateTime, Numeric, Boolean, ForeignKey, JSON, Text, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str]=mapped_column(String(160))
    role: Mapped[str]=mapped_column(String(40), default="ANALYST")
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())

class Account(Base):
    __tablename__="accounts"
    id: Mapped[int]=mapped_column(primary_key=True)
    account_code: Mapped[str]=mapped_column(String(80), unique=True, index=True)
    account_name: Mapped[str|None]=mapped_column(String(200))
    base_currency: Mapped[str]=mapped_column(String(3), default="USD")
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)

class Security(Base):
    __tablename__="securities"
    id: Mapped[int]=mapped_column(primary_key=True)
    security_code: Mapped[str]=mapped_column(String(80), unique=True, index=True)
    description: Mapped[str|None]=mapped_column(String(250))
    isin: Mapped[str|None]=mapped_column(String(12), index=True)
    cusip: Mapped[str|None]=mapped_column(String(9), index=True)
    asset_type: Mapped[str|None]=mapped_column(String(50))

class SourceFile(Base):
    __tablename__="source_files"
    id: Mapped[int]=mapped_column(primary_key=True)
    filename: Mapped[str]=mapped_column(String(255))
    source_side: Mapped[str]=mapped_column(String(20))
    record_type: Mapped[str]=mapped_column(String(20))
    sha256: Mapped[str]=mapped_column(String(64), index=True)
    row_count: Mapped[int]=mapped_column(Integer)
    uploaded_at: Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    uploaded_by: Mapped[int|None]=mapped_column(ForeignKey("users.id"))

class ReconciliationRun(Base):
    __tablename__="reconciliation_runs"
    id: Mapped[int]=mapped_column(primary_key=True)
    record_type: Mapped[str]=mapped_column(String(20))
    business_date: Mapped[Date]=mapped_column(Date)
    status: Mapped[str]=mapped_column(String(20), default="COMPLETED")
    config: Mapped[dict]=mapped_column(JSON)
    total_count: Mapped[int]=mapped_column(Integer, default=0)
    matched_count: Mapped[int]=mapped_column(Integer, default=0)
    break_count: Mapped[int]=mapped_column(Integer, default=0)
    created_at: Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())

class TransactionRecord(Base):
    __tablename__="transaction_records"
    id: Mapped[int]=mapped_column(primary_key=True)
    source_file_id: Mapped[int]=mapped_column(ForeignKey("source_files.id"))
    side: Mapped[str]=mapped_column(String(20))
    account_code: Mapped[str]=mapped_column(String(80), index=True)
    transaction_id: Mapped[str]=mapped_column(String(120), index=True)
    security_code: Mapped[str]=mapped_column(String(80), index=True)
    transaction_type: Mapped[str|None]=mapped_column(String(30))
    trade_date: Mapped[Date|None]=mapped_column(Date)
    settlement_date: Mapped[Date|None]=mapped_column(Date)
    quantity: Mapped[Numeric|None]=mapped_column(Numeric(24,8))
    price: Mapped[Numeric|None]=mapped_column(Numeric(24,8))
    net_amount: Mapped[Numeric|None]=mapped_column(Numeric(24,8))
    currency: Mapped[str]=mapped_column(String(3))
    raw_data: Mapped[dict]=mapped_column(JSON)

class PositionSnapshot(Base):
    __tablename__="position_snapshots"
    id: Mapped[int]=mapped_column(primary_key=True)
    source_file_id: Mapped[int]=mapped_column(ForeignKey("source_files.id"))
    side: Mapped[str]=mapped_column(String(20))
    business_date: Mapped[Date]=mapped_column(Date)
    account_code: Mapped[str]=mapped_column(String(80), index=True)
    security_code: Mapped[str]=mapped_column(String(80), index=True)
    currency: Mapped[str]=mapped_column(String(3))
    quantity: Mapped[Numeric|None]=mapped_column(Numeric(24,8))
    price: Mapped[Numeric|None]=mapped_column(Numeric(24,8))
    market_value: Mapped[Numeric|None]=mapped_column(Numeric(24,8))
    raw_data: Mapped[dict]=mapped_column(JSON)


class ReconciliationResult(Base):
    __tablename__="reconciliation_results"
    id: Mapped[int]=mapped_column(primary_key=True)
    run_id: Mapped[int]=mapped_column(ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), index=True)
    record_type: Mapped[str]=mapped_column(String(20))
    match_key: Mapped[str]=mapped_column(String(500), index=True)
    account_code: Mapped[str|None]=mapped_column(String(80), index=True)
    security_code: Mapped[str|None]=mapped_column(String(80), index=True)
    status: Mapped[str]=mapped_column(String(20), index=True)
    break_types: Mapped[list]=mapped_column(JSON)
    result_data: Mapped[dict]=mapped_column(JSON)

class Break(Base):
    __tablename__="reconciliation_breaks"
    id: Mapped[int]=mapped_column(primary_key=True)
    run_id: Mapped[int]=mapped_column(ForeignKey("reconciliation_runs.id"), index=True)
    record_type: Mapped[str]=mapped_column(String(20))
    match_key: Mapped[str]=mapped_column(String(500), index=True)
    account_code: Mapped[str|None]=mapped_column(String(80), index=True)
    security_code: Mapped[str|None]=mapped_column(String(80), index=True)
    break_types: Mapped[list]=mapped_column(JSON)
    difference_data: Mapped[dict]=mapped_column(JSON)
    root_cause: Mapped[str]=mapped_column(String(100), default="Pending investigation")
    owner: Mapped[str|None]=mapped_column(String(160))
    status: Mapped[str]=mapped_column(String(30), default="OPEN", index=True)
    comment: Mapped[str|None]=mapped_column(Text)
    created_at: Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BreakComment(Base):
    __tablename__="break_comments"
    id: Mapped[int]=mapped_column(primary_key=True)
    break_id: Mapped[int]=mapped_column(ForeignKey("reconciliation_breaks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"))
    comment: Mapped[str]=mapped_column(Text)
    created_at: Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())

class AuditEvent(Base):
    __tablename__="audit_events"
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"))
    entity_type: Mapped[str]=mapped_column(String(60))
    entity_id: Mapped[str]=mapped_column(String(80))
    action: Mapped[str]=mapped_column(String(60))
    before_data: Mapped[dict|None]=mapped_column(JSON)
    after_data: Mapped[dict|None]=mapped_column(JSON)
    created_at: Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())
