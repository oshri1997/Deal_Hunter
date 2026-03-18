# 🎮 PS5 Deal Hunter Bot -HOT

Multi-region PlayStation deal notifications via Telegram.

## ✅ Project Statuss

All core components are implemented:

- ✅ Database layer (SQLAlchemy async models)
- ✅ Scraper (PSPrices.com integration)
- ✅ Bot handlers (all 7 commands)
- ✅ Notification engine
- ✅ Scheduler (APScheduler)
- ✅ Main entry point

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- PostgreSQL database
- Redis (optional, for caching)
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### 2. Installation

```bash
# Clone or navigate to project
cd ps-bot

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ps5deals
REDIS_URL=redis://localhost:6379/0
SCRAPE_INTERVAL_HOURS=3
LOG_LEVEL=INFO
```

### 4. Database Setup

The bot will automatically create tables on first run. Ensure PostgreSQL is running:

```bash
# Start PostgreSQL (example for Windows)
# Make sure PostgreSQL service is running

# Or use Docker
docker run --name ps5deals-db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres
```

### 5. Run the Bot

```bash
python main.py
```

You should see:

```
🚀 PS5 Deal Hunter Bot starting...
Scraping interval: 3 hours
Supported regions: IL, IN, US, GB, DE, FR, BR, JP, AU, RU
```

## 📱 Bot Commands

| Command           | Description                                           |
| ----------------- | ----------------------------------------------------- |
| `/start`          | Welcome message and setup                             |
| `/help`           | Show all commands                                     |
| `/regions`        | Select regions to track (Free: 2, Premium: unlimited) |
| `/deals`          | View current deals in your regions                    |
| `/watch <game>`   | Add game to wishlist (Free: 5, Premium: unlimited)    |
| `/unwatch <game>` | Remove game from wishlist                             |
| `/watchlist`      | View your tracked games                               |
| `/compare <game>` | Compare prices across regions (Premium only)          |
| `/settings`       | View your preferences                                 |
| `/premium`        | Upgrade to Premium                                    |

## 🏗️ Project Structure

```
ps-bot/
├── bot/
│   ├── handlers/          # Command handlers
│   │   ├── start.py       # /start, /help
│   │   ├── regions.py     # /regions
│   │   ├── deals.py       # /deals
│   │   ├── wishlist.py    # /watch, /unwatch, /watchlist
│   │   ├── compare.py     # /compare
│   │   ├── settings.py    # /settings
│   │   └── premium.py     # /premium
│   └── helpers.py         # Utility functions
├── database/
│   ├── models.py          # SQLAlchemy models
│   └── engine.py          # DB connection
├── scraper/
│   ├── psprices.py        # PSPrices scraper
│   └── manager.py         # Scraper coordinator
├── notification.py        # Notification engine
├── scheduler.py           # APScheduler jobs
├── config.py              # Configuration
├── main.py                # Entry point
└── requirements.txt       # Dependencies
```

## 🔧 Configuration Options

Edit `config.py` to customize:

- **Regions**: Add/remove supported PSN regions
- **Free tier limits**: Adjust max regions/wishlist for free users
- **Scraping interval**: Change how often deals are checked
- **Notification timing**: Set daily digest time
- **Premium pricing**: Configure subscription prices

## 📊 Database Models

- **User**: Telegram users and premium status
- **UserRegion**: User's subscribed regions
- **UserWishlist**: User's tracked games
- **Game**: Game catalog
- **Price**: Historical price data
- **ActiveDeal**: Current sales/discounts

## 🔄 How It Works

1. **Scheduler** triggers scraping every N hours
2. **Scraper** fetches deals from PSPrices.com for all regions
3. **Database** stores new/updated deals
4. **Notification Engine** matches deals to users:
   - Premium users get instant alerts
   - Free users get daily digest
   - Wishlist matches get priority notifications
5. **Bot** handles user commands and preferences

## 🎯 Next Steps

### Essential

- [ ] Test with real Telegram bot
- [ ] Verify database connections
- [ ] Test scraping for all regions
- [ ] Validate notification delivery

### Optional Enhancements

- [ ] Integrate Stripe for payments
- [ ] Add price history charts (matplotlib)
- [ ] Implement Redis caching
- [ ] Add admin commands
- [ ] Create web dashboard
- [ ] Add analytics/metrics

## 🐛 Troubleshooting

**Bot doesn't start:**

- Check `TELEGRAM_BOT_TOKEN` is set correctly
- Verify PostgreSQL is running
- Check logs for errors

**No deals appearing:**

- Wait for first scraping cycle (check `SCRAPE_INTERVAL_HOURS`)
- Verify PSPrices.com is accessible
- Check scraper logs

**Database errors:**

- Ensure PostgreSQL is running
- Verify `DATABASE_URL` format
- Check database permissions

## 📝 Development

Run in development mode with debug logging:

```bash
LOG_LEVEL=DEBUG python main.py
```

## 📄 License

MIT License - See LICENSE file

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

Built with ❤️ for PlayStation gamers worldwide 🎮
