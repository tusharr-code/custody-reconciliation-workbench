# Custody Reconciliation Workbench

**Automating Transaction Reconciliation, Position Reconciliation and Break Management**

A full-stack financial operations application designed to streamline custody reconciliation between custodian records and internal accounting books.

Built to demonstrate how financial domain knowledge and modern technology can help improve reconciliation workflows, exception investigation and operational efficiency.

**Developed by:** [Tushar Ramugade](https://github.com/tusharr-code)

**GitHub Repository:** https://github.com/tusharr-code/custody-reconciliation-workbench

---

## Project Overview

In investment operations, reconciliation teams regularly compare custodian statements against internal accounting records to identify discrepancies, investigate exceptions and resolve outstanding breaks.

Traditional reconciliation processes can involve significant manual effort, fragmented workflows and limited visibility into unresolved exceptions.

The Custody Reconciliation Workbench explores a technology-driven approach to these challenges through automated matching, break identification and centralised exception management.

## Key Features

### 1. Transaction Reconciliation
- Compare custodian and internal transaction records.
- Identify matched and unmatched transactions.
- Highlight missing records and duplicate transactions.
- Identify quantity, amount and date discrepancies.
- Apply configurable matching rules and tolerances.

### 2. Position Reconciliation
- Compare security-level holdings between custodian and internal books.
- Identify quantity differences.
- Highlight market value discrepancies.
- Identify securities missing from either source.

### 3. Break Management
- Centralised exception management.
- Track open and resolved breaks.
- Record investigation comments and root causes.
- Assign ownership and monitor resolution status.

### 4. Data Ingestion and Processing
- Upload reconciliation input files in CSV format.
- Validate incoming records.
- Process data using Python and Pandas.
- Identify data-quality issues.

### 5. Reporting and Export
- Review reconciliation results.
- Analyse identified exceptions.
- Export reconciliation outputs for operational review.

---

## Application Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.jpg)

### Transaction Reconciliation
![Transaction Reconciliation](screenshots/transaction-reconciliation.jpg)

### Position Reconciliation
![Position Reconciliation](screenshots/position-reconciliation.jpg)

### Break Management
![Break Management](screenshots/break-management.jpg)

*Replace screenshot filenames above with the exact names of your uploaded image files if they differ.*

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| Data Processing | Pandas |
| API | REST API |
| Deployment Setup | Docker, Docker Compose |
| Input Data | CSV |

---

## Project Architecture

```text
Custody Reconciliation Workbench
│
├── frontend/
│   ├── React Application
│   └── User Interface
│
├── backend/
│   ├── FastAPI Application
│   ├── Reconciliation Engine
│   ├── Data Processing
│   └── API Endpoints
│
├── database/
│   └── PostgreSQL Schema
│
├── screenshots/
│   └── Application Screenshots
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11 or compatible version
- Node.js and npm
- PostgreSQL
- Docker Desktop (recommended for containerised setup)

### Run Using Docker

1. Clone the repository:

```bash
git clone https://github.com/tusharr-code/custody-reconciliation-workbench.git
```

2. Navigate to the project directory:

```bash
cd custody-reconciliation-workbench
```

3. Configure environment variables using `.env.example`.

4. Start the application:

```bash
docker compose up --build
```

5. Access the application using the frontend and backend URLs configured in the project.

Refer to the project configuration and backend/frontend README instructions for environment-specific setup.

---

## Business Use Cases

This project explores reconciliation workflows relevant to:

- Custodian versus internal accounting reconciliation.
- Fund accounting operations.
- Investment operations.
- Cash and position reconciliation.
- Financial data quality monitoring.
- Break investigation and exception management.

---

## Future Enhancements

The following capabilities are potential future development areas:

- Advanced one-to-many and many-to-one transaction matching.
- Corporate action reconciliation.
- User authentication and role-based access control.
- Maker-checker approval workflow.
- Detailed audit trail and activity history.
- Advanced reconciliation dashboards and analytics.
- Scheduled reconciliation and automated notifications.
- Integration with external custodian data feeds.

---

## About the Developer

I have 7.5+ years of experience in financial markets and investment operations, with practical exposure to reconciliation processes and exception investigation.

This project reflects my interest in combining financial domain expertise with software development, data analytics and automation to solve practical challenges in financial operations.

**Areas of Interest:**
- Custody and Fund Accounting
- Investment Operations
- Financial Data Analytics
- Reconciliation Automation
- FinTech and Product Data Engineering

**Connect with me:**

- GitHub: https://github.com/tusharr-code
- LinkedIn: https://www.linkedin.com/in/tushar-ramugade-3abbb915b

---

## Disclaimer

This is a portfolio and learning project intended to demonstrate reconciliation concepts and application development.

It is not a production-ready financial reconciliation system. Production deployment would require additional security controls, authentication, auditability, operational resilience, data governance and comprehensive integration testing.

---

**If you find this project interesting, feel free to explore the repository, share feedback or connect for collaboration.**
