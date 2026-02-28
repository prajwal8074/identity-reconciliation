# Bitespeed Identity Reconciliation 📦

A robust identity linking service built for FluxKart.com to consolidate customer data across multiple purchases. This service identifies when different orders (using varying email addresses or phone numbers) belong to the same individual, ensuring a personalized customer experience for even the most "eccentric" shoppers.

## 🛠️ Technical Stack

* **Backend:** Python (Flask)
* **Database:** PostgreSQL (Raw SQL Queries)
* **Testing:** Python `unittest` (Integration Testing)
* **CI/CD:** GitHub Actions
* **Environment:** Docker-ready, Python-dotenv for configuration

## 🏃 Quick Start

### 1. Prerequisites

* Python 3.10+
* PostgreSQL instance running locally or in the cloud.

### 2. Installation

clone the repository
cd into repo folder

```python
pip install -r requirements.txt
```
create a postgres db named bitespeed_db
```bash
psql "postgresql://user:password@localhost/bitespeed_db" -f schema.sql
```
create .env and write DATABASE_URL=postgresql://user:password@localhost:5432/bitespeed_db <br>
(replace user and password with your postgres credentials in above lines)
```python
python app.py
```
run unit tests using
```python
python test.py
```
(app.py should be running while testing)
