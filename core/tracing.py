from __future__ import annotations

from typing import Optional
from langfuse import get_client


class Tracer:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._client = get_client() if enabled else None

    def start_trace(self, seed: Optional[str] = None) -> Optional[str]:
        if not self._client:
            return None
        return self._client.create_trace_id(seed=seed)

    def get_url(self, trace_id: Optional[str]) -> Optional[str]:
        if not (self._client and trace_id):
            return None
        return self._client.get_trace_url(trace_id=trace_id)
