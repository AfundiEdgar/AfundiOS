"""
Vector Store with optional encryption

Provides encrypted vector storage using Chroma backend.
Supports selective encryption of texts and metadata fields.
"""

from typing import List, Tuple, Dict, Any, Optional
import logging
from chromadb import PersistentClient
from .encryption import EncryptionManager, SelectiveEncryption, is_encryption_enabled

logger = logging.getLogger(__name__)


class EncryptedVectorStore:
    """Vector store with optional encryption layer."""

    def __init__(
        self,
        path: str,
        encryption_manager: Optional[EncryptionManager] = None,
        encrypt_texts: bool = False,
        encrypt_metadata_fields: Optional[List[str]] = None,
    ):
        """
        Initialize encrypted vector store.

        Args:
            path: Path to vector store
            encryption_manager: EncryptionManager instance (created if None and encryption enabled)
            encrypt_texts: Whether to encrypt document texts
            encrypt_metadata_fields: List of metadata field names to encrypt (e.g., ["source", "author"])
        """
        self.client = PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("afundios_docs")

        self.encryption_enabled = is_encryption_enabled()

        if self.encryption_enabled:
            if encryption_manager is None:
                from .encryption import get_encryption_manager
                encryption_manager = get_encryption_manager()

            self.encryptor = encryption_manager
            self.selective_encryption = SelectiveEncryption(encryption_manager)
            self.encrypt_texts = encrypt_texts
            self.encrypt_metadata_fields = encrypt_metadata_fields or []

            logger.info(
                f"EncryptedVectorStore initialized with encryption "
                f"(texts={encrypt_texts}, metadata_fields={self.encrypt_metadata_fields})"
            )
        else:
            self.encryptor = None
            self.selective_encryption = None
            self.encrypt_texts = False
            self.encrypt_metadata_fields = []

    def add(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: List[dict],
        ids: List[str],
    ) -> None:
        """
        Add documents with optional encryption.

        Encrypts texts and metadata fields before storing.
        """
        if not self.encryption_enabled:
            self.collection.add(
                embeddings=embeddings, documents=texts, metadatas=metadatas, ids=ids
            )
            return

        # Encrypt texts if enabled
        encrypted_texts = texts
        if self.encrypt_texts:
            encrypted_texts = [self.encryptor.encrypt(text) for text in texts]

        # Encrypt metadata fields
        encrypted_metadatas = metadatas
        if self.encrypt_metadata_fields:
            encrypted_metadatas = [
                self.selective_encryption.encrypt_fields(meta, self.encrypt_metadata_fields)
                for meta in metadatas
            ]

        # Mark encrypted fields for decryption on retrieval
        for meta in encrypted_metadatas:
            if self.encrypt_texts:
                meta["__encrypted_text"] = True
            if self.encrypt_metadata_fields:
                meta["__encrypted_fields"] = self.encrypt_metadata_fields

        self.collection.add(
            embeddings=embeddings,
            documents=encrypted_texts,
            metadatas=encrypted_metadatas,
            ids=ids,
        )

    def search(self, query_embedding: List[float], k: int = 5) -> List[Tuple[str, str, dict]]:
        """
        Search and decrypt results.

        Retrieves results from collection and decrypts texts and metadata fields.
        """
        res = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        ids = res.get("ids", [[]])[0]

        if not self.encryption_enabled:
            return list(zip(ids, docs, metas))

        # Decrypt texts and metadata
        decrypted_results = []
        for doc_id, doc_text, metadata in zip(ids, docs, metas):
            # Decrypt text if needed
            if metadata.get("__encrypted_text"):
                try:
                    doc_text = self.encryptor.decrypt(doc_text)
                except Exception as e:
                    logger.error(f"Failed to decrypt text for {doc_id}: {e}")

            # Decrypt metadata fields if needed
            encrypted_fields = metadata.pop("__encrypted_fields", [])
            if encrypted_fields:
                try:
                    metadata = self.selective_encryption.decrypt_fields(metadata, encrypted_fields)
                except Exception as e:
                    logger.error(f"Failed to decrypt metadata for {doc_id}: {e}")

            # Remove decryption markers
            metadata.pop("__encrypted_text", None)

            decrypted_results.append((doc_id, doc_text, metadata))

        return decrypted_results

    def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        self.collection.delete(ids=ids)

    def update(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: List[dict],
        ids: List[str],
    ) -> None:
        """
        Update documents with optional encryption.

        Encrypts new values before storing.
        """
        if not self.encryption_enabled:
            self.collection.update(
                embeddings=embeddings, documents=texts, metadatas=metadatas, ids=ids
            )
            return

        # Encrypt texts if enabled
        encrypted_texts = texts
        if self.encrypt_texts:
            encrypted_texts = [self.encryptor.encrypt(text) for text in texts]

        # Encrypt metadata fields
        encrypted_metadatas = metadatas
        if self.encrypt_metadata_fields:
            encrypted_metadatas = [
                self.selective_encryption.encrypt_fields(meta, self.encrypt_metadata_fields)
                for meta in metadatas
            ]

        # Mark encrypted fields
        for meta in encrypted_metadatas:
            if self.encrypt_texts:
                meta["__encrypted_text"] = True
            if self.encrypt_metadata_fields:
                meta["__encrypted_fields"] = self.encrypt_metadata_fields

        self.collection.update(
            embeddings=embeddings,
            documents=encrypted_texts,
            metadatas=encrypted_metadatas,
            ids=ids,
        )

    def list_all(self) -> List[dict]:
        """
        Return all documents stored in the collection (decrypted when needed).

        Returns a list of dicts: {"id": id, "text": text, "metadata": metadata}
        """
        try:
            res = self.collection.get()
        except Exception:
            # Some chroma versions require empty args
            res = self.collection.get(ids=None)

        ids = res.get("ids", [[]])[0] if isinstance(res.get("ids"), list) and res.get("ids") and isinstance(res.get("ids")[0], list) else res.get("ids", [])
        docs = res.get("documents", [[]])[0] if isinstance(res.get("documents", list)) and res.get("documents") and isinstance(res.get("documents")[0], list) else res.get("documents", [])
        metas = res.get("metadatas", [[]])[0] if isinstance(res.get("metadatas", list)) and res.get("metadatas") and isinstance(res.get("metadatas")[0], list) else res.get("metadatas", [])

        results = []
        for _id, doc_text, metadata in zip(ids, docs, metas):
            if metadata is None:
                metadata = {}

            # Decrypt if markers present
            if self.encryption_enabled:
                if metadata.get("__encrypted_text"):
                    try:
                        doc_text = self.encryptor.decrypt(doc_text)
                    except Exception:
                        logger.exception("Failed to decrypt doc text for %s", _id)

                encrypted_fields = metadata.get("__encrypted_fields", [])
                if encrypted_fields:
                    try:
                        metadata = self.selective_encryption.decrypt_fields(metadata, encrypted_fields)
                    except Exception:
                        logger.exception("Failed to decrypt metadata for %s", _id)

                # cleanup markers
                metadata.pop("__encrypted_text", None)
                metadata.pop("__encrypted_fields", None)

            results.append({"id": _id, "text": doc_text, "metadata": metadata})

        return results

    def compact(
        self,
        strategy: str = "deduplicate_exact",
        keep_recent_days: int = 365,
        dry_run: bool = True,
    ) -> dict:
        """
        Compact / prune the vector store.

        Strategies supported:
        - "deduplicate_exact": remove exact duplicate documents (keeping the most recent by metadata.created_at if present)
        - "age_based": remove documents older than `keep_recent_days` based on metadata.created_at

        If `dry_run` is True, the method only returns a summary of what would be deleted.
        Returns a summary dict with counts and deleted ids (or candidate ids when dry_run=True).
        """
        from datetime import datetime, timedelta

        all_docs = self.list_all()
        to_delete = set()
        kept = set()

        if strategy == "deduplicate_exact":
            # group by exact plaintext
            groups: dict = {}
            for item in all_docs:
                text = (item.get("text") or "").strip()
                groups.setdefault(text, []).append(item)

            for text, items in groups.items():
                if len(items) <= 1:
                    continue

                # pick one to keep: prefer newest by created_at if available
                def created_at_val(it):
                    meta = it.get("metadata") or {}
                    ts = meta.get("created_at") or meta.get("timestamp") or meta.get("created")
                    if not ts:
                        return 0
                    try:
                        return datetime.fromisoformat(ts).timestamp()
                    except Exception:
                        try:
                            return float(ts)
                        except Exception:
                            return 0

                items_sorted = sorted(items, key=created_at_val, reverse=True)
                keeper = items_sorted[0]
                kept.add(keeper["id"])
                for it in items_sorted[1:]:
                    to_delete.add(it["id"])

        elif strategy == "age_based":
            cutoff = datetime.utcnow() - timedelta(days=keep_recent_days)
            for item in all_docs:
                meta = item.get("metadata") or {}
                ts = meta.get("created_at") or meta.get("timestamp") or meta.get("created")
                if not ts:
                    continue
                try:
                    d = datetime.fromisoformat(ts)
                except Exception:
                    try:
                        d = datetime.utcfromtimestamp(float(ts))
                    except Exception:
                        continue

                if d < cutoff and not meta.get("pinned"):
                    to_delete.add(item["id"]) 

        else:
            raise ValueError(f"Unknown compaction strategy: {strategy}")

        summary = {
            "strategy": strategy,
            "total_documents": len(all_docs),
            "candidates_to_delete": list(to_delete),
            "kept": list(kept),
            "dry_run": bool(dry_run),
        }

        if not dry_run and to_delete:
            try:
                ids_to_delete = list(to_delete)
                self.collection.delete(ids=ids_to_delete)
                summary["deleted_count"] = len(ids_to_delete)
                summary["deleted_ids"] = ids_to_delete
            except Exception as e:
                logger.exception("Failed to delete items during compaction: %s", e)
                summary["error"] = str(e)

        return summary


# For backward compatibility, create alias
class VectorStore(EncryptedVectorStore):
    """Backward-compatible VectorStore that uses EncryptedVectorStore."""
    def __init__(self, path: str):
        super().__init__(
            path=path,
            encrypt_texts=False,
            encrypt_metadata_fields=None,
        )
