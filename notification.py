import asyncio
import logging
from typing import List
from urllib.parse import quote

from sqlalchemy import select
from telegram import Bot
from telegram.error import TelegramError

from database.engine import get_session
from database.models import User, UserRegion, UserWishlist, ActiveDeal, Game, PriceAlert
from config import config

logger = logging.getLogger(__name__)


class NotificationEngine:
    """Matches deals to users and sends notifications"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_new_deals(self, deals: List[ActiveDeal]):
        """Send notifications for new deals to all matching users"""
        if not deals:
            return

        logger.info(f"Processing {len(deals)} new deals for notifications")

        async with get_session() as session:
            # First, update placeholder games to real games
            await self._update_placeholder_games(session, deals)
            
            for deal in deals:
                sent_user_ids = set()

                # Find users with this game on their wishlist (high priority)
                wishlist_result = await session.execute(
                    select(User, UserWishlist)
                    .join(UserWishlist, User.id == UserWishlist.user_id)
                    .where(UserWishlist.game_id == deal.game_id)
                )
                wishlist_users = wishlist_result.all()

                # Find users subscribed to this region
                result = await session.execute(
                    select(User, UserRegion)
                    .join(UserRegion, User.id == UserRegion.user_id)
                    .where(UserRegion.region_code == deal.region_code)
                )
                region_users = result.all()

                # Get game details
                game_result = await session.execute(
                    select(Game).where(Game.id == deal.game_id)
                )
                game = game_result.scalar_one_or_none()

                if not game:
                    continue

                # Send to wishlist users first (high priority)
                for user, _ in wishlist_users:
                    await self._send_deal_notification(user, deal, game, is_wishlist=True)
                    sent_user_ids.add(user.id)
                    await asyncio.sleep(0.05)

                # Send to region subscribers (skip if already notified via wishlist)
                for user, _ in region_users:
                    if user.id not in sent_user_ids:
                        await self._send_deal_notification(user, deal, game, is_wishlist=False)
                        sent_user_ids.add(user.id)
                        await asyncio.sleep(0.05)

    async def check_price_alerts(self):
        """Check all active price alerts against current deals"""
        logger.info("Checking price alerts...")

        async with get_session() as session:
            # Get all active alerts
            result = await session.execute(
                select(PriceAlert, Game)
                .join(Game, PriceAlert.game_id == Game.id)
                .where(PriceAlert.is_active == True)
            )
            alerts = result.all()

            if not alerts:
                logger.info("No active price alerts")
                return

            triggered_count = 0

            for alert, game in alerts:
                # Check if there's an active deal matching this alert
                deal_query = select(ActiveDeal).where(
                    ActiveDeal.game_id == alert.game_id,
                    ActiveDeal.region_code == alert.region_code,
                )
                deal_result = await session.execute(deal_query)
                deal = deal_result.scalar_one_or_none()

                if not deal:
                    continue

                # Check if alert conditions are met
                triggered = False
                trigger_reason = ""

                if alert.target_price is not None and deal.price <= alert.target_price:
                    triggered = True
                    region_info = config.REGIONS.get(alert.region_code, {})
                    symbol = region_info.get("currency_symbol", "$")
                    trigger_reason = f"Price dropped to {symbol}{deal.price:.2f} (your target: {symbol}{alert.target_price:.2f})"

                if alert.target_discount is not None and deal.discount_percent >= alert.target_discount:
                    triggered = True
                    trigger_reason = f"Discount reached {deal.discount_percent}% (your target: {alert.target_discount}%)"

                if triggered:
                    # Send alert notification
                    user = await session.get(User, alert.user_id)
                    if user:
                        await self._send_price_alert(user, game, deal, trigger_reason)
                        triggered_count += 1

                    # Deactivate alert
                    from datetime import datetime
                    alert.is_active = False
                    alert.triggered_at = datetime.utcnow()
                    await asyncio.sleep(0.05)

            logger.info(f"Triggered {triggered_count} price alerts")

    async def _update_placeholder_games(self, session, deals: List[ActiveDeal]):
        """Update placeholder games to real games when they match"""
        # Get all placeholder games in wishlists
        placeholder_result = await session.execute(
            select(UserWishlist, Game)
            .join(Game, UserWishlist.game_id == Game.id)
            .where(Game.id.like("search_%"))
        )
        placeholders = placeholder_result.all()
        
        if not placeholders:
            return
        
        updated_count = 0
        for deal in deals:
            game = await session.get(Game, deal.game_id)
            if not game:
                continue
            
            # Check if any placeholder matches this game
            for wishlist, placeholder_game in placeholders:
                # Check if placeholder title is in real game title
                if placeholder_game.title.lower() in game.title.lower():
                    logger.info(f"Updating placeholder '{placeholder_game.title}' to real game '{game.title}'")
                    wishlist.game_id = game.id
                    updated_count += 1
        
        if updated_count > 0:
            await session.commit()
            logger.info(f"Updated {updated_count} placeholder games to real games")

    async def _send_deal_notification(self, user: User, deal: ActiveDeal, game: Game, is_wishlist: bool):
        """Send individual deal notification with store links"""
        region_info = config.REGIONS.get(deal.region_code, {})
        flag = region_info.get("flag", "")
        currency = region_info.get("currency_symbol", "")
        store_url = region_info.get("store_url", "")

        wishlist_tag = "⭐ WISHLIST ALERT! " if is_wishlist else ""

        end_date_str = deal.sale_end_date.strftime('%Y-%m-%d') if deal.sale_end_date else "Unknown"

        # Build store links
        search_query = quote(game.title)
        psn_link = f"{store_url}/search/{search_query}" if store_url else ""
        cdkeys_link = f"https://www.cdkeys.com/catalogsearch/result?q={search_query}"

        message = (
            f"{wishlist_tag}{flag} New Deal in {region_info.get('name', deal.region_code)}!\n\n"
            f"🎮 {game.title}\n"
            f"💰 {currency}{deal.price:.2f} (was {currency}{deal.original_price:.2f})\n"
            f"🔥 {deal.discount_percent}% OFF\n"
            f"⏰ Ends: {end_date_str}\n\n"
            f"🛒 PS Store: {psn_link}\n"
            f"🔑 CDKeys: {cdkeys_link}"
        )

        try:
            await self.bot.send_message(chat_id=user.id, text=message)
            logger.info(f"Sent notification to user {user.id}")
        except TelegramError as e:
            logger.error(f"Failed to send notification to {user.id}: {e}")

    async def _send_price_alert(self, user: User, game: Game, deal: ActiveDeal, trigger_reason: str):
        """Send price alert notification"""
        region_info = config.REGIONS.get(deal.region_code, {})
        flag = region_info.get("flag", "")
        currency = region_info.get("currency_symbol", "")
        store_url = region_info.get("store_url", "")

        search_query = quote(game.title)
        psn_link = f"{store_url}/search/{search_query}" if store_url else ""

        message = (
            f"🔔 PRICE ALERT TRIGGERED!\n\n"
            f"🎮 {game.title}\n"
            f"{flag} {region_info.get('name', deal.region_code)}\n\n"
            f"✅ {trigger_reason}\n\n"
            f"💰 Current price: {currency}{deal.price:.2f} (was {currency}{deal.original_price:.2f})\n"
            f"🔥 {deal.discount_percent}% OFF\n\n"
            f"🛒 Buy now: {psn_link}"
        )

        try:
            await self.bot.send_message(chat_id=user.id, text=message)
            logger.info(f"Sent price alert to user {user.id} for {game.title}")
        except TelegramError as e:
            logger.error(f"Failed to send price alert to {user.id}: {e}")
