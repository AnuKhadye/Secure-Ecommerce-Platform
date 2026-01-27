# Secure E-Commerce Platform (Flask)

A security-focused e-commerce web application built in Python using Flask, demonstrating secure-by-design principles, threat modelling, and mitigation of common web vulnerabilities.

This project was developed as part of the **6000CMD – Security** module and is included here as a **portfolio project** to showcase secure software engineering skills.

---

## Project Overview

This application simulates a small online retail platform supporting:
- User registration and authentication
- Product browsing and purchasing
- Reviews and seller-managed listings
- Role-based access control (Customer, Seller, Admin)

The primary focus of the project is **security**, not scale or UI polish. Industry-aligned security practices were applied throughout the system lifecycle.

---

## Tech Stack

- **Backend:** Python 3, Flask
- **Frontend:** HTML5, CSS3, Jinja2
- **Database:** SQLite
- **Security Libraries:**  
  - Flask-WTF (CSRF protection)  
  - Werkzeug (password hashing)  
  - Bleach (XSS sanitisation)
- **Security Analysis:** Bandit (static analysis)

---

## Security Features Implemented

### Authentication & Session Security
- Password hashing using **PBKDF2-HMAC**
- Secure server-side sessions
- Session regeneration on login
- HttpOnly and SameSite cookie flags

### Authorisation (RBAC)
- Role-Based Access Control with three roles:
  - Customer
  - Seller
  - Administrator
- Ownership checks to prevent IDOR attacks
- Server-side enforcement via decorators

### Input Validation & Data Protection
- Parameterised SQL queries (SQL injection mitigation)
- HTML sanitisation of user-generated content using Bleach
- Jinja2 auto-escaping
- MIME-type validation for uploads

### Request Integrity
- CSRF tokens on all state-changing routes
- POST-only semantics for destructive actions
- Inventory re-validation during checkout (TOCTOU protection)

---

## Security Testing & Audit

- **Static Analysis:** Bandit  
  - Identified development-only risks (debug mode, hardcoded secrets)
  - All findings reviewed and contextualised
- **Manual Dynamic Testing:**  
  - SQL injection → blocked  
  - Stored XSS → sanitised  
  - CSRF attacks → blocked  
  - Privilege escalation (IDOR) → blocked via RBAC  

The application successfully mitigates key OWASP Top 10 risks.

---

## Project Structure
```
/static/        : CSS and assets
/templates/     : Jinja2 HTML templates
/db/            : SQLite database files
app.py          : Main Flask application
forms.py        : Form definitions
database.py     : Database access logic
```

---

## Running the Project Locally
```bash
git clone https://github.com/AnuKhadye/Secure-Ecommerce-Platform.git
cd Secure-Ecommerce-Platform
pip install -r requirements.txt
python app.py
```

Then open:
http://localhost:5000


---

## Key Learning Outcomes

- Applied STRIDE threat modelling to a real system
- Implemented secure authentication and RBAC
- Mitigated OWASP Top 10 vulnerabilities in practice
- Performed static security analysis and manual testing
- Designed a layered, security-oriented web architecture


---

## Limitations & Future Work

- No multi-factor authentication
- SQLite used for simplicity (not production scale)
- Limited automated dynamic testing
- No deployment hardening (HTTPS, WAF, containerisation)


---

## Disclaimer

This project is a secure prototype developed for educational and portfolio purposes and is not intended for production deployment without further hardening.


