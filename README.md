# Plugus Platform

A multi-role service marketplace platform built with FastAPI and React Native.

## Tech Stack

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL 15
- SQLAlchemy 2.0
- Alembic (migrations)
- JWT Authentication
- Role-Based Access Control (RBAC)
- WebSockets for real-time updates

**Frontend:**
- React Native (Expo)
- Role-based navigation
- Google Maps integration

## Roles

| Role | Description |
|------|-------------|
| Customer | Browse services, book, track, review |
| Vendor | Manage services, workers, orders |
| Worker | View tasks, update location, complete |
| Regional Admin | Approve vendors, view revenue |
| Super Admin | Manage admins, categories, analytics |

## Quick Start

### 1. Start PostgreSQL (Docker)

```bash
docker-compose up -d db
```

Or use existing PostgreSQL and update `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/plugus
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Create super admin
python -m scripts.create_super_admin

# Start server
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start Expo
npx expo start --web
```

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@plugus.com | admin123 |

## API Endpoints

### Auth
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register (Customer/Vendor)
- `GET /api/v1/auth/me` - Current user

### Customer
- `GET /api/v1/customer/categories` - Browse categories
- `GET /api/v1/customer/vendors` - List vendors
- `GET /api/v1/customer/services` - List services
- `POST /api/v1/customer/bookings` - Create booking
- `GET /api/v1/customer/bookings` - My bookings
- `POST /api/v1/customer/reviews` - Submit review
- `POST /api/v1/customer/complaints` - File complaint

### Vendor
- `CRUD /api/v1/vendor/services` - Manage services
- `CRUD /api/v1/vendor/workers` - Manage workers
- `GET /api/v1/vendor/orders` - View orders
- `PUT /api/v1/vendor/orders/{id}/accept` - Accept order
- `PUT /api/v1/vendor/orders/{id}/assign-worker` - Assign worker
- `GET /api/v1/vendor/revenue` - Revenue analytics

### Worker
- `GET /api/v1/worker/tasks` - View tasks
- `PUT /api/v1/worker/tasks/{id}/start` - Start task
- `PUT /api/v1/worker/tasks/{id}/complete` - Complete task
- `PUT /api/v1/worker/location` - Update location

### Admin
- `GET /api/v1/admin/vendors` - Pending vendors
- `PUT /api/v1/admin/vendors/{id}/approve` - Approve vendor
- `GET /api/v1/admin/revenue/vendors` - Revenue per vendor
- `CRUD /api/v1/admin/categories` - Manage categories
- `CRUD /api/v1/admin/admins` - Manage regional admins

## Booking State Machine

```
CREATED → VENDOR_ACCEPTED → WORKER_ASSIGNED → IN_PROGRESS → COMPLETED → PAYMENT_UPLOADED
                ↓
          VENDOR_REJECTED
```

## Complaint Escalation

Complaints auto-escalate after 24 hours:
1. Vendor (Level 1)
2. Regional Admin (Level 2)
3. Super Admin (Level 3)

## Docker Deployment

### Development (Quick Start)

```bash
# Copy environment file
copy .env.docker .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

This starts:
- **PostgreSQL** on port 5432
- **Backend API** on port 8000
- **Redis** on port 6379

### Production (with Nginx)

```bash
# Copy and edit environment
copy .env.docker .env
# Edit .env with secure passwords and secrets

# Start with production profile (includes Nginx)
docker-compose --profile production up -d
```

Production adds:
- **Nginx** on ports 80/443 with:
  - Rate limiting
  - WebSocket support
  - SSL termination (configure certs in nginx/ssl/)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Database password | plugus_secret |
| `SECRET_KEY` | JWT signing key | (change in production!) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 1440 (24h) |

### Useful Commands

```bash
# Rebuild after code changes
docker-compose build backend

# Restart backend
docker-compose restart backend

# View database
docker exec -it plugus_db psql -U plugus -d plugus

# Stop all
docker-compose down

# Stop and remove volumes (reset data)
docker-compose down -v
```

## License

MIT
