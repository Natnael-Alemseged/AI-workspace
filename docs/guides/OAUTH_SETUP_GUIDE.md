# OAuth Setup Guide

## Overview

This guide explains how to set up and use OAuth authentication (Google OAuth) in Armada Den.

## Prerequisites

1. **Google Cloud Console Setup**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Google+ API
   - Create OAuth 2.0 credentials (Web application)
   - Add authorized redirect URIs:
     - `http://localhost:8000/api/auth/google/callback` (development)
     - Your production callback URL

2. **Environment Variables**
   
   Add the following to your `.env` file:
   ```env
   SECRET_KEY=your_strong_random_secret_key_here
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
   FRONTEND_URL=http://localhost:3000
   ```

   **Important**: The `SECRET_KEY` is used for both JWT tokens and OAuth session management. Use a strong, random secret key in production.

## Session Middleware

The application uses `SessionMiddleware` from Starlette to manage OAuth state during the authorization flow. This middleware is configured in `app/main.py`:

```python
application.add_middleware(
    SessionMiddleware,
    secret_key=str(SECRET_KEY),
    max_age=3600,  # 1 hour session timeout
    same_site="lax",
    https_only=False  # Set to True in production with HTTPS
)
```

**Production Settings**:
- Set `https_only=True` when using HTTPS
- Use a strong, random `SECRET_KEY`
- Consider adjusting `max_age` based on your security requirements

## OAuth Flow

### 1. Initiate Authorization

```
GET /api/auth/google/authorize
```

This endpoint redirects the user to Google's authorization page.

### 2. Handle Callback

```
GET /api/auth/google/callback
```

After the user authorizes, Google redirects back to this endpoint with an authorization code. The endpoint:
- Exchanges the code for access tokens
- Creates or updates the user in the database
- Generates a JWT token
- Redirects to the frontend with the JWT token

### 3. Frontend Integration

The frontend should handle the callback redirect:

```
http://localhost:3000/auth/callback?token=<jwt_token>&type=google
```

Store the JWT token and use it for subsequent API requests:

```javascript
// Store token
localStorage.setItem('token', token);

// Use in API requests
fetch('/api/endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## API Endpoints

### Check OAuth Status

```
GET /api/auth/google/status
Authorization: Bearer <jwt_token>
```

Returns the OAuth connection status for the current user:

```json
{
  "connected": true,
  "email": "user@example.com",
  "expires_at": "2025-11-15T18:30:00",
  "is_expired": false
}
```

## Troubleshooting

### Error: SessionMiddleware must be installed

**Cause**: The SessionMiddleware is not configured in the application.

**Solution**: Ensure `SessionMiddleware` is added to the FastAPI app before other middleware (already fixed in `app/main.py`).

### Error: Invalid redirect_uri

**Cause**: The redirect URI in your request doesn't match the authorized URIs in Google Cloud Console.

**Solution**: 
1. Check your `GOOGLE_REDIRECT_URI` in `.env`
2. Verify it matches exactly in Google Cloud Console (including protocol, domain, port, and path)

### Error: Invalid client

**Cause**: Google client credentials are incorrect or missing.

**Solution**: 
1. Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. Ensure they match the credentials from Google Cloud Console

## Security Considerations

1. **HTTPS in Production**: Always use HTTPS in production and set `https_only=True` in SessionMiddleware
2. **Strong Secret Key**: Use a cryptographically strong random secret key
3. **CORS Configuration**: Ensure `ALLOWED_ORIGINS` only includes trusted domains
4. **Token Expiration**: JWT tokens expire after 60 minutes by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
5. **OAuth Token Storage**: OAuth tokens are stored securely in the database with user associations

## Database Schema

OAuth accounts are stored in the `oauth_account` table:

```python
class OAuthAccount(Base):
    id: UUID
    user_id: UUID  # Foreign key to users table
    oauth_name: str  # "google"
    access_token: str
    refresh_token: Optional[str]
    expires_at: Optional[datetime]
    account_id: str  # Google user ID
    account_email: str
```

## Testing

To test the OAuth flow:

1. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Navigate to:
   ```
   http://localhost:8000/api/auth/google/authorize
   ```

3. Complete the Google authorization

4. You should be redirected to your frontend with a JWT token

## References

- [Authlib Documentation](https://docs.authlib.org/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
