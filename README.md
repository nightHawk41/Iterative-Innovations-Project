# Iterative Innovations - Vending Inventory System
**Course:** CMSC 447 | **Section:** 06 | **Semester:** Spring 2026

## Team 6 Members
* **Sean Laverty** - GitHub: `nightHawk41`, `StockSlayer`
* **Habib Aina** - GitHub: `MajorH5`
* **Iyioluwakanmi Kumolalo** - GitHub: `hiya-hey`

---

## Project Overview
The **Iterative Innovations Project** aims to modernize legacy vending infrastructure at the University Library. We are designing a software-based inventory tracking system that bridges the gap between older-model hardware and modern operational needs.

By integrating campus card transaction data (CBORD), the system infers real-time inventory levels, sales trends, and restocking needs without requiring expensive hardware replacements.

### The Problem
Current 15-year-old vending machines process payments but lack item-level data exports. This results in:
* **Manual Inspections:** Staff must physically visit machines to check stock.
* **Operational Inefficiency:** High labor costs and "blind" restocking runs.
* **Customer Friction:** Frequent "sold-out" items and expired products.

### Our Solution
A full-stack web dashboard that:
1. **Maps Transactions to Items:** Uses unique price-point mapping to identify items from redacted CBORD export logs.
2. **Monitors Stock Levels:** Inferred depletion tracking based on real-time sales data.
3. **Inventory Management:** A dedicated interface for student workers to log restocking events and expiration dates.

---

## Technology Stack
* **Frontend:** React (JavaScript) with Bootstrap UI
* **Backend:** Flask (Python) 
* **Database/Data:** Redacted CBORD Transactional Data (CSV/JSON)
* **Project Management:** JIRA
* **Version Control:** GitHub (WSL/Linux Environment)
* **Communication:** MS Teams

---

## Getting Started
To set up the development environment on your local machine, please follow the detailed instructions here:
**[Getting Started Guide](docs/Getting_Started.txt)**

---

## Reference Materials
* **[Branching Overview](docs/Branching_Overview.txt):** Standards for feature branches and stable releases.
* **[Git Workflow Guide](docs/Git_Workflow_Guide.txt):** Protocol for Pull Requests and Code Reviews.