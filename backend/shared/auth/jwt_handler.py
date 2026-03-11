from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os

class JWTHandler:

    def __init__(self, public_key_path: str, private_key_path: str=None, algorithm: str='RS256'):
        self.algorithm = algorithm
        self.public_key = self._load_key(public_key_path)
        self.private_key = None
        if private_key_path and os.path.exists(private_key_path):
            self.private_key = self._load_key(private_key_path)

    def _load_key(self, path: str) -> bytes:
        if not os.path.exists(path):
            raise FileNotFoundError(f'Key not found at {path}')
        with open(path, 'rb') as f:
            return f.read()

    def create_access_token(self, data: Dict[str, Any], expires_minutes: int=120) -> str:
        if not self.private_key:
            raise ValueError('Private key not loaded — cannot create tokens')
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        to_encode.update({'exp': expire, 'type': 'access', 'iat': datetime.utcnow()})
        return jwt.encode(to_encode, self.private_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any], expires_days: int=7) -> str:
        if not self.private_key:
            raise ValueError('Private key not loaded — cannot create tokens')
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=expires_days)
        to_encode.update({'exp': expire, 'type': 'refresh', 'iat': datetime.utcnow()})
        return jwt.encode(to_encode, self.private_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            print(f'JWT decode error: {e}')
            return None

    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        payload = self.decode_token(token)
        if payload and payload.get('type') == 'access':
            return payload
        return None

    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        payload = self.decode_token(token)
        if payload and payload.get('type') == 'refresh':
            return payload
        return None