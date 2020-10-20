from dataclasses import dataclass
from typing import List

import faust


class StatusEvent(faust.Record, serializer="json"):
    """
    Deserializer for a particular topic message
    """

    url: str
    http_status: int
    response_time: float
    event_time: str
    search_results: dict = {}
