# UMBC Vending Inventory System (Iterative Innovations - Team 6)
**Course:** CMSC 447 - Software Engineering | **Section:** 06 | **Semester:** Spring 2026

## Team 6 Members
* **Sean Laverty** - GitHub: `nightHawk41`, `StockSlayer`
* **Habib Aina** - GitHub: `MajorH5`
* **Iyioluwakanmi Kumolalo** - GitHub: `hiya-hey`

### Project Overview
The Iterative Innovations Project offers a modern, software-driven inventory-tracking system for the legacy vending machine at the UMBC Library. Leveraging “Unique Price Mapping” logic, our system connects 15-year-old hardware with modern operational needs, transforming raw, item-blind transaction logs from the Campus Card (CBORD) system into real-time, actionable inventory data.

### The Problem
The current vending machine, originally designed for DVDs, lacks the capability to report slot IDs or product names and transmits only transaction amounts. This leads to several issues:
- No automated method to identify which items have been sold or restocked.
- Student workers must rely on handwritten logs and manual inspections to track inventory, which is time-consuming and error-prone.
- Inconsistent stocking of essential health supplies.

### Our Solution
A comprehensive web dashboard that:
- Matches unique price points to specific inventory slots, automating stock deduction.
- Provides an intuitive interface for staff to log restocks and expiration dates.
- Offers a color-coded "health pulse" indicating stock levels and product expiration status.

### Technology Stack
* **Frontend:** React (JavaScript)
* **Backend:** Flask (Python) 
* **Database/Data:** SQLite 
* **Integration:** RESTful API & CSV Mocking Service
* **Dev Environment:** Linux/WSL/Windows
* **Project Management:** JIRA & MS Teams

### Getting Started
To set up the development environment on your local machine, please follow the detailed instructions here:
**[Getting Started Guide](docs/Getting_Started.txt)**

### Reference Materials
* **[Branching Overview](docs/Branching_Overview.txt):** Standards for feature branches and stable releases.
* **[Git Workflow Guide](docs/Git_Workflow_Guide.txt):** Protocol for Pull Requests and Code Reviews.