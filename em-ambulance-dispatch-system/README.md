# Ambulance Management System API

A FastAPI-based ambulance management system with JWT authentication, role-based authorization, and separate APIs for authentication, users, admins, ambulances, ambulance requests, and trips.

## API Summary

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new passenger |
| POST | `/auth/login` | Login and receive JWT access token |
| GET | `/auth/google` | Start Google sign-in |
| GET | `/auth/facebook` | Start Facebook sign-in |
| POST | `/auth/oauth/exchange` | Exchange a one-time OAuth code for a JWT |
| GET | `/auth/me` | Get the currently authenticated user |

Google and Facebook sign-in require `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`FACEBOOK_CLIENT_ID`, and `FACEBOOK_CLIENT_SECRET` in the backend environment.
Register these callback URLs with the providers:

- `{BACKEND_URL}/api/v1/auth/google/callback`
- `{BACKEND_URL}/api/v1/auth/facebook/callback`

The backend redirects successful sign-ins to `{FRONTEND_URL}/oauth/callback`.

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/me` | Get own profile |
| PUT | `/users/me` | Update own profile |
| DELETE | `/users/me` | Deactivate own account |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/users` | Get all users |
| GET | `/admin/users/{user_id}` | Get a specific user |
| DELETE | `/admin/users/{user_id}` | Deactivate a user |
| POST | `/admin/drivers` | Create a driver |
| GET | `/admin/drivers` | Get all drivers |
| POST | `/admin/ambulances` | Create an ambulance |
| PUT | `/admin/ambulances/{ambulance_id}` | Update an ambulance |
| DELETE | `/admin/ambulances/{ambulance_id}` | Delete an ambulance |

### Ambulances

| Method | Endpoint | Description |
|---|---|---|
| GET | `/ambulances/` | Get all ambulances |
| GET | `/ambulances/available` | Get available ambulances |
| GET | `/ambulances/{ambulance_id}` | Get a specific ambulance |
| GET | `/ambulances/my/ambulance` | Get the driver's assigned ambulance |
| PUT | `/ambulances/my/ambulance/status` | Update assigned ambulance status |

### Ambulance Requests

#### Passenger

| Method | Endpoint | Description |
|---|---|---|
| POST | `/requests/` | Create an ambulance request |
| GET | `/requests/my` | Get own requests |
| GET | `/requests/my/{request_id}` | Get a specific own request |
| POST | `/requests/{request_id}/cancel` | Cancel a pending request |

#### Driver

| Method | Endpoint | Description |
|---|---|---|
| GET | `/requests/pending` | Get pending requests |
| POST | `/requests/{request_id}/accept` | Accept a request |
| POST | `/requests/{request_id}/reject` | Reject a request |

#### Admin

| Method | Endpoint | Description |
|---|---|---|
| GET | `/requests/admin/all` | Get all ambulance requests |

### Trips

#### Passenger

| Method | Endpoint | Description |
|---|---|---|
| GET | `/trips/my` | Get own trips |
| GET | `/trips/my/{trip_id}` | Get a specific own trip |

#### Driver

| Method | Endpoint | Description |
|---|---|---|
| GET | `/trips/driver/my` | Get driver's trips |
| POST | `/trips/{trip_id}/start` | Start a trip |
| POST | `/trips/{trip_id}/complete` | Complete a trip |
| PUT | `/trips/{trip_id}/fare` | Update trip fare |

#### Admin

| Method | Endpoint | Description |
|---|---|---|
| GET | `/trips/admin/all` | Get all trips |

---

## Authentication Flow

The application uses JWT (JSON Web Token) authentication.

### 1. Register

A new passenger can register through:

```http
POST /auth/register
```

Example request:

```json
{
    "username": "rahim",
    "email": "rahim@gmail.com",
    "firstname": "Rahim",
    "lastname": "Ahmed",
    "password": "123456"
}
```

The public registration endpoint does not accept a `role`.

A newly registered user automatically receives:

```text
role = passenger
```

### 2. Login

Login through:

```http
POST /auth/login
```

The endpoint uses OAuth2 password form data:

```text
username=rahim
password=123456
```

Successful response:

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

### 3. Send the JWT

Authenticated requests use:

```http
Authorization: Bearer <access_token>
```

For example:

```http
GET /users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 4. Get Current User

The current authenticated user can be retrieved with:

```http
GET /auth/me
```

The JWT contains information such as:

```json
{
    "sub": "rahim",
    "id": 5,
    "role": "passenger",
    "exp": "..."
}
```

The token is signed with the application's JWT secret and validated before protected endpoints are accessed.

---

## Role Authorization

Authentication and authorization are separate concepts.

### Authentication

Authentication answers:

> Who are you?

JWT authentication is responsible for identifying the user.

```text
Login
  ↓
JWT token
  ↓
Validate token
  ↓
Find user
  ↓
Authenticated
```

### Authorization

Authorization answers:

> What are you allowed to do?

The application uses role-based dependencies:

```text
admin_dependency
driver_dependency
passenger_dependency
```

### Admin

Endpoints requiring:

