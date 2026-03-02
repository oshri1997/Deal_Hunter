import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time

from engagement import (
    send_engagement_message,
    ENGAGEMENT_MESSAGES,
    FEATURE_TIPS,
)


def _mock_get_session_with_users(users):
    """Return a patched get_session that yields users from a select query."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = users
    mock_session.execute = AsyncMock(return_value=mock_result)

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _make_user(user_id):
    user = MagicMock()
    user.id = user_id
    return user


@pytest.fixture
def bot():
    return AsyncMock()


class TestTimeWindow:
    """Messages should only be sent between 08:00 and 20:00."""

    @pytest.mark.asyncio
    async def test_outside_window_early_morning(self, bot):
        """At 05:00 no message should be sent."""
        with patch("engagement.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 3, 2, 5, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            # time() must still work normally
            with patch("engagement.get_session") as mock_gs:
                await send_engagement_message(bot)
                mock_gs.assert_not_called()
        bot.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_outside_window_late_night(self, bot):
        """At 22:00 no message should be sent."""
        with patch("engagement.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 3, 2, 22, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            with patch("engagement.get_session") as mock_gs:
                await send_engagement_message(bot)
                mock_gs.assert_not_called()
        bot.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_inside_window_midday(self, bot):
        """At 12:00 messages should be sent."""
        users = [_make_user(1)]
        ctx = _mock_get_session_with_users(users)

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.5  # engagement message
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[0]
            # random.choice returns dict, so .get("text") via the real code
            # Actually the code does random.choice(ENGAGEMENT_MESSAGES)["text"]
            # so we need to return a real dict
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[0]

            await send_engagement_message(bot)

        bot.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_boundary_0800(self, bot):
        """At exactly 08:00 messages should be sent."""
        users = [_make_user(1)]
        ctx = _mock_get_session_with_users(users)

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 8, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.5
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[0]

            await send_engagement_message(bot)

        bot.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_boundary_2000(self, bot):
        """At exactly 20:00 messages should be sent."""
        users = [_make_user(1)]
        ctx = _mock_get_session_with_users(users)

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 20, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.5
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[0]

            await send_engagement_message(bot)

        bot.send_message.assert_awaited_once()


class TestMessageSelection:
    """Test the 40% tips / 60% engagement split."""

    @pytest.mark.asyncio
    async def test_feature_tip_selected_when_random_below_04(self, bot):
        """random() < 0.4 should pick a feature tip."""
        users = [_make_user(1)]
        ctx = _mock_get_session_with_users(users)
        tip = FEATURE_TIPS[0]

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.2  # < 0.4 -> tip
            mock_random.choice.return_value = tip

            await send_engagement_message(bot)

        sent_text = bot.send_message.call_args.kwargs["text"]
        assert sent_text == tip

    @pytest.mark.asyncio
    async def test_engagement_message_selected_when_random_above_04(self, bot):
        """random() >= 0.4 should pick an engagement message."""
        users = [_make_user(1)]
        ctx = _mock_get_session_with_users(users)

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.7  # >= 0.4 -> engagement
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[1]

            await send_engagement_message(bot)

        sent_text = bot.send_message.call_args.kwargs["text"]
        assert sent_text == ENGAGEMENT_MESSAGES[1]["text"]


class TestNoUsers:
    """When there are no users, nothing should be sent."""

    @pytest.mark.asyncio
    async def test_no_users_no_messages(self, bot):
        ctx = _mock_get_session_with_users([])

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.5
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[0]

            await send_engagement_message(bot)

        bot.send_message.assert_not_awaited()


class TestMultipleUsers:
    """Messages should be sent to every user."""

    @pytest.mark.asyncio
    async def test_message_sent_to_all_users(self, bot):
        users = [_make_user(1), _make_user(2), _make_user(3)]
        ctx = _mock_get_session_with_users(users)

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.5
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[0]

            await send_engagement_message(bot)

        assert bot.send_message.await_count == 3
        sent_ids = {c.kwargs["chat_id"] for c in bot.send_message.call_args_list}
        assert sent_ids == {1, 2, 3}


class TestTelegramFailure:
    """Failures for individual users should not stop delivery to others."""

    @pytest.mark.asyncio
    async def test_failure_does_not_stop_other_users(self, bot):
        from telegram.error import TelegramError

        users = [_make_user(1), _make_user(2)]
        ctx = _mock_get_session_with_users(users)

        # First call fails, second succeeds
        bot.send_message.side_effect = [TelegramError("blocked"), None]

        with patch("engagement.datetime") as mock_dt, \
             patch("engagement.get_session", return_value=ctx), \
             patch("engagement.random") as mock_random:
            mock_dt.now.return_value = datetime(2026, 3, 2, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_random.random.return_value = 0.5
            mock_random.choice.return_value = ENGAGEMENT_MESSAGES[0]

            await send_engagement_message(bot)

        assert bot.send_message.await_count == 2


class TestEngagementSchedulingInterval:
    """The scheduler should use a 4-6 hour interval."""

    def test_schedule_interval_between_4_and_6(self):
        """_schedule_next_engagement should create a job with 4-6h interval."""
        with patch("scheduler.ScraperManager"), \
             patch("scheduler.NotificationEngine"), \
             patch("scheduler.AmazonChecker"), \
             patch("scheduler.random") as mock_random:
            mock_random.uniform.return_value = 5.0

            from scheduler import DealScheduler
            bot = AsyncMock()
            ds = DealScheduler(bot)
            ds._schedule_next_engagement()

            mock_random.uniform.assert_called_once_with(4, 6)
            job = ds.scheduler.get_job("engagement_message")
            assert job is not None
