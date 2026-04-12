# medical-appointment-django



# 🏥 Medical Appointment Web Application

A full-featured Django web application where patients can book appointments with doctors online, doctors manage schedules, and admins oversee the system.

![Django Version](https://img.shields.io/badge/django-6.0-green)
![Python Version](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Bootstrap](https://img.shields.io/badge/bootstrap-5.3-purple)

---

## 🚀 Live Demo

> *To be deployed – currently localhost only*

---

## ✨ Features

### 👤 Authentication System
- User registration & login with role selection (Patient / Doctor)
- Role-based access control (Patient, Doctor, Admin)
- Profile management for each role

### 🏥 Patient Features
- View list of doctors filtered by specialization
- Book appointments (date, time, doctor)
- View and cancel upcoming appointments

### 👨‍⚕️ Doctor Features
- View appointment requests
- Accept / reject appointments
- Manage availability schedule (add/edit/delete time slots)

### 🛠️ Admin Features
- Full user management (CRUD)
- Manage doctor specializations
- View all appointments system-wide

---

## 🧰 Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Backend     | Django 6.0 (Python)                 |
| Database    | SQLite (development)                |
| Frontend    | Django Templates + Bootstrap 5      |
| Icons       | Bootstrap Icons                     |
| ORM         | Django ORM                          |

---

## 📁 Project Structure


medical_appointment/
├── medical_appointment/ # Project settings
├── appointments/ # Main app (models, views, forms, templates)
│ ├── templates/ # HTML files
│ ├── static/ # CSS, JS, images (optional)
│ ├── models.py # Database models
│ ├── views.py # Logic (CBVs & FBVs)
│ ├── forms.py # Form definitions
│ ├── urls.py # App URLs
│ └── decorators.py # Role-based access decorators
├── db.sqlite3 # SQLite database (ignored in git)
├── manage.py
└── requirements.txt




## ⚙️ Setup Instructions (for local development)

### Prerequisites
- Python 3.11 or higher
- pip
- Git

### Step 1: Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/medical-appointment-django.git
cd medical-appointment-django


Step 2: Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

Step 3: Install dependencies
pip install django

Step 4: Run migrations

python manage.py makemigrations appointments
python manage.py migrate

Step 5: Create a superuser (admin)
python manage.py createsuperuser
Set role to admin after creation via Django admin or shell.


Step 7: Run the development server
python manage.py runserver





