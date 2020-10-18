from dataclasses import dataclass
from typing import List

import faust


@dataclass
class SearchResult:
    pattern: str
    found: bool


class StatusEvent(faust.Record, serializer="json"):
    """
    Deserializer for a particular topic message
    """

    url: str
    http_status: int
    response_time: float
    event_time: str
    search_results: SearchResult = {}
