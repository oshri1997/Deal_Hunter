import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from scheduler import DealScheduler


@pytest.fixture
def bot():
    return AsyncMock()


@pytest.fixture
def deal_scheduler(bot):
    with patch("scheduler.ScraperManager"), \
         patch("scheduler.NotificationEngine"):
        ds = DealScheduler(bot)
        return ds


class TestSchedulerJobConfiguration:
    """Verify that jobs are registered with the correct triggers."""

    @pytest.mark.asyncio
    async def test_scrape_job_scheduled_at_0400(self, deal_scheduler):
        """The daily scrape job must fire at 04:00."""
        deal_scheduler.start(run_initial_scrape=False)

        job = deal_scheduler.scheduler.get_job("scrape_deals")
        assert job is not None
        trigger = job.trigger
        assert isinstance(trigger, CronTrigger)
        fields = {f.name: str(f) for f in trigger.fields}
        assert fields["hour"] == "4"
        assert fields["minute"] == "0"

        deal_scheduler.stop()

    @pytest.mark.asyncio
    async def test_deliver_job_scheduled_at_0900(self, deal_scheduler):
        """The delivery job must fire at 09:00."""
        deal_scheduler.start(run_initial_scrape=False)

        job = deal_scheduler.scheduler.get_job("deliver_deals")
        assert job is not None
        trigger = job.trigger
        assert isinstance(trigger, CronTrigger)
        fields = {f.name: str(f) for f in trigger.fields}
        assert fields["hour"] == "9"
        assert fields["minute"] == "0"

        deal_scheduler.stop()

    @pytest.mark.asyncio
    async def test_engagement_job_scheduled(self, deal_scheduler):
        """An engagement message job should be scheduled."""
        deal_scheduler.start(run_initial_scrape=False)

        job = deal_scheduler.scheduler.get_job("engagement_message")
        assert job is not None
        trigger = job.trigger
        assert isinstance(trigger, IntervalTrigger)

        deal_scheduler.stop()

    @pytest.mark.asyncio
    async def test_cleanup_job_scheduled_at_0300(self, deal_scheduler):
        """Cleanup job at 03:00."""
        deal_scheduler.start(run_initial_scrape=False)

        job = deal_scheduler.scheduler.get_job("cleanup_deals")
        assert job is not None
        trigger = job.trigger
        fields = {f.name: str(f) for f in trigger.fields}
        assert fields["hour"] == "3"

        deal_scheduler.stop()


class TestScrapeDeals:
    """Test the _scrape_deals internal method."""

    @pytest.mark.asyncio
    async def test_scrape_deals_calls_scraper_with_mark_pending(self, deal_scheduler):
        """_scrape_deals should call scrape_all_regions with mark_pending=True."""
        deal_scheduler.scraper_manager.scrape_all_regions = AsyncMock(return_value=[])

        await deal_scheduler._scrape_deals()

        deal_scheduler.scraper_manager.scrape_all_regions.assert_awaited_once_with(
            full_scrape=False, mark_pending=True
        )

    @pytest.mark.asyncio
    async def test_scrape_deals_handles_exception(self, deal_scheduler):
        """If scraping raises, the job logs but does not propagate."""
        deal_scheduler.scraper_manager.scrape_all_regions = AsyncMock(
            side_effect=RuntimeError("network down")
        )

        # Should not raise
        await deal_scheduler._scrape_deals()


class TestDeliverDeals:
    """Test the _deliver_deals internal method."""

    @pytest.mark.asyncio
    async def test_deliver_deals_calls_engine(self, deal_scheduler):
        """_deliver_deals should call deliver_pending_deals and check_price_alerts."""
        deal_scheduler.notification_engine.deliver_pending_deals = AsyncMock()
        deal_scheduler.notification_engine.check_price_alerts = AsyncMock()

        await deal_scheduler._deliver_deals()

        deal_scheduler.notification_engine.deliver_pending_deals.assert_awaited_once()
        deal_scheduler.notification_engine.check_price_alerts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deliver_deals_handles_exception(self, deal_scheduler):
        """If delivery raises, the job logs but does not propagate."""
        deal_scheduler.notification_engine.deliver_pending_deals = AsyncMock(
            side_effect=RuntimeError("db down")
        )

        await deal_scheduler._deliver_deals()


class TestScrapeAndNotifyNow:
    """Test manual admin trigger."""

    @pytest.mark.asyncio
    async def test_scrape_and_notify_now_with_deals(self, deal_scheduler):
        """Manual trigger should scrape and immediately notify."""
        fake_deal = MagicMock()
        deal_scheduler.scraper_manager.scrape_all_regions = AsyncMock(return_value=[fake_deal])
        deal_scheduler.notification_engine.notify_new_deals = AsyncMock()
        deal_scheduler.notification_engine.check_price_alerts = AsyncMock()

        await deal_scheduler.scrape_and_notify_now()

        deal_scheduler.scraper_manager.scrape_all_regions.assert_awaited_once_with(full_scrape=False)
        deal_scheduler.notification_engine.notify_new_deals.assert_awaited_once_with([fake_deal])
        deal_scheduler.notification_engine.check_price_alerts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_scrape_and_notify_now_no_deals(self, deal_scheduler):
        """When no new deals are found, notify_new_deals should not be called."""
        deal_scheduler.scraper_manager.scrape_all_regions = AsyncMock(return_value=[])
        deal_scheduler.notification_engine.notify_new_deals = AsyncMock()
        deal_scheduler.notification_engine.check_price_alerts = AsyncMock()

        await deal_scheduler.scrape_and_notify_now()

        deal_scheduler.notification_engine.notify_new_deals.assert_not_awaited()
        deal_scheduler.notification_engine.check_price_alerts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_scrape_and_notify_now_handles_exception(self, deal_scheduler):
        """Manual trigger should not propagate exceptions."""
        deal_scheduler.scraper_manager.scrape_all_regions = AsyncMock(
            side_effect=RuntimeError("fail")
        )

        await deal_scheduler.scrape_and_notify_now()


class TestEngagementScheduling:
    """Test engagement rescheduling logic."""

    @pytest.mark.asyncio
    async def test_send_engagement_reschedules(self, deal_scheduler):
        """After sending, _send_engagement should reschedule with a new interval."""
        deal_scheduler.start(run_initial_scrape=False)

        with patch("scheduler.send_engagement_message", new_callable=AsyncMock) as mock_send:
            old_job = deal_scheduler.scheduler.get_job("engagement_message")
            old_trigger = old_job.trigger

            await deal_scheduler._send_engagement()

            mock_send.assert_awaited_once_with(deal_scheduler.bot)
            new_job = deal_scheduler.scheduler.get_job("engagement_message")
            # Job should still exist (replaced)
            assert new_job is not None

        deal_scheduler.stop()

    @pytest.mark.asyncio
    async def test_send_engagement_handles_exception(self, deal_scheduler):
        """If engagement message fails, still reschedule."""
        deal_scheduler.start(run_initial_scrape=False)

        with patch("scheduler.send_engagement_message", new_callable=AsyncMock,
                    side_effect=RuntimeError("fail")):
            await deal_scheduler._send_engagement()

            # Job should still be rescheduled
            job = deal_scheduler.scheduler.get_job("engagement_message")
            assert job is not None

        deal_scheduler.stop()
