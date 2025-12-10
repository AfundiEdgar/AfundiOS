"""
Encryption utilities for secure vector storage.

Provides encryption/decryption for sensitive data using AES-256-GCM.
Supports both at-rest encryption (for stored vectors) and in-transit encryption.
"""

import os
import json
import base64
import logging
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption/decryption using AES-256-GCM."""

    def __init__(self, encryption_key: Optional[str] = None, derive_from_password: bool = False):
        """
        Initialize encryption manager.

        Args:
            encryption_key: 32-byte hex-encoded key or password (if derive_from_password=True)
            derive_from_password: If True, derive key from password using PBKDF2
        """
        self.encryption_key = self._get_or_create_key(encryption_key, derive_from_password)

    def _get_or_create_key(self, provided_key: Optional[str], derive: bool) -> bytes:
        """Get encryption key from provided value or create/load from file."""
        if provided_key:
            if derive:
                # Derive from password using PBKDF2
                return self._derive_key_from_password(provided_key)
            else:
                # Parse as hex-encoded 32-byte key
                try:
                    return bytes.fromhex(provided_key)
                except ValueError:
                    raise ValueError("Encryption key must be 32-byte hex-encoded or set derive_from_password=True")

        # Try to load from file
        key_file = ".encryption_key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()

        # Generate new key and save
        key = os.urandom(32)  # 256-bit key
        with open(key_file, "wb") as f:
            f.write(key)
        logger.info(f"Generated new encryption key and saved to {key_file}")
        return key

    @staticmethod
    def _derive_key_from_password(password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive a 32-byte key from a password using PBKDF2."""
        if salt is None:
            # Fixed salt for consistent key derivation
            salt = b"afundios_vector_store"

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return kdf.derive(password.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-GCM.

        Returns base64-encoded string: base64(nonce + ciphertext + tag)
        """
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        cipher = AESGCM(self.encryption_key)
        ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)

        # Combine nonce + ciphertext and encode as base64
        encrypted = nonce + ciphertext
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt base64-encoded AES-256-GCM ciphertext.

        Expects: base64(nonce + ciphertext + tag)
        """
        encrypted = base64.b64decode(encrypted_text)

        # Extract nonce (first 12 bytes) and ciphertext
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]

        cipher = AESGCM(self.encryption_key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)

        return plaintext.decode()

    def encrypt_metadata(self, metadata: Dict[str, Any]) -> str:
        """Encrypt metadata dict by serializing to JSON first."""
        json_str = json.dumps(metadata)
        return self.encrypt(json_str)

    def decrypt_metadata(self, encrypted_metadata: str) -> Dict[str, Any]:
        """Decrypt metadata and deserialize from JSON."""
        json_str = self.decrypt(encrypted_metadata)
        return json.loads(json_str)


class SelectiveEncryption:
    """Applies selective encryption to specific fields (e.g., sensitive metadata)."""

    def __init__(self, encryption_manager: EncryptionManager):
        self.encryptor = encryption_manager

    def encrypt_fields(self, data: Dict[str, Any], fields_to_encrypt: list) -> Dict[str, Any]:
        """Encrypt specified fields in a dictionary."""
        encrypted_data = data.copy()
        for field in fields_to_encrypt:
            if field in encrypted_data:
                value = encrypted_data[field]
                if isinstance(value, (str, int, float, bool)):
                    encrypted_data[field] = self.encryptor.encrypt(str(value))
                else:
                    encrypted_data[field] = self.encryptor.encrypt(json.dumps(value))
        return encrypted_data

    def decrypt_fields(self, data: Dict[str, Any], fields_to_decrypt: list) -> Dict[str, Any]:
        """Decrypt specified fields in a dictionary."""
        decrypted_data = data.copy()
        for field in fields_to_decrypt:
            if field in decrypted_data:
                try:
                    decrypted_data[field] = self.decrypt_value(decrypted_data[field])
                except Exception as e:
                    logger.warning(f"Failed to decrypt field {field}: {e}")
        return decrypted_data

    def decrypt_value(self, encrypted_value: str) -> Any:
        """Attempt to decrypt and deserialize a value."""
        decrypted = self.encryptor.decrypt(encrypted_value)
        # Try to parse as JSON
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or initialize the global encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        from config import settings

        if settings.encryption_enabled:
            _encryption_manager = EncryptionManager(
                encryption_key=settings.encryption_key,
                derive_from_password=settings.encryption_derive_from_password,
            )
            logger.info("Encryption enabled for vector store")
        else:
            logger.info("Encryption disabled")

    return _encryption_manager


def is_encryption_enabled() -> bool:
    """Check if encryption is enabled."""
    from config import settings
    return settings.encryption_enabled
