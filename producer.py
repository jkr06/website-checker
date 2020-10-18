import logging
import pytz
import re
import typing
import asyncio

from datetime import datetime
from dynaconf import settings
import faust
import httpx

from models import StatusEvent

app = faust.App("checkwebsite", broker=settings.KAFKA_BROKER_URL)

events_topic = app.topic("events", value_type=StatusEvent)

log = logging.getLogger("producer")


async def check_websites():
    while True:
        coros = [check_single(site) for site in settings.WEBSITES.keys()]
        await asyncio.gather(*coros)

        await asyncio.sleep(1)


async def check_single(site):
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_websites())
