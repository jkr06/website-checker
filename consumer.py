import json
import logging
import ssl
import typing

from dynaconf import settings
import faust

from db import ConnPool
from models import StatusEvent


if settings.USE_SASL:
    ssl_context = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH, cafile=settings.CA_FILE
    )
    app = faust.App(
        "checkwebsite",
        topic_disable_leader=True,
        broker=settings.KAFKA_BROKER_URL,
        broker_credentials=faust.SASLCredentials(
            ssl_context=ssl_context,
            username=settings.KAFKA_USER,
            password=settings.KAFKA_PASSWORD,
        ),
    )
else:
    app = faust.App("checkwebsite", broker=settings.KAFKA_BROKER_URL)

events_topic = app.topic("events", value_type=StatusEvent)

log = logging.getLogger(__name__)


@app.agent(events_topic)
async def process_event(events: typing.List[StatusEvent]):
    """
    Process events in 'events' topic.

    """
    async for event in events:
        log.info(event)
        await handle_event(event)
        yield event

    log.info("shutting down, releasing DB pool")
    await ConnPool.clear()


async def handle_event(event: StatusEvent):
    pool = await ConnPool.pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"INSERT INTO events (url, http_status, response_time, "
                f"event_time, search_results) VALUES "
                f"('{event.url}', '{event.http_status}', '{event.response_time}', "
                f"'{event.event_time}', '{json.dumps(event.search_results)}')"
            )
