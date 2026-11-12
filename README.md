
# Custody Reconciliation Workbench v2

A database-backed development implementation extending the supplied browser MVP.

## Architecture

- **Frontend:** React + Vite (`frontend/`), blue operational header, reconciliation upload controls, transaction/position grids, Open Breaks, Position History entry point, run list and break investigation form.
- **API:** FastAPI (`backend/app/main.py`), CSV ingestion/validation, reconciliation endpoints, break lifecycle endpoints, report export and OpenAPI docs.
- **Database:** PostgreSQL 16 with SQLAlchemy models (`backend/app/models.py`).
- **Processing:** Pandas for CSV ingestion; Decimal-based matching logic (`backend/app/reconciliation.py`).

## Start locally (Docker recommended)

Prerequisite: Docker Desktop / Docker Engine with Compose.

```bash
docker compose up --build
```

Then open:
- Frontend: http://localhost:5173
- API health: http://localhost:8000/health
- Interactive API docs: http://localhost:8000/docs

To stop: `docker compose down`. To reset the development database: `docker compose down -v` (deletes all local data).

Development database credentials are intentionally simple and MUST be changed before any shared or production deployment.

## Reconciliation workflow

1. Select Transaction or Position.
2. Select the business date.
3. Upload custodian and internal CSV files with compatible columns.
4. Click **Load & Reconcile**.
5. Review matched and break records in the grid; open **Open Breaks** to assign root cause, owner, status and comments.
6. Export break records as CSV.

### Supported transaction columns
`account` (or `account_id`), `transaction_id` (or `trade_id`), `security` (or `security_name`/`ticker`), `transaction_type`, `trade_date`, `settlement_date`, `quantity` (or `qty`), `price`, `net_amount` (or `amount`), `currency`.

Matching defaults: account + transaction ID; quantity tolerance 0.000001; amount tolerance 0.01; price tolerance 0.0001; exact currency and trade/settlement dates. Config JSON can override transaction keys and tolerances.

### Supported position columns
`account`, `security` (or `security_name`/`ticker`), `currency`, `quantity` (or `qty`), `market_value` (or `value`), `price`.

Matching defaults: account + security + currency; quantity tolerance 0.000001; market value tolerance 0.01.

## Database entities

| Table | Purpose |
|---|---|
| `users` | User identities and role placeholder |
| `accounts` | Account reference data |
| `securities` | Security master reference data, including ISIN/CUSIP |
| `source_files` | Uploaded file metadata, hash, side and row count |
| `transaction_records` | Custodian/internal transaction source records |
| `position_snapshots` | Dated custodian/internal holdings snapshots |
| `reconciliation_runs` | Run date, type, config and control totals |
| `reconciliation_results` | Persistent matched/break result detail for each run |
| `reconciliation_breaks` | Persistent exception, root cause, owner and status |
| `break_comments` | Comment history |
| `audit_events` | Entity change event trail |

See `database/schema.sql` for the PostgreSQL DDL reference. SQLAlchemy creates the current model tables at API startup for this development build.

## Sample data

- `sample_data/custodian_sample.csv`
- `sample_data/internal_sample.csv`
- `sample_data/custodian_transactions.csv` and `sample_data/internal_transactions.csv`
- `sample_data/custodian_positions.csv` and `sample_data/internal_positions.csv`

The sample files contain transaction and position rows. For a transaction run, retain the `TRANSACTION` rows; for a position run, retain the `POSITION` rows. You can split them into separate files in a spreadsheet or text editor.

<img width="1280" height="720" alt="YG67WIh5OxtNu3kUNeusOXZnBZWNgLBlE4j2kV5WeciwZhDXJWMd-7jwNoR04IvmfFFGU4oNGC464Wb4BzH3E9qkefBwxXVqjVgx2fgzv4SfCLq9H7fawz6dNGszZrEFUqiF3Fo5hnOkfTUajKHBXE8Lx97y0ojePd0E00P6mfY_-G0sIo0jj0PZYBOQEFcC" src="https://github.com/user-attachments/assets/de5ebce8-167a-4534-8868-6aecdd4af36e" />
<img width="3600" height="2160" alt="PpNQT9GUi-S_l6iHhGIZoiQ_ewqw28ZKRhZv_qD2yNnEIYk9nP-cG53Vi5ulUXsBvelMkb8PG4OB5sj8xQFJqHycdXxfAVLTexbq6YNmy4h6Y9RzbzHLQYcNBaKoTZS7FrucvHaAJBcfVmEVwRmB01ai3eWOvgYDKOly1nkS9Dui5KpHwzICMP_oA4mKVDZj" src="https://github.com/user-attachments/assets/5662fccc-1668-44d6-9149-4e436237e523" />
<img width="3600" height="2160" alt="PpNQT9GUi-S_l6iHhGIZoiQ_ewqw28ZKRhZv_qD2yNnEIYk9nP-cG53Vi5ulUXsBvelMkb8PG4OB5sj8xQFJqHycdXxfAVLTexbq6YNmy4h6Y9RzbzHLQYcNBaKoTZS7FrucvHaAJBcfVmEVwRmB01ai3eWOvgYDKOly1nkS9Dui5KpHwzICMP_oA4mKVDZj (1)" src="https://github.com/user-attachments/assets/b35c2c3d-71ce-49d1-a530-97f22cee221e" />
<img width="2650" height="1254" alt="0ebyGdz5vzYiXoTI3NI7loDZGW6sC8AJWNjXznH7_rJ-7ZHPEDwezJ6tvejxsyH1Z1g8SLvwhQW1cNGQLa77X_wPm1N2pCBR0k3aRbGitIRHpMUZv_Jk1k_ra7eKIKK6hloh5vp7Eww-MD1db1h1h1LdXpt4NU1MKPGLFrbBdkyE-VdYzzckVKfishQX0_OC" src="https://github.com/user-attachments/assets/96bf7701-0196-4591-a2e5-a724bfff8169" />

## Tests

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

The unit tests cover matched records, missing-side records, quantity/amount/currency/date breaks and position market-value differences.

## Current limitations / production controls still required

This is a development foundation, not a production-ready financial control system. Before production:

- Add SSO/OIDC, MFA, role-based authorization and least-privilege database roles.
- Replace demo DB credentials; use secrets management, TLS, encryption at rest and key rotation.
- Implement immutable, tamper-evident audit events with actor identity and before/after values for every material change.
- Add maker-checker approval, segregation of duties and controlled break closure.
- Add idempotency and duplicate-file detection enforcement, ingestion job retries, file quarantine and schema/version management.
- Add account/security mapping tables and controlled reference-data maintenance; support ISIN/CUSIP/SEDOL/ticker crosswalks.
- Review matching keys and tolerance policy with operations, including partial fills, reversals, cancellations, FX, fees, corporate actions, pending trades and settlement conventions.
- Add robust duplicate-key handling and one-to-many/many-to-one matching strategies.
- Persist complete reconciliation output detail for matched records, not only the imported source records and breaks.
- Add pagination, retention policies, backups, monitoring, alerting, performance/load tests and disaster recovery.
- Add comprehensive API authorization, upload size limits, malware scanning and security testing.

The current API persists source records, dated position snapshots, run control totals, complete per-run match results, break records, comments and audit event entries. Position history is exposed through `/api/positions/history`; run details are exposed through `/api/runs/{run_id}/results`. User authentication is not implemented; audit actor IDs are currently nullable. Position History tab currently provides the navigation surface and run list; detailed historical snapshot search UI is a follow-up.
