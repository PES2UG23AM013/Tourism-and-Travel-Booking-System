🧳Tourism and Travel Booking System

A complete web-based travel management system built using Flask (Python) and MySQL, designed to manage customers, bookings, payments, tour packages, destinations, hotels, transport, and dependents for a travel agency.

📌Project Overview

The Tourism and Travel Booking System is a full-stack database-driven application designed to streamline travel agency operations.
It supports:

Customer onboarding

Booking and payment handling

Tour package management

Dependent management

Travel itineraries

Hotels, destinations, transport

Stored procedures, functions, triggers

Dashboard analytics & advanced SQL queries

The project focuses on database design, relational mapping, and SQL automation through triggers and procedures.

⭐Features
🧑‍💼 Customer Management

Add/update/delete customers

Multi-valued phone numbers

Travel dependents (weak entity)

🧾 Booking & Payment

Create bookings

Add payments

Auto-update booking status to Paid using a trigger

🧳 Package Management

Create/manage tour packages

Link with hotels, destinations, transport via M:N relationships

🏨 Hotel, Destination, Transport

Maintain resource details

Integrated with packages and itineraries

🧩 Advanced SQL

Triggers

Stored Procedures

Functions

Views

Nested queries

Aggregates

Joins

📊 Dashboard

Total customers

Total bookings

Total payments

Navigation to all modules

🛠️ Tech Stack
Backend

Python Flask

MySQL

MySQL Connector

Frontend

HTML

CSS

Bootstrap

Jinja templates

Tools

VS Code

XAMPP

GitHub

phpMyAdmin


🗄️ Database Features (Core DBMS Components)
✔ Triggers

trg_before_insert_dependent → Validates dependent age

trg_after_payment_insert → Auto-updates booking status

✔ Stored Procedures

calculate_package_total_cost

get_bookings_by_customer

✔ Functions

TotalAmountSpent

fn_count_dependents

✔ Views

Booking overview

Package–transport mapping



✔ Advanced Queries

Top 3 most expensive packages (nested)

Total dependents per customer (aggregate)

Confirmed bookings with hotel details (join)

📁 Project Structure
Tourism-and-Travel-Booking-System/
│
├── app.py
├── requirements.txt
├── tourism_and_travel_booking_system.sql
│
├── templates/
│   ├── dashboard.html
│   ├── customers.html
│   ├── bookings.html
│   ├── payments.html
│   ├── packages.html
│   ├── destinations.html
│   ├── hotels.html
│   ├── transports.html
│   ├── procedures.html
│   ├── functions.html
│   ├── advanced_queries.html
│   ├── login.html
│   ├── register.html
│   └── (other UI files)
│
└── static/
    ├── styles.css



⚙️ How to Run the Project
1️⃣ Install dependencies
pip install -r requirements.txt

2️⃣ Import the SQL file

Open phpMyAdmin

Create database:

Tourism_and_Travel_Booking_System


Import:

tourism_and_travel_booking_system.sql

3️⃣ Start Flask server
python app.py

4️⃣ Open in browser
http://127.0.0.1:5000/


Screenshots

All screenshots used in the report (dashboard, CRUD, procedures, functions, advanced queries) are available in the folder:

/screenshots

🧩 Future Enhancements

Improved role-based authentication

Automated dynamic itinerary planner

Email notifications

PDF invoice generator

AI-based package recommendation

