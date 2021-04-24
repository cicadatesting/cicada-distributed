from unittest.mock import patch, Mock

from cicadad.services import eventing


@patch("cicadad.services.eventing.get_events")
def test_get_work(get_events_mock):
    c = Mock()
    h = 123
    re = set()

    e1 = eventing.WorkEvent(
        action="work",
        event_id="abc",
        amount=2,
        user_id_limit=None,
    )

    e2 = eventing.WorkEvent(
        action="work",
        event_id="def",
        amount=2,
        user_id_limit=None,
    )

    get_events_mock.return_value = [e1, e2]

    work = eventing.get_work(c, h, re)

    assert work.amount == 4
    assert work.ids == {"abc", "def"}


@patch("cicadad.services.eventing.get_events")
def test_get_work_seen_already(get_events_mock):
    c = Mock()
    h = 123
    re = set(["abc"])

    e1 = eventing.WorkEvent(
        action="work",
        event_id="abc",
        amount=2,
        user_id_limit=None,
    )

    e2 = eventing.WorkEvent(
        action="work",
        event_id="def",
        amount=2,
        user_id_limit=None,
    )

    get_events_mock.return_value = [e1, e2]

    work = eventing.get_work(c, h, re)

    assert work.amount == 2
    assert work.ids == {"def"}


@patch("cicadad.services.eventing.get_events")
def test_get_work_seen_hash(get_events_mock):
    c = Mock()
    h = 123
    re = set()

    e1 = eventing.WorkEvent(
        action="work",
        event_id="abc",
        amount=2,
        user_id_limit=200,
    )

    e2 = eventing.WorkEvent(
        action="work",
        event_id="def",
        amount=2,
        user_id_limit=100,
    )

    get_events_mock.return_value = [e1, e2]

    work = eventing.get_work(c, h, re)

    assert work.amount == 2
    assert work.ids == {"abc"}
