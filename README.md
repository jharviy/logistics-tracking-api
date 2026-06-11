# 📦 LogiTrack API (Logistics Tracking & Management)

A secure, enterprise-ready RESTful API built to streamline logistics data logging, package transit milestones, and user access control. 

[![Live Demo](https://img.shields.io/badge/Demo-Live%20API-green?style=for-the-badge&logo=railway)](https://logistics-tracking-api-production.up.railway.app/docs)

---

## 👔 Executive Summary
In modern supply chain management, data accuracy and security are everything. **LogiTrack** solves the problem of untrusted data entry by providing a highly secure backend system where logistics personnel can log shipments, update item status, and track routes. 

### Core Features:
* **Secure Access Control:** Users must register and securely log in to interact with data. Unauthorized external entities cannot manipulate or view logistics logs.
* **Real-Time Data Management:** Designed to instantly handle data creations, updates, and lookups for moving supply chains.
* **Interactive Digital Documentation:** Built-in self-documenting interface allowing stakeholders or front-end teams to test capabilities live without writing any code.

---

## 🌐 Live Interactive Demo & Database Viewer
You can interact with the live system and view the cloud database immediately without setting up any code locally.

👉 **[Launch Live API Documentation & Swagger UI](https://logistics-tracking-api-production.up.railway.app/docs)**

### 🔒 Accessing the Secure System (Quick Walkthrough)
To protect supply chain integrity, both data insertion and database tracking are fully locked behind our JWT security layer. You can use our pre-configured demo account to test the system instantly:

1. **Log In:** Click the prominent green **Authorize 🔓** button at the top right of the Swagger UI page and enter these demo credentials:
   * **Username:** `admin`
   * **Password:** `password123`
2. Just click **Authorize**, then click **Close**. You are now authorized to submit new logistics records and view the live database.
3. **Post Data & View the Live Database:**
   * **Post Data:** Head over to `Shipment Tracking` ➔ `POST /logs` ➔ `Try it out` ➔ enter tracking details ➔ `Execute` to write new log data instantly.
   * **View the Live DB:** Head over to `Raw Database Content` ➔ `GET /tracking_database` ➔ `Try it out` ➔ `Execute` to see real-time JSON data logs pulled directly from our PostgreSQL cloud database (Neon).

> 🛠️ **Custom Accounts:** If you prefer to test the system with your own unique credentials instead of the demo account, simply head over to the `Create Account` ➔ `POST /register` ➔ `Try it out` ➔ enter your account details ➔ `Execute` to register your new account to our system. **Once registered, use your newly created credentials to log in.**


## 🛠️ Technical Overview & Architecture

### Tech Stack Justification
* **FastAPI:** Chosen for its industry-leading performance, high execution speed, and automated interactive API documentation generation.
* **PostgreSQL:** An enterprise-grade, highly reliable relational database optimized for handling complex relationships between users, shipments, and tracking logs.
* **SQLAlchemy (ORM):** Used to write clean, Pythonic database queries while protecting the application against SQL injection attacks.
* **JWT Authentication:** JSON Web Tokens ensure that all client-server communications are stateless, scalable, and fully protected.
* **Docker:** Containerized architecture ensures the system builds and runs perfectly across any server, avoiding the "works on my machine" dilemma.

### System Flow
1. **Client Request** ➔ 2. **JWT Authentication Layer** ➔ 3. **FastAPI Route Handlers** ➔ 4. **SQLAlchemy ORM Data Mapping** ➔ 5. **PostgreSQL Database Storage**

---
