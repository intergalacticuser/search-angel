"""Near-duplicate detection using SimHash."""

from __future__ import annotations

import hashlib
import logging
import re

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\w+", text.lower())


def compute_simhash(text: str, hash_bits: int = 64) -> int:
    """Compute a SimHash fingerprint for text content.

    SimHash produces a 64-bit fingerprint where similar texts produce
    similar hashes (small Hamming distance).
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0

    # Use 3-gram shingles for better similarity detection
    shingles: list[str] = []
    for i in range(len(tokens) - 2):
        shingles.append(" ".join(tokens[i : i + 3]))
    if not shingles:
        shingles = tokens

    # Initialize vector of hash_bits dimensions
    v = [0] * hash_bits

    for shingle in shingles:
        # Hash each shingle to a fixed-width integer
        h = int(hashlib.md5(shingle.encode()).hexdigest(), 16) % (2**hash_bits)
        for i in range(hash_bits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    # Build fingerprint: bit i is 1 if v[i] > 0
    fingerprint = 0
    for i in range(hash_bits):
        if v[i] > 0:
            fingerprint |= 1 << i

    return fingerprint


def hamming_distance(hash_a: int, hash_b: int) -> int:
    """Compute Hamming distance between two SimHash fingerprints."""
    xor = hash_a ^ hash_b
    return bin(xor).count("1")


def is_near_duplicate(hash_a: int, hash_b: int, threshold: int = 5) -> bool:
    """Check if two documents are near-duplicates.

    Default threshold of 5 bits (out of 64) catches ~90% of near-duplicates
    while maintaining low false positive rate.
    """
    return hamming_distance(hash_a, hash_b) <= threshold


class Deduplicator:
    """Collapses near-duplicate documents in search results."""

    def __init__(self, threshold: int = 5) -> None:
        self.threshold = threshold

    def collapse(
        self, documents: list, *, keep: str = "highest_score"
    ) -> list:
        """Remove near-duplicates from a ranked result list.

        Keeps the highest-scoring document from each duplicate group.
        Works with any list of objects that have `doc_id` and `content` attributes.
        """
        if not documents:
            return []

        # Compute fingerprints
        fingerprints: list[tuple[int, int]] = []  # (index, simhash)
        for i, doc in enumerate(documents):
            content = getattr(doc, "content", "")
            fprint = compute_simhash(content)
            fingerprints.append((i, fprint))

        # Group by near-duplicate clusters
        seen: set[int] = set()
        result: list = []

        for i, (idx_a, hash_a) in enumerate(fingerprints):
            if idx_a in seen:
                continue

            # This is a new canonical document
            result.append(documents[idx_a])
            seen.add(idx_a)

            # Find all near-duplicates of this document
            for idx_b, hash_b in fingerprints[i + 1 :]:
                if idx_b not in seen and is_near_duplicate(hash_a, hash_b, self.threshold):
                    seen.add(idx_b)
                    logger.debug(
                        "Duplicate detected: %s is near-duplicate of %s (distance=%d)",
                        getattr(documents[idx_b], "doc_id", idx_b),
                        getattr(documents[idx_a], "doc_id", idx_a),
                        hamming_distance(hash_a, hash_b),
                    )

        return result
