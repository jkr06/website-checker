import asyncio
from datetime import datetime
import logging
import pytz
import re
import ssl
import typing

from dynaconf import settings
import faust
import httpx

from models import StatusEvent

if settings.USE_SASL:
    ssl_context = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH, cafile=settings.CA_FILE
    )
    app = faust.App(
        "checkwebsite",
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

log = logging.getLogger("producer")


@app.timer(settings.PRODUCER_FREQUENCY)
async def check_websites():
    coros = [check_single(site) for site in settings.WEBSITES.keys()]
    await asyncio.gather(*coros)


async def check_single(site: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(site)
    event = StatusEvent(
        url=site,
        http_status=response.status_code,
        response_time=response.elapsed.total_seconds(),
        event_time=datetime.now(pytz.utc),
    )
    event.search_results = {
        pattern: bool(re.search(pattern, str(response.content)))
        for pattern in settings.WEBSITES.get(site)
    }
    await events_topic.send(value=event)
    log.info("event sent %s", event)
