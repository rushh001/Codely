import jwt
import time
from typing import Optional, Dict, Any

SECRET_KEY = "cluely-super-secure-key"
ALGORITHM = "HS256"

class AuthenticationService:
    """
    Handles enterprise SSO, JWT generation, and token validation.
    """
    def __init__(self, token_ttl_seconds: int = 3600):
        self.token_ttl = token_ttl_seconds
        self.revoked_tokens = set()

    def generate_jwt_token(self, user_id: str, role: str = "engineer") -> str:
        """
        Generates a signed JWT bearer token with expiration and roles.
        """
        payload = {
            "sub": user_id,
            "role": role,
            "exp": time.time() + self.token_ttl,
            "iat": time.time()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def verify_auth_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validates JWT bearer token, checks revocation list, and extracts claims.
        """
        if token in self.revoked_tokens:
            return None
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return decoded
        except Exception:
            return None

    def revoke_token(self, token: str) -> bool:
        """
        Blacklists an active token immediately across all sessions.
        """
        self.revoked_tokens.add(token)
        return True
