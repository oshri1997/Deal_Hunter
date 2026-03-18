import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime
from decimal import Decimal

from notification import NotificationEngine


def _make_deal(game_id="game1", region_code="IL", pending=True, price=19.99,
               original_price=59.99, discount_percent=67):
    """Helper to build a mock ActiveDeal."""
    deal = MagicMock()
    deal.game_id = game_id
    deal.region_code = region_code
    deal.pending_notification = pending
    deal.price = Decimal(str(price))
    deal.original_price = Decimal(str(original_price))
    deal.discount_percent = discount_percent
    deal.currency = "ILS"
    deal.sale_end_date = datetime(2026, 12, 31)
    return deal


def _make_game(game_id="game1", title="Test Game"):
    game = MagicMock()
    game.id = game_id
    game.title = title
    return game


def _make_user(user_id=100):
    user = MagicMock()
    user.id = user_id
    return user


@pytest.fixture
def bot():
    return AsyncMock()


@pytest.fixture
def engine(bot):
    return NotificationEngine(bot)


class TestDeliverPendingDeals:
    """Tests for deliver_pending_deals."""

    @pytest.mark.asyncio
    async def test_queries_only_pending_deals(self, engine):
        """deliver_pending_deals should query ActiveDeal.pending_notification == True."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("notification.get_session", return_value=ctx):
            await engine.deliver_pending_deals()

        # The execute call should have been made (querying pending deals)
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_clears_pending_flag_after_delivery(self, engine):
        """After delivery, pending_notification should be set to False."""
        deal1 = _make_deal("g1", pending=True)
        deal2 = _make_deal("g2", pending=True)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [deal1, deal2]
        mock_session.execute = AsyncMock(return_value=mock_result)

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("notification.get_session", return_value=ctx), \
             patch.object(engine, "notify_new_deals", new_callable=AsyncMock):
            await engine.deliver_pending_deals()

        assert deal1.pending_notification is False
        assert deal2.pending_notification is False
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_pending_deals_returns_early(self, engine):
        """When there are no pending deals, notify_new_deals should not be called."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("notification.get_session", return_value=ctx), \
             patch.object(engine, "notify_new_deals", new_callable=AsyncMock) as mock_notify:
            await engine.deliver_pending_deals()

        mock_notify.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_pending_deals_passed_to_notify(self, engine):
        """Pending deals should be forwarded to notify_new_deals."""
        deal1 = _make_deal("g1", pending=True)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [deal1]
        mock_session.execute = AsyncMock(return_value=mock_result)

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("notification.get_session", return_value=ctx), \
             patch.object(engine, "notify_new_deals", new_callable=AsyncMock) as mock_notify:
            await engine.deliver_pending_deals()

        mock_notify.assert_awaited_once_with([deal1])


class TestNotifyNewDeals:
    """Tests for notify_new_deals."""

    @pytest.mark.asyncio
    async def test_empty_deals_returns_immediately(self, engine):
        """notify_new_deals([]) should return without DB queries."""
        with patch("notification.get_session") as mock_gs:
            await engine.notify_new_deals([])
            mock_gs.assert_not_called()

    @pytest.mark.asyncio
    async def test_wishlist_users_notified_first(self, engine, bot):
        """Users with the game on their wishlist should be notified."""
        deal = _make_deal("g1", region_code="IL")
        game = _make_game("g1", "Test Game")
        user = _make_user(100)

        mock_session = AsyncMock()

        # First execute: _update_placeholder_games -> placeholders query
        placeholder_result = MagicMock()
        placeholder_result.all.return_value = []

        # Second execute: wishlist query
        wishlist_result = MagicMock()
        wishlist_result.all.return_value = [(user, MagicMock())]

        # Third execute: region subscribers query
        region_result = MagicMock()
        region_result.all.return_value = []

        # Fourth execute: game query
        game_result = MagicMock()
        game_result.scalar_one_or_none.return_value = game

        mock_session.execute = AsyncMock(
            side_effect=[placeholder_result, wishlist_result, region_result, game_result]
        )
        mock_session.get = AsyncMock(return_value=None)

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("notification.get_session", return_value=ctx), \
             patch("notification.ExchangeRateService.convert_to_ils", new_callable=AsyncMock, return_value=70.0), \
             patch("notification.is_subscriber", new_callable=AsyncMock, return_value=True):
            await engine.notify_new_deals([deal])

        bot.send_message.assert_awaited_once()
        call_kwargs = bot.send_message.call_args
        assert call_kwargs.kwargs["chat_id"] == 100

    @pytest.mark.asyncio
    async def test_region_subscriber_not_duplicated_with_wishlist(self, engine, bot):
        """A user on both wishlist and region list should only get one notification."""
        deal = _make_deal("g1", region_code="IL")
        game = _make_game("g1", "Test Game")
        user = _make_user(100)

        mock_session = AsyncMock()

        placeholder_result = MagicMock()
        placeholder_result.all.return_value = []

        wishlist_result = MagicMock()
        wishlist_result.all.return_value = [(user, MagicMock())]

        # Same user is also a region subscriber
        region_result = MagicMock()
        region_result.all.return_value = [(user, MagicMock())]

        game_result = MagicMock()
        game_result.scalar_one_or_none.return_value = game

        mock_session.execute = AsyncMock(
            side_effect=[placeholder_result, wishlist_result, region_result, game_result]
        )
        mock_session.get = AsyncMock(return_value=None)

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("notification.get_session", return_value=ctx), \
             patch("notification.ExchangeRateService.convert_to_ils", new_callable=AsyncMock, return_value=70.0), \
             patch("notification.is_subscriber", new_callable=AsyncMock, return_value=True):
            await engine.notify_new_deals([deal])

        # Should be called exactly once (not twice)
        assert bot.send_message.await_count == 1
