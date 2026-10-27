# Resource Reservation System API

A Django REST Framework backend application designed for managing resource categories, resources, dynamic time-slot scheduling, and reservations with role-based access control and JWT authentication.

---

## Table of Contents
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Installation & Setup](#installation--setup)
- [Running Automated Tests](#running-automated-tests)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Resource & Category Management](#resource--category-management)
  - [User Resource & Reservation Actions](#user-resource--reservation-actions)

---

## Tech Stack
- **Framework:** Django 5.2, Django REST Framework
- **Authentication:** JWT via `djangorestframework-simplejwt`
- **Database:** SQLite (default)
- **Language:** Python 3.10+

---

## Key Features
- **Custom User Model:** Supports `user`, `organisation`, and `admin` roles.
- **JWT Authentication:** Secure token-based access with access and refresh tokens.
- **Role-Based Access Control:** Only organisations can create and configure resources; users can book and manage their own reservations.
- **Dynamic Slot Generation:** Calculates discrete time intervals between start and end hours based on `slot_interval`.
- **Double-Booking Prevention:** Validates overlapping time windows and prevents concurrent bookings.
- **Ownership Verification:** Users can only view or cancel their own reservations.
- **Pagination & Filtering:** Paginated reservations with optional filtering by status (`booked`, `cancelled`).
- **Comprehensive Test Suite:** 26 automated unit tests covering all features and edge cases.

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/svakhilr/Fegno-Machine-task.git
cd Fegno-Machine-task
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install django djangorestframework djangorestframework-simplejwt
```

### 4. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create superuser (optional, for Django admin)
```bash
python manage.py createsuperuser
```

### 6. Start the server
```bash
python manage.py runserver
```
The server will start at `http://127.0.0.1:8000/`.

---

## Running Automated Tests

Run the full test suite with:
```bash
python manage.py test
```
All **26 tests** should pass cleanly.

---

## API Documentation

### Base URL
```text
http://127.0.0.1:8000
```

### Authorization Header
For protected endpoints, include the JWT access token in the `Authorization` header:
```http
Authorization: Bearer <your_access_token>
```

---

### Authentication

#### 1. User Registration
Registers a standard user (`role: user`).

- **Endpoint:** `POST /users/register/user/`
- **Access:** Public

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "password": "strongpassword123"
}
```

**Response (`201 Created`):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "organisation_name": null,
    "role": "user",
    "is_active": true
  },
  "tokens": {
    "refresh": "<refresh_token>",
    "access": "<access_token>"
  }
}
```

---

#### 2. Organisation Registration
Registers an organisation (`role: organisation`).

- **Endpoint:** `POST /users/register/organisation/`
- **Access:** Public

**Request Body:**
```json
{
  "email": "contact@acme.org",
  "password": "orgpassword123",
  "organisation_name": "Acme Corporation"
}
```
*(Note: `organisation_name` is optional).*

**Response (`201 Created`):**
```json
{
  "message": "Organisation registered successfully",
  "user": {
    "id": 2,
    "email": "contact@acme.org",
    "first_name": "",
    "last_name": "",
    "organisation_name": "Acme Corporation",
    "role": "organisation",
    "is_active": true
  },
  "tokens": {
    "refresh": "<refresh_token>",
    "access": "<access_token>"
  }
}
```

---

#### 3. Login
Unified login endpoint for both regular users and organisations.

- **Endpoint:** `POST /users/login/`
- **Access:** Public

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "password": "strongpassword123"
}
```

**Response (`200 OK`):**
```json
{
  "message": "User login successful",
  "tokens": {
    "refresh": "<refresh_token>",
    "access": "<access_token>"
  }
}
```

*(Dedicated role-restricted endpoints are also available at `/users/login/user/` and `/users/login/organisation/`).*

---

### Resource & Category Management

#### 4. List & Create Categories
- **Endpoint:** `GET /resources/categories/` / `POST /resources/categories/`
- **Access:** Authenticated (`IsAuthenticated`)

**Create Request (`POST`):**
```json
{
  "name": "Meeting Rooms",
  "is_active": true
}
```

**Response (`201 Created`):**
```json
{
  "message": "Resource category created successfully",
  "data": {
    "id": 1,
    "name": "Meeting Rooms",
    "is_active": true,
    "created_at": "2026-10-27T10:00:00Z",
    "updated_at": "2026-10-27T10:00:00Z"
  }
}
```

---

#### 5. List & Create Resources (Organisation Only)
- **Endpoint:** `GET /resources/` / `POST /resources/`
- **Access:** Authenticated (`role: organisation`)

**Create Request (`POST`):**
```json
{
  "category": 1,
  "title": "Boardroom A",
  "slot_interval": 30,
  "slot_start_time": "09:00:00",
  "slot_end_time": "17:00:00",
  "is_active": true
}
```

**Response (`201 Created`):**
```json
{
  "message": "Resource created successfully",
  "data": {
    "id": 1,
    "organisation": 2,
    "category": 1,
    "title": "Boardroom A",
    "slot_interval": 30,
    "slot_start_time": "09:00:00",
    "slot_end_time": "17:00:00",
    "is_active": true,
    "category_name": "Meeting Rooms",
    "organisation_email": "contact@acme.org",
    "organisation_name": "Acme Corporation",
    "created_at": "2026-10-27T10:00:00Z",
    "updated_at": "2026-10-27T10:00:00Z"
  }
}
```

---

### User Resource & Reservation Actions

#### 6. List Active Resources
Lists available resources for users to browse.

- **Endpoint:** `GET /user/resource/`
- **Access:** Authenticated

**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "title": "Boardroom A",
    "organisation": "Acme Corporation"
  }
]
```

---

#### 7. Get Available Slots for a Date
Dynamically generates all time slots for a resource on a specific date, indicating whether each slot is already booked.

- **Endpoint:** `GET /user/resource/get_slot/?resource_id=1&date=2026-11-05`
- **Access:** Authenticated

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `resource_id` | Integer | Yes | ID of the resource |
| `date` | String | Yes | Date in `YYYY-MM-DD` format |

**Response (`200 OK`):**
```json
{
  "message": "Slots fetched successfully",
  "slots": [
    {
      "start_time": "09:00:00",
      "end_time": "09:30:00",
      "is_booked": false
    },
    {
      "start_time": "09:30:00",
      "end_time": "10:00:00",
      "is_booked": true
    },
    {
      "start_time": "10:00:00",
      "end_time": "10:30:00",
      "is_booked": false
    }
  ]
}
```

---

#### 8. Make a Reservation
Books a specific time slot for the authenticated user. Validates operating hours, format, and checks for double-bookings.

- **Endpoint:** `POST /user/resource/make_resevation/`
- **Access:** Authenticated

**Request Body:**
```json
{
  "resourse_id": 1,
  "date": "2026-11-05",
  "start_time": "10:00:00",
  "end_time": "10:30:00"
}
```

**Response (`201 Created`):**
```json
{
  "message": "Reservation made successfully",
  "reservation": {
    "id": 1,
    "user": 1,
    "user_email": "john.doe@example.com",
    "resource": 1,
    "resource_title": "Boardroom A",
    "organisation_name": "Acme Corporation",
    "category_name": "Meeting Rooms",
    "booking_status": "booked",
    "booking_date": "2026-11-05",
    "booking_slot_start_time": "10:00:00",
    "booking_slot_end_time": "10:30:00",
    "created_at": "2026-10-27T12:00:00Z",
    "updated_at": "2026-10-27T12:00:00Z"
  }
}
```

**Conflict Error (`400 Bad Request`):**
```json
{
  "message": "This slot is already booked. Please choose another slot."
}
```

---

#### 9. Cancel a Reservation
Cancels an existing reservation. Enforces an ownership check so users can only cancel their own reservations. Freeing the slot makes it available for booking again.

- **Endpoint:** `POST /user/resource/cancel_reservation/`
- **Access:** Authenticated

**Request Body:**
```json
{
  "reservation_id": 1
}
```

**Response (`200 OK`):**
```json
{
  "message": "Reservation cancelled successfully",
  "reservation": {
    "id": 1,
    "user": 1,
    "user_email": "john.doe@example.com",
    "resource": 1,
    "resource_title": "Boardroom A",
    "booking_status": "cancelled",
    "booking_date": "2026-11-05",
    "booking_slot_start_time": "10:00:00",
    "booking_slot_end_time": "10:30:00",
    "created_at": "2026-10-27T12:00:00Z",
    "updated_at": "2026-10-27T12:15:00Z"
  }
}
```

**Forbidden Error (`403 Forbidden`):**
```json
{
  "message": "You are not authorized to cancel this reservation"
}
```

---

#### 10. List User Reservations (Paginated)
Retrieves a paginated list of reservations belonging to the authenticated user.

- **Endpoint:** `GET /user/resource/user_reservations/`
- **Access:** Authenticated

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | Integer | 1 | Page number |
| `page_size` | Integer | 10 | Results per page (max 100) |
| `status` | String | null | Filter by `'booked'` or `'cancelled'` |

**Request Example:**
```http
GET /user/resource/user_reservations/?page=1&page_size=10&status=booked
```

**Response (`200 OK`):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "user_email": "john.doe@example.com",
      "resource": 1,
      "resource_title": "Boardroom A",
      "organisation_name": "Acme Corporation",
      "category_name": "Meeting Rooms",
      "booking_status": "booked",
      "booking_date": "2026-11-05",
      "booking_slot_start_time": "10:00:00",
      "booking_slot_end_time": "10:30:00",
      "created_at": "2026-10-27T12:00:00Z",
      "updated_at": "2026-10-27T12:00:00Z"
    }
  ]
}
```