# Security Policy - Nuvemhost

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Active          |

---

## Reporting a Vulnerability

**Please do NOT open public issues for security vulnerabilities.**

Report security issues privately via:
- Email: security@diogomilhomem.com
- GitHub Security Advisories: Use "Report a vulnerability" tab

We aim to respond within 48 hours and provide a fix timeline.

---

## Security Measures Implemented

### Authentication & Authorization
- ✅ **Password hashing**: bcrypt with salt (cost factor 12)
- ✅ **Session management**: Flask sessions with secure cookies
- ✅ **Login required decorator**: Protects all user routes
- ✅ **User ownership validation**: All project operations verify `user_id`
- ✅ **CSRF protection**: SameSite=Lax cookies, POST for state changes

### Input Validation & Sanitization
- ✅ **File upload validation**: 
  - Extension whitelist (`.zip` only for uploads)
  - File size limit (10MB via `MAX_CONTENT_LENGTH`)
  - Secure filename handling (`werkzeug.utils.secure_filename`)
- ✅ **ZIP extraction safety**:
  - Path traversal prevention (`..` and absolute paths blocked)
  - Extension validation for extracted files
  - Temporary ZIP removal after extraction
- ✅ **File serving validation**:
  - Extension whitelist for public access
  - Path traversal prevention (`os.path.abspath` check)
  - MIME type detection for proper serving
- ✅ **SQL injection prevention**: Parameterized queries only
- ✅ **XSS prevention**: Jinja2 auto-escaping, CSP-ready

### Access Control
- ✅ **Project isolation**: Users only access own projects
- ✅ **Public project access**: Read-only via unique UUID URLs
- ✅ **Status enforcement**: Paused projects return custom page, not content
- ✅ **Rate limiting ready**: Flask-Limiter compatible

### Data Protection
- ✅ **Environment variables**: Secrets in `.env` (gitignored)
- ✅ **Database credentials**: Not in code
- ✅ **Error handling**: Generic messages to users, detailed in logs
- ✅ **Logging**: No sensitive data in logs (passwords, tokens)

### Infrastructure
- ✅ **HTTPS ready**: Works behind reverse proxy (nginx/Traefik)
- ✅ **Security headers**: Can add via Flask-Talisman
- ✅ **File permissions**: Uploads outside web root

---

## Security Checklist for Deployment

### Required
- [ ] Set strong `SECRET_KEY` (32+ random bytes)
- [ ] Use HTTPS in production (TLS 1.2+)
- [ ] Configure MySQL with strong passwords
- [ ] Restrict MySQL to localhost or private network
- [ ] Set `DEBUG=False` in production
- [ ] Use dedicated database user with minimal privileges
- [ ] Configure firewall (allow only 80/443, SSH)
- [ ] Set up automated backups

### Recommended
- [ ] Add Flask-Talisman for security headers (HSTS, CSP, etc.)
- [ ] Implement rate limiting (Flask-Limiter)
- [ ] Add WAF (ModSecurity/CrowdSec)
- [ ] Enable MySQL SSL connections
- [ ] Set up log monitoring/alerting
- [ ] Regular dependency updates (`pip-audit`)
- [ ] Use container/VM isolation

### Optional
- [ ] Two-factor authentication (2FA)
- [ ] API keys for programmatic access
- [ ] Audit logging for sensitive operations
- [ ] Penetration testing

---

## Known Limitations

1. **No rate limiting** on login/register (add Flask-Limiter)
2. **No CSP headers** by default (add Flask-Talisman)
3. **Session fixation**: Regenerate session ID on login (implement if needed)
4. **Password policy**: Minimum 6 chars only (strengthen if needed)
5. **No account lockout** after failed attempts

---

## Dependency Security

Run regular audits:

```bash
# Check for vulnerabilities
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt
```

Current dependencies (check `requirements.txt`):
- Flask
- mysql-connector-python
- bcrypt
- python-dotenv
- werkzeug

---

## Secure Development Practices

### Code Review Checklist
- [ ] All SQL uses parameterized queries
- [ ] No `eval()`, `exec()`, or dynamic code
- [ ] File paths validated with `os.path.abspath`
- [ ] User input never directly in HTML/JS/SQL
- [ ] Error messages don't leak stack traces
- [ ] Secrets never in code or logs

### Testing
```bash
# Security-focused tests
# - SQL injection attempts
# - Path traversal attempts
# - XSS payloads in inputs
# - Authentication bypass
# - Authorization bypass
# - File upload bypasses
```

---

## Incident Response

1. **Contain**: Disable affected feature/route
2. **Assess**: Determine scope and impact
3. **Fix**: Apply patch, deploy
4. **Rotate**: Compromised secrets (DB, SESSION keys)
5. **Notify**: Affected users if data exposed
6. **Document**: Lessons learned, update policies

---

## Contact

Security issues: security@diogomilhomem.com

General issues: GitHub Issues tab