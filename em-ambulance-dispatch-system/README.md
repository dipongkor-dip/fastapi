# CallNow Ambulance Dispatch API

CallNow is a FastAPI backend for ambulance dispatch and patient transport. It provides authentication, role-based authorization, ambulance fleet management, ride requests, trip coordination, payment processing, password recovery, social login, and administrative operations.

The API is consumed by the CallNow React frontend and is mounted under the `/api/v1` prefix.

## Product Capabilities

- Passenger registration and JWT login.
- Google and Facebook OAuth authentication.
- Role-based access for passengers, drivers, admins, and superadmins.
- Ambulance fleet registration, lookup, status management, and pagination.
- Passenger ambulance requests with pickup and destination details.
- Driver dispatch queue with accept/reject actions.
- Trip lifecycle management from ongoing to completed.
- Fare updates for completed transport coordination.
- SSLCommerz payment initialization and callback handling.
- Password reset through Redis-backed email OTP verification.
- User profile updates and account deactivation.
- Admin user, driver, ambulance, request, trip, and payment operations.
- Interactive OpenAPI documentation through Swagger UI.

## Technology Stack

### API and runtime

- Python 3.12
- FastAPI 0.141
- Uvicorn
- Starlette middleware
- Pydantic 2 and Pydantic Settings
- Python type annotations and dependency injection

### Database

- SQLAlchemy 2
- MySQL-compatible database support through PyMySQL
- Alembic migrations
- Relational models for users, social identities, ambulances, requests, trips, and payments

### Authentication and security

- JWT access tokens with `python-jose`
- Password hashing with Passlib and bcrypt
- OAuth2 password flow for login
- Role-based authorization dependencies
- Authlib for Google and Facebook OAuth
- Starlette session middleware for OAuth state
- Proxy header middleware for deployed HTTPS environments
- CORS middleware for frontend access

### Infrastructure and integrations

- Redis or Upstash Redis for OTP and one-time OAuth exchange codes
- Mailtrap email delivery for password recovery and receipts
- Cloudinary for cloud media services
- SSLCommerz payment gateway
- ReportLab for payment receipt generation
- HTTPX and Requests for external service communication

### Development and operations

- Pytest
- Docker with Python 3.12 Slim
- Environment configuration through `.env`
- FastAPI OpenAPI and Swagger UI

## Architecture

```text
fastapi/em-ambulance-dispatch-system/
├── main.py                 FastAPI application, middleware, and routers
├── config.py               Pydantic Settings environment configuration
├── database.py             SQLAlchemy engine, session, and Base
├── models.py               Database models
├── schemas.py              Request and response schemas
├── enums.py                User, request, trip, ambulance, and payment states
├── requirements.txt        Locked Python dependencies
├── migrations/             SQL migration files
├── router/
│   ├── auth.py             Registration, login, OTP, password changes
│   ├── socialAuth.py       Google and Facebook OAuth flows
│   ├── users.py            Current-user profile operations
│   ├── admin.py            Admin user, driver, and fleet operations
│   ├── ambulances.py       Fleet lookup and driver status operations
│   ├── ambulance_requests.py Passenger and driver request workflows
│   ├── trips.py            Passenger, driver, and admin trip workflows
│   └── payments.py         Payment creation, callbacks, history, receipts
└── utils/
    ├── auth.py             JWT, password hashing, and role dependencies
    ├── bootstrap.py        Default superadmin setup
    ├── redis.py            Redis client configuration
    ├── email_sending.py    Email delivery helpers
    ├── sslcommerz.py       Payment gateway integration
    ├── payment_receipt.py  Receipt generation and delivery
    └── cloudinary*.py      Cloudinary configuration and helpers
```

## API Base URL

Local development uses:

```text
http://127.0.0.1:8000/api/v1
```

The root health endpoint is outside the versioned API:

```text
GET /
```

It returns a simple server-running message.

## API Routes

