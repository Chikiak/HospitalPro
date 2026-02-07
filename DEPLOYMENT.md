# HospitalPro Deployment Guide - HTTPS and Security Configuration

This guide explains how to configure HTTPS enforcement and Host Header security for production deployment.

## Overview

HospitalPro implements two critical security middlewares:

1. **HTTPSRedirectMiddleware**: Redirects all HTTP traffic to HTTPS (301 permanent redirect)
2. **TrustedHostMiddleware**: Prevents HTTP Host Header attacks by validating allowed hosts

## Environment Configuration

### Development Mode (Default)

In development mode, the system is configured for easy local testing:

```bash
ENVIRONMENT=development
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Behavior:**
- HTTPS redirect is **disabled** (allows HTTP for local development)
- Trusted Host middleware accepts localhost, 127.0.0.1, and wildcard (`*`) for testing
- Health check endpoints remain accessible

### Production Mode

For production deployment, you **MUST** configure the following environment variables:

```bash
# Required: Set environment to production
ENVIRONMENT=production

# Required: Specify allowed hostnames (comma-separated)
ALLOWED_HOSTS=api.hospital.com,hospital.com,www.hospital.com
```

**Behavior:**
- HTTPS redirect is **enabled** - all HTTP requests return 301 redirect to HTTPS
- Trusted Host middleware **only** accepts requests from specified hosts
- Missing or invalid Host headers return 400 Bad Request
- Application will **fail to start** if `ALLOWED_HOSTS` is not set in production mode

## Docker Deployment

### Step 1: Configure Environment Variables

Create or edit `.env` file in your project root:

```bash
# Copy the example file
cp .env.docker.example .env

# Edit with your production values
nano .env
```

Update the following in `.env`:

```bash
# Set to production
ENVIRONMENT=production

# Your actual domain(s)
ALLOWED_HOSTS=api.yourhospital.com,yourhospital.com

# Strong secret key (generate with: openssl rand -hex 32)
SECRET_KEY=<your-generated-secret-key>

# Other required settings
POSTGRES_PASSWORD=<strong-password>
STAFF_PASSWORD=<strong-password>
```

### Step 2: Configure HTTPS Termination

HospitalPro's HTTPS redirect works with any of these setups:

#### Option A: Reverse Proxy (Recommended)

Use Nginx or Traefik to terminate SSL/TLS:

**Nginx Example:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourhospital.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.yourhospital.com;
    
    # Let HospitalPro handle the redirect, or redirect here
    return 301 https://$host$request_uri;
}
```

#### Option B: Cloud Load Balancer

Configure your cloud provider's load balancer to:
1. Terminate SSL/TLS
2. Forward requests to your containers
3. Set the `Host` header correctly

### Step 3: Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

### Step 4: Verify Security Configuration

Test your deployment:

```bash
# Test HTTPS redirect (should return 301 in production)
curl -I http://api.yourhospital.com/health

# Test valid Host header (should return 200)
curl https://api.yourhospital.com/health

# Test invalid Host header (should return 400)
curl -H "Host: malicious.com" https://api.yourhospital.com/health
```

## Common Issues and Solutions

### Issue 1: Application Fails to Start in Production

**Error:** `ValueError: ALLOWED_HOSTS environment variable must be set in production mode`

**Solution:** Set the `ALLOWED_HOSTS` environment variable:
```bash
export ALLOWED_HOSTS=api.hospital.com,hospital.com
```

### Issue 2: 400 Bad Request After Deployment

**Error:** All requests return 400 Bad Request

**Cause:** The `Host` header in requests doesn't match `ALLOWED_HOSTS`

**Solution:** 
1. Check what Host header your reverse proxy is sending
2. Add that hostname to `ALLOWED_HOSTS`
3. For load balancers, ensure they preserve the original Host header

### Issue 3: Health Checks Failing

**Cause:** Load balancer health checks may use IP addresses instead of hostnames

**Solutions:**
- Add the load balancer's health check IP or hostname to `ALLOWED_HOSTS`
- Configure load balancer to send correct Host header
- Use hostname-based health checks instead of IP-based

## Security Best Practices

### 1. Always Use HTTPS in Production

```bash
ENVIRONMENT=production
```

This ensures all HTTP traffic is automatically redirected to HTTPS.

### 2. Specify Exact Hostnames

```bash
# Good - specific hostnames
ALLOWED_HOSTS=api.hospital.com,hospital.com

# Bad - too permissive
ALLOWED_HOSTS=*
```

### 3. Use Strong Secrets

```bash
# Generate a strong secret key
openssl rand -hex 32

# Set in environment
SECRET_KEY=<generated-key>
```

### 4. Keep Certificates Updated

- Use Let's Encrypt for free SSL certificates
- Set up automatic renewal
- Monitor certificate expiration

### 5. Review Security Headers

Consider adding these security headers in your reverse proxy:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
```

## Testing Your Configuration

### Local Testing with Production Settings

You can test production configuration locally:

```bash
# Set production mode
export ENVIRONMENT=production
export ALLOWED_HOSTS=localhost,127.0.0.1

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Automated Tests

The test suite includes comprehensive middleware tests:

```bash
cd backend
pytest tests/api/test_security_middleware.py -v
```

All 9 tests should pass:
- ✅ Health check accessibility
- ✅ Trusted Host configuration
- ✅ HTTPS redirect behavior
- ✅ Middleware ordering
- ✅ Production validation

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | Set to `production` to enable HTTPS redirect |
| `ALLOWED_HOSTS` | Yes (production) | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames |
| `SECRET_KEY` | Yes | - | JWT signing key (generate with `openssl rand -hex 32`) |
| `POSTGRES_*` | Yes | - | Database connection settings |
| `STAFF_PASSWORD` | Yes | - | Staff authentication password |

## Support

For issues or questions:
1. Check the [SECURITY_SUMMARY.md](../SECURITY_SUMMARY.md) for security features
2. Review test cases in `backend/tests/api/test_security_middleware.py`
3. Open an issue on GitHub

## Version History

- **v3.1 (2026-02-07)**: Initial HTTPS redirect and Trusted Host middleware implementation
  - HTTPSRedirectMiddleware for production
  - TrustedHostMiddleware with environment-based validation
  - Comprehensive test coverage (9 tests)
  - CodeQL scan: 0 alerts