```python
admin: admin_dependency
```

allow only users with:

```text
role = admin
```

Admins can manage users, drivers, and ambulances.

### Driver

Endpoints requiring:

```python
driver: driver_dependency
```

allow only users with:

```text
role = driver
```

Drivers can manage their assigned ambulance status, accept requests, and manage their trips.

### Passenger

Endpoints requiring:

```python
passenger: passenger_dependency
```

allow only users with:

```text
role = passenger
```

Passengers can create ambulance requests and view their own requests and trips.

### Authorization Flow

```text
JWT token
    ↓
Token valid?
    ↓
User exists?
    ↓
User active?
    ↓
Check role
    ↓
┌─────────┬─────────┬───────────┐
│  admin  │ driver  │ passenger │
└─────────┴─────────┴───────────┘
    ↓          ↓          ↓
  Admin      Driver    Passenger
   APIs       APIs        APIs
```

If the JWT is invalid, the API returns:

```http
401 Unauthorized
```

If the user is authenticated but does not have the required role, the API returns:

```http
403 Forbidden
```

---

## Important Role Design

The public registration endpoint should **not allow users to choose their own role**.

Do not expose registration like:

```json
{
    "username": "hacker",
    "password": "123456",
    "role": "admin"
}
```

Otherwise, a user could potentially register themselves as an administrator.

Instead, public registration only accepts normal user information:

```json
{
    "username": "rahim",
    "email": "rahim@gmail.com",
    "firstname": "Rahim",
    "lastname": "Ahmed",
    "password": "123456"
}
```

The system automatically assigns:

```text
passenger
```

### Creating Drivers

Drivers are created by an authenticated admin:

```http
POST /admin/drivers
```

The server explicitly assigns:

```text
role = driver
```

### Creating Admins

Admin accounts should not be created through public registration.

They can be created through an initial seed/setup process or another protected administrative mechanism.

This gives the application the following role structure:

```text
                    USER
                     │
          ┌──────────┼──────────┐
          │          │          │
        ADMIN      DRIVER    PASSENGER
          │          │          │
          │          │          └── Create request
          │          │                    │
          │          │                    ▼
          │          │                 PENDING
          │          │                    │
          │          └──── Accept ────────┘
          │                               │
          │                               ▼
          │                             TRIP
          │                               │
          │                         ┌─────┴─────┐
          │                         │           │
          │                       Start      Complete
          │                         │           │
          │                         ▼           ▼
          │                      ONGOING    COMPLETED
          │
          ├── Manage users
          ├── Manage drivers
          └── Manage ambulances
```

---

## Request and Trip Flow

A typical ambulance request follows this lifecycle:

```text
Passenger
    │
    │ POST /requests/
    ▼
 PENDING
    │
    ├──────────── Driver rejects
    │                    │
    │                    ▼
    │                 REJECTED
    │
    └──────────── Driver accepts
                         │
                         ▼
                     ACCEPTED
                         │
                         ▼
                    Trip created
                         │
                         ▼
                      ONGOING
                         │
                         │ Driver completes
                         ▼
                     COMPLETED
```

When a driver accepts a request:

1. The request becomes `accepted`.
2. The driver's available ambulance is assigned.
3. The ambulance becomes `busy`.
4. A trip is created.

When the driver completes the trip:

1. The trip becomes `completed`.
2. The request becomes `completed`.
3. The trip receives an end time.
4. The ambulance becomes `available`.

---

## Swagger Documentation

Start the application:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

FastAPI provides interactive Swagger documentation.

After logging in, use the **Authorize** button and provide the OAuth2 credentials.

The protected endpoints will then send the JWT automatically.

---

## API Role Overview

| Feature | Admin | Driver | Passenger |
|---|:---:|:---:|:---:|
| Register | — | — | ✓ |
| Login | ✓ | ✓ | ✓ |
| View own profile | ✓ | ✓ | ✓ |
| Manage users | ✓ | — | — |
| Create drivers | ✓ | — | — |
| Manage ambulances | ✓ | — | — |
| Update own ambulance status | — | ✓ | — |
| Create ambulance request | — | — | ✓ |
| View pending requests | — | ✓ | — |
| Accept/reject requests | — | ✓ | — |
| View own requests | — | — | ✓ |
| Cancel own request | — | — | ✓ |
| View own trips | — | ✓ | ✓ |
| Start trip | — | ✓ | — |
| Complete trip | — | ✓ | — |
| View all requests | ✓ | — | — |
| View all trips | ✓ | — | — |

---

## Project Architecture

```text
                    FastAPI
                       │
       ┌───────────────┼────────────────┐
       │               │                │
     Routers       Authentication    Authorization
       │               │                │
       │              JWT              Roles
       │               │                │
       └───────────────┼────────────────┘
                       │
                   SQLAlchemy
                       │
                    Database
```

The application separates:

- Authentication
- Authorization
- Users
- Admin operations
- Ambulances
- Ambulance requests
- Trips
- Database models
- Pydantic schemas
- Enums

This structure keeps the FastAPI project easier to maintain as more features are added.