All routes below are relative to `/api/v1`.

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/auth/register` | Register a passenger account |
| POST | `/auth/login` | Login with OAuth2 password form data |
| POST | `/auth/send-otp` | Send a password reset OTP |
| POST | `/auth/verify-otp` | Verify a password reset OTP |
| POST | `/auth/reset-password` | Reset a password after OTP verification |
| POST | `/auth/change-password` | Change the authenticated user password |
| GET | `/auth/google` | Start Google OAuth |
| GET | `/auth/google/callback` | Handle Google OAuth callback |
| GET | `/auth/facebook` | Start Facebook OAuth |
| GET | `/auth/facebook/callback` | Handle Facebook OAuth callback |
| POST | `/auth/oauth/exchange` | Exchange a one-time OAuth code for a JWT |

Successful social login redirects to the frontend OAuth callback route with a
short-lived one-time code.

### Users

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/users/me` | Get the authenticated user profile |
| PUT | `/users/me` | Update the authenticated user profile |
| DELETE | `/users/me` | Deactivate the authenticated account |

### Admin

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/admin/create-admin` | Create an admin; superadmin only |
| GET | `/admin/users` | List all users |
| GET | `/admin/users/{id}` | Get one user |
| DELETE | `/admin/users/{id}` | Deactivate one user |
| POST | `/admin/drivers` | Create a driver |
| GET | `/admin/drivers` | List drivers |
| POST | `/admin/ambulances` | Create an ambulance |
| PUT | `/admin/ambulances/{id}` | Update an ambulance |
| DELETE | `/admin/ambulances/{id}` | Delete an ambulance |

### Ambulances

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/ambulances/` | Paginated fleet list with optional status/search filters |
| GET | `/ambulances/{id}` | Get one ambulance |
| GET | `/ambulances/my/ambulance` | Get the authenticated driver's assigned ambulance |
| PUT | `/ambulances/my/ambulance/status` | Update the driver's assigned ambulance status |

#### Ambulance list query parameters

```text
GET /api/v1/ambulances/?page=1&page_size=12
GET /api/v1/ambulances/?page=1&page_size=24&status=available
GET /api/v1/ambulances/?page=1&page_size=36&search=ABC
```

Supported status values are:

```text
available
busy
maintenance
```

The response is:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 12,
  "pages": 0
}
```

The list endpoint applies status and text search filters before calculating the
page total. Search checks the ambulance number, type, and model.

### Ambulance requests

#### Passenger

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/requests/` | Create an ambulance request |
| GET | `/requests/my` | List the passenger's requests |
| GET | `/requests/my/{id}` | Get one passenger request |
| POST | `/requests/{id}/cancel` | Cancel a pending request |

#### Driver

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/requests/pending` | List pending requests |
| POST | `/requests/{id}/accept` | Accept a request and create a trip |
| POST | `/requests/{id}/reject` | Reject a pending request |

#### Admin

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/requests/admin/all` | List all requests |

### Trips

#### Passenger

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/trips/my` | List the passenger's trips |
| GET | `/trips/my/{id}` | Get one passenger trip |

#### Driver

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/trips/driver/my` | List the driver's trips |
| POST | `/trips/{id}/start` | Set a trip start time |
| POST | `/trips/{id}/complete` | Complete a trip and release the ambulance |
| PUT | `/trips/{id}/fare` | Update a trip fare |

#### Admin

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/trips/admin/all` | List all trips |

### Payments

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/payments/create/{id}` | Initialize payment for a trip |
| GET | `/payments/all` | List all payments; admin only |
| GET | `/payments/my` | List passenger or driver payment history |
| GET | `/payments/transaction/{transaction_id}` | Get one passenger payment |
| POST | `/payments/success` | Process the payment gateway success callback |
| POST | `/payments/cancel` | Process the payment gateway cancellation callback |
| POST | `/payments/fail` | Process the payment gateway failure callback |

Payment callback routes are called by the payment gateway and redirect the
browser to the frontend payment result route.

## Authentication and Authorization

### JWT flow

1. A passenger registers through `/auth/register`.
2. The account receives the default `passenger` role.
3. The user logs in through `/auth/login`.
4. The API returns a JWT access token.
5. Protected requests send the token as:

```http
Authorization: Bearer <access_token>
```

6. The backend validates the token, loads the user, checks account activity,
   and applies the endpoint's role dependency.

### Roles

| Role | Main permissions |
| --- | --- |
| `passenger` | Create and manage own requests, trips, profile, and payments |
| `driver` | View pending requests, accept/reject requests, manage trips and assigned ambulance |
| `admin` | Manage users, drivers, ambulances, requests, trips, and payments |
| `superadmin` | Admin management and protected administrative setup |

