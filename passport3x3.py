"""Content seal for a reproducible synthetic evaluation.

The digest is an integrity check over canonical JSON payload data and the
source-file hashes. It does not certify external truth, peer review, or
scientific validity. Synthetic results never meet the headline rule.
"""
import hashlib
import json
import pathlib


def sha_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def code_hashes(code_files):
    """Return SHA-256 hashes keyed by package-relative file name."""
    return {pathlib.Path(path).name: sha_file(path)
            for path in sorted(code_files)}


def seal(payload, code_files):
    """Hash canonical JSON plus the ordered source-file digests."""
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False, allow_nan=False)
    h = hashlib.sha256(canon.encode("utf-8"))
    for path in sorted(code_files):
        h.update(sha_file(path).encode("ascii"))
    return h.hexdigest()


def headline_allowed(data_kind, lower_bound):
    return data_kind == "measured" and lower_bound is not None and lower_bound > 0
