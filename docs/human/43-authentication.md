# Authentication & Authorization

Complete guide to authentication, user management, and role-based access control in the Network Device Monitor.

## Overview

As of version 0.2.0, the Network Device Monitor includes a comprehensive authentication and authorization system with:

- **JWT Token Authentication** - Secure token-based authentication
- **User Management** - Multi-user support with registration and login
- **Role-Based Access Control (RBAC)** - Admin, Operator, and Viewer roles
- **Password Security** - Bcrypt hashing with password strength validation
- **Optional Authentication** - Can be enabled/disabled via configuration

## Quick Start

### Enable Authentication

Authentication is **disabled by default** for backward compatibility. To enable it:

```bash
# In backend/.env
REQUIRE_AUTH=true
```

### Create First Admin User

```bash
# Register admin user via API
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePass123",
    "full_name": "Administrator",
    "role": "admin"
  }'
```

### Login and Get Token

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Administrator",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  },
  "token": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### Use Token for API Requests

```bash
# Use token in Authorization header
curl http://localhost:8000/api/devices \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## User Roles

The system supports three roles with different permissions:

### Viewer (Default)

- **Read-only access** to all network data
- View devices, metrics, and topology
- Cannot modify configurations
- Cannot manage users

**Use case**: Network monitoring dashboards, read-only users

### Operator

- All viewer permissions
- Trigger network discovery scans
- Acknowledge alerts (future feature)
- Manage device tags and notes (future feature)
- Cannot manage users or system settings

**Use case**: Network operations team, day-to-day monitoring

### Admin

- All operator permissions
- User management (create, update, delete users)
- System configuration
- Access control management
- Full API access

**Use case**: System administrators, security team

## User Management

### Register New User

**Endpoint**: `POST /api/auth/register`

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe",
    "role": "viewer",
    "is_active": true
  }'
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Maximum 128 characters

**Username Requirements**:
- 3-50 characters
- Alphanumeric, dashes, and underscores only
- Must be unique

### Login

**Endpoint**: `POST /api/auth/login`

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123"
  }'
```

Returns:
- User information
- JWT access token
- Token expiration time

### Get Current User Info

**Endpoint**: `GET /api/auth/me`

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List All Users (Admin Only)

**Endpoint**: `GET /api/auth/users`

```bash
curl http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

Query parameters:
- `limit` - Maximum users to return (default: 100)
- `offset` - Pagination offset (default: 0)

### Get User by ID (Admin Only)

**Endpoint**: `GET /api/auth/users/{user_id}`

```bash
curl http://localhost:8000/api/auth/users/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Update User (Admin Only)

**Endpoint**: `PATCH /api/auth/users/{user_id}`

```bash
curl -X PATCH http://localhost:8000/api/auth/users/USER_ID \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "operator",
    "is_active": true,
    "full_name": "John Updated Doe"
  }'
```

Updatable fields:
- `email` - Email address
- `full_name` - Full name
- `role` - User role
- `is_active` - Account status
- `password` - New password

### Delete User (Admin Only)

**Endpoint**: `DELETE /api/auth/users/{user_id}`

```bash
curl -X DELETE http://localhost:8000/api/auth/users/USER_ID \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Note**: Admins cannot delete their own account.

## Configuration

### Environment Variables

Add to `backend/.env`:

```bash
# Authentication Settings
REQUIRE_AUTH=true                    # Enable authentication (default: false)
JWT_SECRET_KEY=your-secret-key-here  # JWT signing key (auto-generated)
JWT_ALGORITHM=HS256                  # JWT algorithm (default: HS256)
JWT_EXPIRATION_MINUTES=60            # Token expiration (default: 60)
```

### JWT Secret Key

**Important**: Generate a secure secret key for production:

```bash
# Generate a secure random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to `.env`:
```bash
JWT_SECRET_KEY=your-generated-key-here
```

**Never commit the secret key to version control!**

### Token Expiration

Tokens expire after the configured time. Users must re-authenticate after expiration.

Default: 60 minutes (1 hour)

```bash
# Set to 24 hours
JWT_EXPIRATION_MINUTES=1440

# Set to 7 days
JWT_EXPIRATION_MINUTES=10080
```

## Security Best Practices

### 1. Secret Key Management

```bash
# Use strong, random keys
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Never hardcode keys
# Never commit keys to git
# Rotate keys periodically
```

### 2. Password Policy

Passwords must meet minimum requirements:
- 8+ characters
- Mixed case
- Include numbers

Consider additional requirements:
- Special characters
- Password history
- Expiration policies

