"""JWT authentication middleware"""

from typing import Optional
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime

from utils.config import config

# Security scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)  # Optional security (no error if missing)


class JWTValidator:
    """JWT token validation"""
    
    def __init__(self):
        self.secret_key = config.JWT_SECRET_KEY
        self.algorithm = config.JWT_ALGORITHM
    
    def decode_token(self, token: str) -> dict:
        """
        Decode and validate JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check if token has expired
            exp = payload.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                if datetime.utcnow() > exp_datetime:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_user_id(self, payload: dict) -> Optional[str]:
        """Extract user ID from token payload"""
        # The payload structure will depend on how Sanjay creates the JWT
        # Common fields: user_id, sub (subject), email
        return payload.get("user_id") or payload.get("sub")
    
    def get_user_email(self, payload: dict) -> Optional[str]:
        """Extract user email from token payload"""
        return payload.get("email")


# Create validator instance
jwt_validator = JWTValidator()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    FastAPI dependency to validate JWT token and get current user
    
    Usage:
        @app.get("/protected-endpoint")
        def protected_route(user: dict = Depends(get_current_user)):
            user_id = user.get("user_id")
            return {"message": f"Hello user {user_id}"}
    """
    token = credentials.credentials
    payload = jwt_validator.decode_token(token)
    
    # Add user_id to payload if not present
    if "user_id" not in payload:
        user_id = jwt_validator.get_user_id(payload)
        if user_id:
            payload["user_id"] = user_id
    
    return payload


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security)
) -> Optional[dict]:
    """
    Optional authentication - returns user if token is valid, None otherwise
    
    Usage:
        @app.get("/optional-auth-endpoint")
        def optional_auth_route(user: Optional[dict] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.get('email')}"}
            return {"message": "Hello anonymous user"}
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt_validator.decode_token(token)
        
        # Add user_id to payload if not present
        if "user_id" not in payload:
            user_id = jwt_validator.get_user_id(payload)
            if user_id:
                payload["user_id"] = user_id
        
        return payload
    except HTTPException:
        return None


# Helper function to extract user_id from token payload
def extract_user_id(user: dict) -> str:
    """
    Extract user ID from decoded JWT payload
    
    Args:
        user: Decoded JWT payload
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If user_id not found in payload
    """
    user_id = user.get("user_id") or user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id

