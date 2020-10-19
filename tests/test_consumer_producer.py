import asyncio
from asynctest import patch, Mock
from datetime import datetime
from decimal import Decimal
import pytest
import pytz

from dynaconf import settings
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pytest_httpx import HTTPXMock

from consumer import app, process_event, handle_event
from initdb import create_db, destroy_db, initialize_db
from models import StatusEvent
from producer import check_single


@pytest.fixture(scope="session")
def setup_database():
    """ Fixture to set up the in-memory database with test data """
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")
    db = settings.DATABASE

    print(f"creating the {db.dbname} database")
    create_db(**(dict(settings.DATABASE)))

    conn = psycopg2.connect(**(dict(settings.DATABASE)))
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    initialize_db(cur)

    yield cur

    cur.close()
    conn.close()

    print(f"dropping the {db.dbname} database")
    destroy_db(**(dict(settings.DATABASE)))


def mock_coro(return_value=None, **kwargs):
    """Create mock coroutine function."""

    async def wrapped(*args, **kwargs):
        return return_value

    return Mock(wraps=wrapped, **kwargs)


@pytest.mark.asyncio
async def test_event_agent(setup_database):
    cur = setup_database
    async with process_event.test_context() as agent:
        dt = datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.utc)
        event = StatusEvent(
            url="example.com",
            http_status=200,
            response_time=0.1,
            event_time=dt,
            search_results={"some pattern": False},
        )
        await agent.put(event)
    cur.execute("select * from events")
    rows = cur.fetchall()

    assert rows[0][1] == "example.com"
    assert rows[0][2] == 200
    assert rows[0][4] == dt
    assert rows[0][5] == {"some pattern": False}


@pytest.mark.asyncio
async def test_url_multiple_search(httpx_mock: HTTPXMock):
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")
    url = "http://test1_url"
    httpx_mock.add_response(url=url, data=b"xyz test123 abcd")

    with patch("producer.events_topic") as mock_fn:
        mock_fn.send = mock_coro()
        await check_single(url)
        actual_event = mock_fn.send.call_args[1]["value"]
        assert actual_event.url == url
        assert actual_event.http_status == 200
        assert actual_event.search_results == {"test123": True, "test789": False}


@pytest.mark.asyncio
async def test_url_no_search(httpx_mock: HTTPXMock):
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")
    url = "http://test3_url"
    httpx_mock.add_response(url=url, data=b"xyz test123 abcd")

    with patch("producer.events_topic") as mock_fn:
        mock_fn.send = mock_coro()
        await check_single(url)
        actual_event = mock_fn.send.call_args[1]["value"]
        assert actual_event.url == url
        assert actual_event.http_status == 200
        assert actual_event.search_results == {}


@pytest.mark.asyncio
async def test_url_http_status(httpx_mock: HTTPXMock):
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")
    url = "http://test3_url"
    httpx_mock.add_response(url=url, status_code=404, data=b"xyz test123 abcd")

    with patch("producer.events_topic") as mock_fn:
        mock_fn.send = mock_coro()
        await check_single(url)
        actual_event = mock_fn.send.call_args[1]["value"]
        assert actual_event.url == url
        assert actual_event.http_status == 404
        assert actual_event.search_results == {}