### 3. HTTPS in Production

Always use HTTPS in production to protect tokens in transit:

```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Authorization $http_authorization;
    }
}
```

### 4. Token Storage

**Frontend applications should**:
- Store tokens securely (e.g., httpOnly cookies)
- Never store in localStorage if XSS risk exists
- Clear tokens on logout
- Handle token expiration gracefully

### 5. Rate Limiting (Future)

Consider implementing rate limiting on authentication endpoints to prevent brute force attacks.

## Python Client Example

```python
import httpx

# Base URL
BASE_URL = "http://localhost:8000/api"

class NetworkMonitorClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        self.client = httpx.Client()

    def login(self, username: str, password: str):
        """Login and store token."""
        response = self.client.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["token"]["access_token"]
        return data["user"]

    def get_headers(self):
        """Get headers with authentication token."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def list_devices(self):
        """Get all devices."""
        response = self.client.get(
            f"{self.base_url}/devices",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_current_user(self):
        """Get current user info."""
        response = self.client.get(
            f"{self.base_url}/auth/me",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = NetworkMonitorClient()
user = client.login("admin", "SecurePass123")
print(f"Logged in as: {user['username']} ({user['role']})")

devices = client.list_devices()
print(f"Found {len(devices)} devices")
```

## JavaScript/TypeScript Example

```typescript
interface LoginResponse {
  user: User;
  token: Token;
}

interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

class NetworkMonitorClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = "http://localhost:8000/api") {
    this.baseUrl = baseUrl;
  }

  async login(username: string, password: string): Promise<User> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

    const data: LoginResponse = await response.json();
    this.token = data.token.access_token;
    return data.user;
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async getDevices(): Promise<Device[]> {
    const response = await fetch(`${this.baseUrl}/devices`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch devices");
    }

    return response.json();
  }
}

// Usage
const client = new NetworkMonitorClient();
const user = await client.login("admin", "SecurePass123");
console.log(`Logged in as: ${user.username} (${user.role})`);

const devices = await client.getDevices();
console.log(`Found ${devices.length} devices`);
```

## Troubleshooting

### 401 Unauthorized

**Problem**: Getting 401 errors when calling API

**Solutions**:
1. Check if `REQUIRE_AUTH=true` is set
2. Verify token is included in Authorization header
3. Check token hasn't expired
4. Ensure token format is `Bearer <token>`

### 403 Forbidden

**Problem**: User doesn't have permission

**Solutions**:
1. Check user role matches required permission
2. Verify user account is active
3. For admin operations, ensure user has admin role

### Cannot Register First User

**Problem**: Need admin to create users, but no users exist

**Solution**: First user registration is always allowed. Register admin user first:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@example.com","password":"SecurePass123","role":"admin"}'
```

### Token Expired

**Problem**: Token expired after 1 hour

**Solutions**:
1. Re-authenticate to get new token
2. Implement automatic token refresh in client
3. Increase `JWT_EXPIRATION_MINUTES` if appropriate

### Forgot Admin Password

**Problem**: Locked out of admin account

**Solution**: Direct database access required:

```python
# In Python shell
from app.utils.auth import hash_password
from app.storage.sqlite import init_sqlite

# Reset password
new_password_hash = hash_password("NewSecurePass123")

# Update database manually
# (Requires direct SQLite access)
```

## Migration from v0.1.0

If upgrading from v0.1.0 without authentication:

1. **Database Migration**: Users table is automatically created
2. **Backward Compatibility**: Authentication is disabled by default
3. **Gradual Rollout**: Enable auth when ready with `REQUIRE_AUTH=true`

**Migration steps**:

```bash
# 1. Update code to v0.2.0
git pull origin main

# 2. Install new dependencies
pip install -r backend/requirements/base.txt

# 3. Start server (creates users table)
make dev

# 4. Register admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@example.com","password":"SecurePass123","role":"admin"}'

# 5. Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecurePass123"}'

# 6. Enable authentication
echo "REQUIRE_AUTH=true" >> backend/.env

# 7. Restart server
make dev
```

## Related Documentation

- [Security Best Practices](42-security.md) - General security guidelines
- [API Reference](40-api-reference.md) - Complete API documentation
- [Configuration Guide](03-configuration.md) - Environment configuration
- [Deployment Guide](30-deployment.md) - Production deployment

## Support

For authentication issues:
1. Check this documentation
2. Review [Troubleshooting Guide](31-troubleshooting.md)
3. Open an issue on GitHub
4. Join community discussions
