"""Test Google report state."""
from unittest.mock import patch

from homeassistant.components.google_assistant import report_state
from homeassistant.util.dt import utcnow

from . import BASIC_CONFIG


from tests.common import mock_coro, async_fire_time_changed


async def test_report_state(hass):
    """Test report state works."""
    hass.states.async_set("light.ceiling", "off")
    hass.states.async_set("switch.ac", "on")

    with patch.object(
        BASIC_CONFIG, "async_report_state", side_effect=mock_coro
    ) as mock_report, patch.object(report_state, "INITIAL_REPORT_DELAY", 0):
        unsub = report_state.async_enable_report_state(hass, BASIC_CONFIG)

        async_fire_time_changed(hass, utcnow())
        await hass.async_block_till_done()

    # Test that enabling report state does a report on all entities
    assert len(mock_report.mock_calls) == 1
    assert mock_report.mock_calls[0][1][0] == {
        "devices": {
            "states": {
                "light.ceiling": {"on": False, "online": True},
                "switch.ac": {"on": True, "online": True},
            }
        }
    }

    with patch.object(
        BASIC_CONFIG, "async_report_state", side_effect=mock_coro
    ) as mock_report:
        hass.states.async_set("light.kitchen", "on")
        await hass.async_block_till_done()

    assert len(mock_report.mock_calls) == 1
    assert mock_report.mock_calls[0][1][0] == {
        "devices": {"states": {"light.kitchen": {"on": True, "online": True}}}
    }

    # Test that state changes that change something that Google doesn't care about
    # do not trigger a state report.
    with patch.object(
        BASIC_CONFIG, "async_report_state", side_effect=mock_coro
    ) as mock_report:
        hass.states.async_set(
            "light.kitchen", "on", {"irrelevant": "should_be_ignored"}
        )
        await hass.async_block_till_done()

    assert len(mock_report.mock_calls) == 0

    unsub()

    with patch.object(
        BASIC_CONFIG, "async_report_state", side_effect=mock_coro
    ) as mock_report:
        hass.states.async_set("light.kitchen", "on")
        await hass.async_block_till_done()

    assert len(mock_report.mock_calls) == 0
