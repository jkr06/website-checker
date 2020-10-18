import json
import logging
import typing

from dynaconf import settings
import faust

from db import ConnPool
from models import StatusEvent

app = faust.App("checkwebsite", broker=settings.KAFKA_BROKER_URL)

events_topic = app.topic("events", value_type=StatusEvent)

log = logging.getLogger(__name__)


@app.agent(events_topic)
async def process_event(events: typing.List[StatusEvent]) -> None:
    """
    Process events in 'events' topic.

    """
    async for event in events:
        log.info(event)
        await handle_event(event)

    log.info("shutting down, releasing DB pool")
    await ConnPool.clear()


async def handle_event(event):
    pool = await ConnPool.pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"INSERT INTO checker_event (url, http_status, response_time, "
                f"event_time, search_results) VALUES "
                f"('{event.url}', '{event.http_status}', '{event.response_time}', "
                f"'{event.event_time}', '{json.dumps(event.search_results)}')"
            )
