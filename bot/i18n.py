"""Internationalization support for PS Deal Hunter Bot."""

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Language selection
        "choose_language": "🌍 <b>Welcome to PS Deal Hunter!</b>\n\nPlease choose your language / אנא בחר שפה:",
        "language_set": "✅ Language set to English!",
        "language_changed": "✅ Language changed to English!",
        "btn_english": "🇬🇧 English",
        "btn_hebrew": "🇮🇱 עברית",
        # Welcome / Help
        "welcome": (
            "🎮 <b>Welcome to PS Deal Hunter!</b>\n\n"
            "I track PlayStation Store deals across multiple regions and send real-time notifications.\n\n"
            "<b>🚀 Getting started:</b>\n"
            "1. Choose your regions with /regions\n"
            "2. Browse deals with /deals\n"
            "3. Track games with /watch\n"
            "💡 Don't want deal alerts? No need to select a region!\n\n"
            "<b>📋 Free commands:</b>\n"
            "/regions – Select PSN regions\n"
            "/deals – Current deals\n"
            "/search &lt;game&gt; – Search for a game\n"
            "/watch &lt;game&gt; – Add to wishlist\n"
            "/unwatch &lt;name|number&gt; – Remove from wishlist\n"
            "/watchlist – Your tracked games\n"
            "/giftcard – Check Amazon gift card availability\n"
            "/settings – Your preferences\n"
            "/language – Change language\n\n"
            "<b>⭐ Subscribers only:</b>\n"
            "/compare &lt;game&gt; – Compare prices across regions\n"
            "/alert &lt;game&gt; &lt;price|%&gt; – Set price alert\n"
            "/alerts – Your active alerts\n"
            "/follow – Get gift card stock alerts\n"
            "+ Daily deal alerts &amp; price drop notifications\n\n"
            "<b>🔔 Subscription:</b>\n"
            "/subscribe – Subscribe for premium alerts\n"
            "/paid – Notify us after payment\n"
            "/status – Check your subscription status\n"
            "/unsubscribe – Cancel your subscription\n"
            "/donate – Support the bot\n\n"
            '☕ <a href="https://buymeacoffee.com/oshri1997">buymeacoffee.com/oshri1997</a>'
        ),
        # Regions
        "regions_title": "🌍 *Select your PSN store regions:*\n{count}\n\nTap a region to toggle it on/off\\.",
        "regions_count": "Selected: {n} region(s)",
        "regions_done_none": "⚠️ You haven't selected any regions\\. Use /regions to choose at least one\\.",
        "regions_done_ok": "✅ *Subscribed to:* {regions}\n\nYou'll receive deal alerts for these regions\\.\nUse /deals to see current deals\\!",
        "regions_start_first": "Please use /start first.",
        "regions_done_btn": "✅ Done",
        # Deals
        "deals_no_regions": "⚠️ You haven't selected any regions yet.\nUse /regions to choose your PSN store regions first!",
        "deals_fetching": "🔍 Fetching latest deals...",
        "deals_header": "<b>🎮 PLAYSTATION DEALS 🎮</b>\n",
        "deals_new_lowest": " 🔥 <b>NEW LOWEST!</b>",
        "deals_lowest": " ⭐ <b>LOWEST</b>",
        "deals_ps_store": "PS Store",
        "deals_show_more": "📄 Show More",
        "deals_none": "❌ No deals found right now. Check back later!",
        "deals_session_expired": "⚠️ Session expired. Use /deals again.",
        "deals_loading_more": "Loading more deals...",
        # Wishlist
        "watch_usage": "ℹ️ *Usage:* `/watch Game Title`\nExample: `/watch God of War Ragnarok`",
        "watch_already": "ℹ️ *{title}* is already on your watchlist\\!",
        "watch_added": "✅ Added *{title}* to your watchlist\\!\nYou'll be notified when it goes on sale\\.",
        "unwatch_usage": "ℹ️ *Usage:* `/unwatch Game Title` or `/unwatch <number>`\nExample: `/unwatch God of War` or `/unwatch 1`",
        "unwatch_invalid_num": "⚠️ Invalid number\\. Use `/watchlist` to see your games\\.",
        "unwatch_removed": "❌ Removed *{title}* from your watchlist\\.",
        "unwatch_not_found": "⚠️ *{title}* is not on your watchlist\\.",
        "watchlist_empty": "📋 *Your watchlist is empty\\.*\nUse `/watch Game Title` to start tracking games\\!",
        "watchlist_header": "📋 *Your Watchlist:*\n",
        "watchlist_count": "📦 {n} game\\(s\\) tracked",
        "watchlist_tip": "ℹ️ Use `/unwatch <number>` or `/unwatch <game name>` to remove",
        # Search
        "search_usage": "Usage: /search <game name>\nExample: /search Spider-Man",
        "search_searching": "🔍 Searching for '{query}'...",
        "search_reply_num": "\n\n📝 Reply with a <b>number</b> to see details.\n🌐 Didn't find your game? Send <b>0</b> to search online.",
        "search_session_expired": "⚠️ Session expired. Use /search again.",
        "search_invalid_pick": "⚠️ Please reply with a number, or /cancel to stop.",
        "search_pick_range": "⚠️ Pick a number between 1 and {max}, or 0 for online search.",
        "search_pick_range_online": "⚠️ Pick a number between 1 and {max}.",
        "search_online": "🌐 Searching online...",
        "search_online_failed": "❌ Online search failed. Try again later.",
        "search_no_results": "❌ No games found matching '{query}' on PSPrices either.",
        "search_online_found": "🌐 Found {n} games on PSPrices:\n",
        "search_online_pick": "\n📝 Reply with a <b>number</b> to see details, or /cancel to stop.",
        "search_cancelled": "🔍 Search cancelled.",
        "search_no_price": "💰 No price data",
        "search_no_price_available": "💰 No price data available.",
        "search_watch_tip": "💡 Use <code>/watch {title}</code> to track this game!",
        "search_found": "🎮 Found {n} result(s):",
        "search_more": "\n<i>...more results available. Send <b>0</b> to search online for all results.</i>",
        "search_no_active_deal": "💰 No active deal",
        "search_free": "💰 Free",
        # Alerts
        "alert_usage": (
            "ℹ️ *Usage:*\n"
            "`/alert Game Title 100` \\- Alert when price drops below 100\n"
            "`/alert Game Title 50%` \\- Alert when discount reaches 50%\n\n"
            "Example:\n"
            "`/alert God of War Ragnarok 100`\n"
            "`/alert Elden Ring 50%`"
        ),
        "alert_invalid_discount": "⚠️ Discount must be between 1% and 99%.",
        "alert_invalid_discount_fmt": "⚠️ Invalid discount format\\. Use e\\.g\\. `50%`",
        "alert_price_positive": "⚠️ Price must be greater than 0.",
        "alert_invalid_target": "⚠️ Invalid target\\. Use a price \\(e\\.g\\. `100`\\) or discount \\(e\\.g\\. `50%`\\)",
        "alert_no_regions": "⚠️ You haven't selected any regions yet.\nUse /regions to choose your PSN store regions first!",
        "alert_no_game": "⚠️ No game found matching *{game}*\\.\nTry a different search term or use /search first\\.",
        "alert_already_set": "ℹ️ You already have active alerts for *{game}* in all your regions\\.",
        "alert_set": (
            "🔔 *Price alert set\\!*\n\n"
            "🎮 {game}\n"
            "🎯 Target: {target}\n"
            "📍 Regions: {regions}\n\n"
            "You'll be notified when the conditions are met\\!"
        ),
        "alert_target_discount": "{pct}% discount",
        "alert_target_price": "price below {price}",
        "alerts_none": "🔔 *No active price alerts\\.*\nUse `/alert Game Title 100` to set one\\!",
        "alerts_header": "🔔 *Your Price Alerts:*\n",
        "alerts_count": "📊 {n} active alert\\(s\\)",
        "alerts_tip": "Use `/delalert <number>` to remove an alert\\.",
        "alerts_below": "below {sym}{price}",
        "alerts_discount": "{pct}% discount",
        "delalert_usage": "ℹ️ *Usage:* `/delalert 1`\nUse /alerts to see your alert numbers\\.",
        "delalert_invalid": "⚠️ Please provide a valid number\\.",
        "delalert_out_of_range": "⚠️ Invalid alert number\\. You have {n} active alerts\\.\nUse /alerts to see the list\\.",
        "delalert_removed": "❌ Removed alert for *{game}*\\.",
        # Compare
        "compare_usage": "ℹ️ Usage: /compare Game Title\nExample: /compare God of War Ragnarok",
        "compare_no_games": "⚠️ No games found for '{query}'.\nTry a different search term.",
        "compare_no_deals": "⚠️ No deals found for '{query}'.\nThese games are not currently on sale.",
        "compare_cheapest": " 👍 <b>CHEAPEST</b>",
        "compare_no_deal": "<i>No deal available</i>",
        "compare_best": "💡 Best: {flag} {name}",
        "compare_buy": "🛒 <a href='{url}'>Buy on PS Store</a>",
        "compare_header": "🎮 <b>Price Comparison for '{query}'</b>\n",
        # Settings
        "settings_header": "⚙️ *Your Settings*\n",
        "settings_subscription": "*Subscription:* {status}",
        "settings_active": "✅ Active",
        "settings_inactive": "❌ Inactive",
        "settings_regions": "*Regions:* {regions}",
        "settings_regions_none": "None",
        "settings_watchlist": "*Watchlist:* {n} games",
        "settings_actions": "*Quick actions:*",
        "settings_change_regions": "/regions \\- Change regions",
        "settings_view_watchlist": "/watchlist \\- View watchlist",
        "settings_subscribe": "/subscribe \\- Get premium alerts",
        "settings_status": "/status \\- Check subscription",
        "settings_language": "/language \\- Change language",
        # Subscribe / status
        "subscribe_msg": (
            "🎮 <b>PS Deal Hunter — Premium Alerts</b>\n\n"
            "Get real-time deal alerts, price drop notifications, "
            "and gift card stock alerts delivered straight to your chat.\n\n"
            "☕ Subscribe here: {url}\n\n"
            "After paying, run /paid to let us know!"
        ),
        "subscribe_already_active": "✅ You already have an active subscription!",
        "subscribe_pending": "⏳ Your payment is already pending approval.",
        "subscribe_got_it": "Got it! You'll be approved shortly.",
        "subscribe_approved_msg": "You're now a subscriber! Alerts are active. 🎉",
        "subscribe_revoked_msg": "Your subscription has ended.",
        "subscribe_active": "✅ Your subscription is active.",
        "subscribe_not_active": "❌ You don't have an active subscription. Use /subscribe to get started.",
        "subscribe_cancelled": (
            "Your subscription has been cancelled.\n\n"
            "⚠️ To stop future payments, also cancel on Buy Me a Coffee:\n"
            "{url}\n"
            "Go to your account → Manage Memberships → Cancel\n\n"
            "Use /subscribe if you'd like to rejoin."
        ),
        "subscribe_not_active_cancel": "❌ You don't have an active subscription.",
        # Follow
        "follow_on": (
            "🔔 <b>Subscribed to gift card alerts!</b>\n\n"
            "You'll be notified as soon as the Amazon PlayStation Gift Card becomes available.\n\n"
            "Use /follow again to unsubscribe."
        ),
        "follow_off": (
            "🔕 <b>Unsubscribed from gift card alerts.</b>\n\n"
            "Use /follow to subscribe again."
        ),
        # Donate
        "donate_msg": (
            "💝 Support PS5 Deal Hunter!\n\n"
            "This bot is free for everyone. If it helped you\n"
            "find a great deal, consider supporting development:\n\n"
            "☕ Buy me a coffee:\n"
            "   https://buymeacoffee.com/oshri1997\n\n"
            "Every contribution helps keep the bot running\n"
            "and fund new features! 🙏"
        ),
        # Premium
        "premium_msg": (
            "🔔 <b>PS Deal Hunter — Premium</b>\n\n"
            "<b>Subscribers get:</b>\n"
            "• ⭐ Daily deal alerts to your chat\n"
            "• ⭐ Price drop notifications\n"
            "• ⭐ Gift card stock alerts (/follow)\n"
            "• ⭐ Cross-region price comparison (/compare)\n"
            "• ⭐ Price alerts (/alert)\n\n"
            "<b>Free for everyone:</b>\n"
            "• 🔍 Search &amp; browse deals\n"
            "• 📋 Wishlist\n"
            "• 🎮 Check gift card availability\n\n"
            "Use /subscribe to get started!\n"
            "Use /status to check your subscription."
        ),
        # require_subscriber
        "subscriber_only": "🔒 This feature is for subscribers only.\nUse /subscribe to get started.",
    },
    "he": {
        # Language selection
        "choose_language": "🌍 <b>ברוכים הבאים ל-PS Deal Hunter!</b>\n\nאנא בחר שפה / Please choose your language:",
        "language_set": "✅ השפה הוגדרה לעברית!",
        "language_changed": "✅ השפה שונתה לעברית!",
        "btn_english": "🇬🇧 English",
        "btn_hebrew": "🇮🇱 עברית",
        # Welcome / Help
        "welcome": (
            "🎮 <b>ברוכים הבאים ל-PS Deal Hunter!</b>\n\n"
            "הבוט עוקב אחרי מבצעים ב-PlayStation Store ממדינות שונות ושולח התראות בזמן אמת.\n\n"
            "<b>🚀 איך מתחילים:</b>\n"
            "1. בחר אזורים עם /regions\n"
            "2. צפה במבצעים עם /deals\n"
            "3. עקוב אחרי משחקים עם /watch\n"
            "💡 לא רוצה לקבל התראות על מבצעים? אין צורך לבחור אזור!\n\n"
            "<b>📋 פקודות חינמיות:</b>\n"
            "/regions – בחר אזורי PSN\n"
            "/deals – מבצעים נוכחיים\n"
            "/search &lt;משחק&gt; – חפש משחק\n"
            "/watch &lt;משחק&gt; – הוסף לרשימת המשאלות\n"
            "/unwatch &lt;שם|מספר&gt; – הסר מהרשימה\n"
            "/watchlist – הרשימה שלך\n"
            "/giftcard – זמינות גיפט קארד Amazon\n"
            "/settings – הגדרות\n"
            "/language – שנה שפה\n\n"
            "<b>⭐ למנויים בלבד:</b>\n"
            "/compare &lt;משחק&gt; – השוואת מחירים בין אזורים\n"
            "/alert &lt;משחק&gt; &lt;מחיר|%&gt; – התראת מחיר\n"
            "/alerts – ההתראות הפעילות שלך\n"
            "/follow – עדכונים על גיפט קארד\n"
            "+ התראות יומיות על מבצעים וירידות מחיר\n\n"
            "<b>🔔 מנוי:</b>\n"
            "/subscribe – הרשמה למנוי\n"
            "/paid – דיווח על תשלום\n"
            "/status – בדיקת סטטוס מנוי\n"
            "/unsubscribe – ביטול מנוי\n"
            "/donate – תמוך בפיתוח\n\n"
            '☕ <a href="https://buymeacoffee.com/oshri1997">buymeacoffee.com/oshri1997</a>'
        ),
        # Regions
        "regions_title": "🌍 *בחר את אזורי ה\\-PSN שלך:*\n{count}\n\nלחץ על אזור להפעלה/ביטול\\.",
        "regions_count": "נבחרו: {n} אזור/ים",
        "regions_done_none": "⚠️ לא בחרת אזורים\\. השתמש ב-/regions לבחירת לפחות אזור אחד\\.",
        "regions_done_ok": "✅ *נרשמת ל:* {regions}\n\nתקבל התראות מבצעים עבור אזורים אלו\\.\nהשתמש ב-/deals לצפייה במבצעים הנוכחיים\\!",
        "regions_start_first": "אנא השתמש ב-/start תחילה.",
        "regions_done_btn": "✅ סיום",
        # Deals
        "deals_no_regions": "⚠️ לא בחרת אזורים עדיין.\nהשתמש ב-/regions לבחירת אזורי PSN שלך תחילה!",
        "deals_fetching": "🔍 מושך מבצעים עדכניים...",
        "deals_header": "<b>🎮 מבצעי פלייסטיישן 🎮</b>\n",
        "deals_new_lowest": " 🔥 <b>שפל חדש!</b>",
        "deals_lowest": " ⭐ <b>הכי זול</b>",
        "deals_ps_store": "PS Store",
        "deals_show_more": "📄 הצג עוד",
        "deals_none": "❌ אין מבצעים כרגע. בדוק מאוחר יותר!",
        "deals_session_expired": "⚠️ הסשן פג תוקף. השתמש ב-/deals שוב.",
        "deals_loading_more": "טוען עוד מבצעים...",
        # Wishlist
        "watch_usage": "ℹ️ *שימוש:* `/watch שם משחק`\nדוגמה: `/watch God of War Ragnarok`",
        "watch_already": "ℹ️ *{title}* כבר ברשימת המשאלות שלך\\!",
        "watch_added": "✅ *{title}* נוסף לרשימת המשאלות\\!\nתקבל התראה כשהמשחק יעמוד למכירה\\.",
        "unwatch_usage": "ℹ️ *שימוש:* `/unwatch שם משחק` או `/unwatch <מספר>`\nדוגמה: `/unwatch God of War` או `/unwatch 1`",
        "unwatch_invalid_num": "⚠️ מספר לא תקין\\. השתמש ב-`/watchlist` לצפייה במשחקים\\.",
        "unwatch_removed": "❌ *{title}* הוסר מרשימת המשאלות\\.",
        "unwatch_not_found": "⚠️ *{title}* אינו ברשימת המשאלות שלך\\.",
        "watchlist_empty": "📋 *רשימת המשאלות שלך ריקה\\.*\nהשתמש ב-`/watch שם משחק` להתחלת מעקב\\!",
        "watchlist_header": "📋 *רשימת המשאלות שלך:*\n",
        "watchlist_count": "📦 {n} משחק/ים במעקב",
        "watchlist_tip": "ℹ️ השתמש ב-`/unwatch <מספר>` או `/unwatch <שם משחק>` להסרה",
        # Search
        "search_usage": "שימוש: /search <שם משחק>\nדוגמה: /search Spider-Man",
        "search_searching": "🔍 מחפש '{query}'...",
        "search_reply_num": "\n\n📝 שלח <b>מספר</b> לפרטים.\n🌐 לא מצאת את המשחק? שלח <b>0</b> לחיפוש אונליין.",
        "search_session_expired": "⚠️ הסשן פג תוקף. השתמש ב-/search שוב.",
        "search_invalid_pick": "⚠️ אנא שלח מספר, או /cancel לביטול.",
        "search_pick_range": "⚠️ בחר מספר בין 1 ל-{max}, או 0 לחיפוש אונליין.",
        "search_pick_range_online": "⚠️ בחר מספר בין 1 ל-{max}.",
        "search_online": "🌐 מחפש אונליין...",
        "search_online_failed": "❌ החיפוש האונליין נכשל. נסה שוב מאוחר יותר.",
        "search_no_results": "❌ לא נמצאו משחקים התואמים '{query}' ב-PSPrices.",
        "search_online_found": "🌐 נמצאו {n} משחקים ב-PSPrices:\n",
        "search_online_pick": "\n📝 שלח <b>מספר</b> לפרטים, או /cancel לביטול.",
        "search_cancelled": "🔍 החיפוש בוטל.",
        "search_no_price": "💰 אין נתוני מחיר",
        "search_no_price_available": "💰 אין נתוני מחיר זמינים.",
        "search_watch_tip": "💡 השתמש ב-<code>/watch {title}</code> למעקב אחרי המשחק!",
        "search_found": "🎮 נמצאו {n} תוצאות:",
        "search_more": "\n<i>...יש עוד תוצאות. שלח <b>0</b> לחיפוש אונליין לכל התוצאות.</i>",
        "search_no_active_deal": "💰 אין מבצע פעיל",
        "search_free": "💰 חינם",
        # Alerts
        "alert_usage": (
            "ℹ️ *שימוש:*\n"
            "`/alert שם משחק 100` \\- התראה כשהמחיר יירד מתחת ל\\-100\n"
            "`/alert שם משחק 50%` \\- התראה כשההנחה תגיע ל\\-50%\n\n"
            "דוגמה:\n"
            "`/alert God of War Ragnarok 100`\n"
            "`/alert Elden Ring 50%`"
        ),
        "alert_invalid_discount": "⚠️ ההנחה חייבת להיות בין 1% ל-99%.",
        "alert_invalid_discount_fmt": "⚠️ פורמט הנחה לא תקין\\. השתמש למשל ב-`50%`",
        "alert_price_positive": "⚠️ המחיר חייב להיות גדול מ-0.",
        "alert_invalid_target": "⚠️ ערך לא תקין\\. השתמש במחיר \\(למשל `100`\\) או הנחה \\(למשל `50%`\\)",
        "alert_no_regions": "⚠️ לא בחרת אזורים עדיין.\nהשתמש ב-/regions לבחירת אזורי PSN תחילה!",
        "alert_no_game": "⚠️ לא נמצא משחק התואם *{game}*\\.\nנסה מונח חיפוש אחר או השתמש ב-/search תחילה\\.",
        "alert_already_set": "ℹ️ כבר הגדרת התראות פעילות עבור *{game}* בכל האזורים שלך\\.",
        "alert_set": (
            "🔔 *התראת מחיר הוגדרה\\!*\n\n"
            "🎮 {game}\n"
            "🎯 יעד: {target}\n"
            "📍 אזורים: {regions}\n\n"
            "תקבל התראה כשהתנאים יתמלאו\\!"
        ),
        "alert_target_discount": "הנחה של {pct}%",
        "alert_target_price": "מחיר מתחת ל-{price}",
        "alerts_none": "🔔 *אין התראות מחיר פעילות\\.*\nהשתמש ב-`/alert שם משחק 100` להגדרת אחת\\!",
        "alerts_header": "🔔 *התראות המחיר שלך:*\n",
        "alerts_count": "📊 {n} התראה/ות פעילות",
        "alerts_tip": "השתמש ב-`/delalert <מספר>` להסרת התראה\\.",
        "alerts_below": "מתחת ל-{sym}{price}",
        "alerts_discount": "הנחה של {pct}%",
        "delalert_usage": "ℹ️ *שימוש:* `/delalert 1`\nהשתמש ב-/alerts לצפייה במספרי ההתראות\\.",
        "delalert_invalid": "⚠️ אנא ספק מספר תקין\\.",
        "delalert_out_of_range": "⚠️ מספר התראה לא תקין\\. יש לך {n} התראות פעילות\\.\nהשתמש ב-/alerts לצפייה ברשימה\\.",
        "delalert_removed": "❌ ההתראה עבור *{game}* הוסרה\\.",
        # Compare
        "compare_usage": "ℹ️ שימוש: /compare שם משחק\nדוגמה: /compare God of War Ragnarok",
        "compare_no_games": "⚠️ לא נמצאו משחקים עבור '{query}'.\nנסה מונח חיפוש אחר.",
        "compare_no_deals": "⚠️ לא נמצאו מבצעים עבור '{query}'.\nמשחקים אלו אינם במבצע כרגע.",
        "compare_cheapest": " 👍 <b>הכי זול</b>",
        "compare_no_deal": "<i>אין מבצע זמין</i>",
        "compare_best": "💡 הכי זול: {flag} {name}",
        "compare_buy": "🛒 <a href='{url}'>קנה ב-PS Store</a>",
        "compare_header": "🎮 <b>השוואת מחירים עבור '{query}'</b>\n",
        # Settings
        "settings_header": "⚙️ *ההגדרות שלך*\n",
        "settings_subscription": "*מנוי:* {status}",
        "settings_active": "✅ פעיל",
        "settings_inactive": "❌ לא פעיל",
        "settings_regions": "*אזורים:* {regions}",
        "settings_regions_none": "אין",
        "settings_watchlist": "*רשימת משאלות:* {n} משחקים",
        "settings_actions": "*פעולות מהירות:*",
        "settings_change_regions": "/regions \\- שנה אזורים",
        "settings_view_watchlist": "/watchlist \\- צפה ברשימת המשאלות",
        "settings_subscribe": "/subscribe \\- קבל התראות פרימיום",
        "settings_status": "/status \\- בדוק מנוי",
        "settings_language": "/language \\- שנה שפה",
        # Subscribe / status
        "subscribe_msg": (
            "🎮 <b>PS Deal Hunter — מנוי פרימיום</b>\n\n"
            "קבל התראות מבצעים בזמן אמת, עדכוני ירידת מחירים "
            "והתראות גיפט קארד ישירות לצ'אט שלך.\n\n"
            "☕ הרשם כאן: {url}\n\n"
            "לאחר התשלום, הפעל /paid לעדכון!"
        ),
        "subscribe_already_active": "✅ יש לך מנוי פעיל כבר!",
        "subscribe_pending": "⏳ התשלום שלך כבר ממתין לאישור.",
        "subscribe_got_it": "קיבלנו! תאושר בקרוב.",
        "subscribe_approved_msg": "אתה עכשיו מנוי! ההתראות פעילות. 🎉",
        "subscribe_revoked_msg": "המנוי שלך הסתיים.",
        "subscribe_active": "✅ המנוי שלך פעיל.",
        "subscribe_not_active": "❌ אין לך מנוי פעיל. השתמש ב-/subscribe להתחלה.",
        "subscribe_cancelled": (
            "המנוי שלך בוטל.\n\n"
            "⚠️ כדי לעצור תשלומים עתידיים, בטל גם ב-Buy Me a Coffee:\n"
            "{url}\n"
            "עבור לחשבון שלך ← Manage Memberships ← Cancel\n\n"
            "השתמש ב-/subscribe אם תרצה לחזור."
        ),
        "subscribe_not_active_cancel": "❌ אין לך מנוי פעיל.",
        # Follow
        "follow_on": (
            "🔔 <b>נרשמת להתראות גיפט קארד!</b>\n\n"
            "תקבל התראה ברגע שגיפט קארד PlayStation של Amazon יהיה זמין.\n\n"
            "השתמש ב-/follow שוב לביטול."
        ),
        "follow_off": (
            "🔕 <b>בוטלה ההרשמה להתראות גיפט קארד.</b>\n\n"
            "השתמש ב-/follow להרשמה מחדש."
        ),
        # Donate
        "donate_msg": (
            "💝 תמוך ב-PS5 Deal Hunter!\n\n"
            "הבוט חינמי לכולם. אם הוא עזר לך\n"
            "למצוא מבצע מעולה, שקול לתמוך בפיתוח:\n\n"
            "☕ קנה לי קפה:\n"
            "   https://buymeacoffee.com/oshri1997\n\n"
            "כל תרומה עוזרת להמשיך את הבוט\n"
            "ולממן פיצ'רים חדשים! 🙏"
        ),
        # Premium
        "premium_msg": (
            "🔔 <b>PS Deal Hunter — פרימיום</b>\n\n"
            "<b>מנויים מקבלים:</b>\n"
            "• ⭐ התראות מבצעים יומיות לצ'אט\n"
            "• ⭐ עדכוני ירידת מחירים\n"
            "• ⭐ התראות גיפט קארד (/follow)\n"
            "• ⭐ השוואת מחירים בין אזורים (/compare)\n"
            "• ⭐ התראות מחיר (/alert)\n\n"
            "<b>חינם לכולם:</b>\n"
            "• 🔍 חיפוש ועיון במבצעים\n"
            "• 📋 רשימת משאלות\n"
            "• 🎮 בדיקת זמינות גיפט קארד\n\n"
            "השתמש ב-/subscribe להתחלה!\n"
            "השתמש ב-/status לבדיקת המנוי שלך."
        ),
        # require_subscriber
        "subscriber_only": "🔒 פיצ'ר זה זמין למנויים בלבד.\nהשתמש ב-/subscribe להתחלה.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return the translated string for `lang` and `key`, with optional format kwargs."""
    lang_strings = STRINGS.get(lang, STRINGS["en"])
    text = lang_strings.get(key) or STRINGS["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
