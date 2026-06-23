"""Gateway-side rules and audit-trail policy.

Illustrative figures — verify against the current Finance Act / NBR before any
real use. The gateway holds no tax rules of its own; it surfaces what the
upstream services compute. What lives here is the access-log policy: every
call through the gateway is logged with the requesting agency and timestamp.
"""
from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Iterable, Optional

from .models import AccessLogEntry

# Bounded in-memory audit trail. In production this would ship to an append-
# only audit store; for the reference we keep the last N entries in memory.
_LOG_CAPACITY = 200
_log: Deque[AccessLogEntry] = deque(maxlen=_LOG_CAPACITY)
_lock = threading.Lock()


def record_access(
    *,
    agency: Optional[str],
    method: str,
    path: str,
    status_code: int,
    target_tin: Optional[str] = None,
) -> AccessLogEntry:
    entry = AccessLogEntry(
        at=datetime.now(timezone.utc),
        agency=agency,
        method=method,
        path=path,
        target_tin=target_tin,
        status_code=status_code,
    )
    with _lock:
        _log.append(entry)
    return entry


def recent(limit: int = 50) -> list[AccessLogEntry]:
    """Most-recent-first slice of the audit log."""
    with _lock:
        items: Iterable[AccessLogEntry] = list(_log)
    return list(reversed(list(items)))[:limit]


def clear() -> None:
    with _lock:
        _log.clear()
