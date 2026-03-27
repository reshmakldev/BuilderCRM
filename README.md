# Real Estate Builder CRM

A premium CRM solution for Real Estate Builders built with Django and Bootstrap 5.

## Features

- **Dashboard**: Overview of leads, projects, and inventory.
- **Lead Management**: Track leads through different stages (New, Contacted, Qualified, etc.).
- **Property Management**: Manage Projects and Units (Inventory).
- **Responsive Design**: Beautiful glassmorphism UI that works on all devices.

## Setup

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**:
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You may need to generate this file first using `pip freeze > requirements.txt`)*

4. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run Server**:
   ```bash
   python manage.py runserver
   ```

## Default Credentials

- **Username**: admin
- **Password**: admin123

## Apps

- **Core**: Dashboard and base templates.
- **Leads**: Lead tracking and management.
- **Properties**: Project and Unit inventory management.