Public registration never accepts a role. Drivers and admins are created only
through protected administrative or bootstrap flows.

Typical authorization responses:

- `401 Unauthorized` means the token is missing, invalid, expired, or the user
  cannot be authenticated.
- `403 Forbidden` means the user is authenticated but lacks the required role.
- `404 Not Found` means the requested resource does not exist or is not visible
  to the current user.

## Request and Trip Lifecycle

```text
Passenger creates request
        |
        v
     PENDING
      /    \
     /      \
 Reject    Accept
   /          |
  v           v
REJECTED   ACCEPTED -> Trip ONGOING
                         |
                         v
                    Trip COMPLETED
```

When a driver accepts a request:

1. The request changes to `accepted`.
2. An available ambulance assigned to that driver is selected.
3. The ambulance changes to `busy`.
4. A trip is created with `ongoing` status.

When the driver completes the trip:

1. The trip changes to `completed`.
2. The request changes to `completed`.
3. The trip receives an end timestamp.
4. The ambulance changes back to `available`.

## Environment Configuration

Create a `.env` file in this backend directory. The following names are read by
`config.py`:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/callnow
JWT_SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

SUPERADMIN_USERNAME=admin
SUPERADMIN_EMAIL=admin@example.com
SUPERADMIN_FIRSTNAME=System
SUPERADMIN_LASTNAME=Administrator
SUPERADMIN_PASSWORD=replace-with-a-secure-password

EMAIL_SENDER=sender@example.com
EMAIL_PASSWORD=mail-provider-password

UPSTASH_REDIS_REST_URL=https://your-instance.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token

SSLCOMMERZ_STORE_ID=your-store-id
SSLCOMMERZ_STORE_PASSWORD=your-store-password
SSLCOMMERZ_BASE_URL=https://sandbox.sslcommerz.com

BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

OAuth provider callback URLs:

```text
{BACKEND_URL}/api/v1/auth/google/callback
{BACKEND_URL}/api/v1/auth/facebook/callback
```

The backend redirects successful OAuth login to:

```text
{FRONTEND_URL}/oauth/callback
```

Do not commit `.env` files or expose these credentials in frontend code.

## Local Development

Create and activate a Python 3.12 virtual environment, then install the
pinned dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the development server:

```bash
uvicorn main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

## Database and Migrations

The application creates the SQLAlchemy metadata during startup and uses
Alembic migration files for tracked schema changes.

Typical Alembic commands:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe schema change"
alembic downgrade -1
```

Run migrations before starting the API in a new deployment. Confirm that the
configured database user can create and alter the required tables.

## Docker

The included Dockerfile uses Python 3.12 Slim, installs `requirements.txt`,
and serves the API on port 8000.

Build the image:

```bash
docker build -t callnow-backend .
```

Run the container:

```bash
docker run --rm -it \
  -p 8000:8000 \
  --env-file .env \
  callnow-backend
```

Open the API documentation at `http://localhost:8000/docs`.

## Testing

Run the backend test suite from this directory:

```bash
pytest
```

For a focused test run:

```bash
pytest -q path/to/test_file.py
```

Tests should use a test database and isolated external-service configuration.
Do not use production payment, email, Redis, or Cloudinary credentials in test
runs.

## CORS and Deployment

The application allows the configured frontend URL and local Vite development
origin through FastAPI CORS middleware. For deployment:

- Set `FRONTEND_URL` to the exact deployed frontend origin.
- Set `BACKEND_URL` to the public HTTPS backend origin.
- Register OAuth callback URLs using the deployed backend URL.
- Configure SSLCommerz success, cancel, and failure callbacks.
- Use a strong, unique `JWT_SECRET_KEY`.
- Keep database, Redis, email, OAuth, payment, and Cloudinary secrets outside
  source control.
- Run behind HTTPS and a trusted reverse proxy.
- Run Alembic migrations before serving traffic.

## API Documentation and Frontend

The React frontend lives in the sibling `embulance-dispatch-frontend`
project. It uses RTK Query and Axios to call this API, stores the JWT access
session in the browser, and provides role-specific dashboards.

Frontend local URL:

```text
http://localhost:5173
```

Backend local URL:

```text
http://localhost:8000
```
