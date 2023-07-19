import hashlib


DEFAULT_CURRENCY = 1


def _compute_numeric_hash(app_id: int, market_hash_name: str) -> int:
    hash_object = hashlib.sha256(f"{app_id}{market_hash_name}".encode())
    numeric_hash = int(hash_object.hexdigest(), 16)
    return numeric_hash


def compute_partition(app_id: int, market_hash_name: str) -> int:
    return _compute_numeric_hash(app_id, market_hash_name) % 100
