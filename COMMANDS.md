# Bot Commands - PS5 Deal Hunter

> All features are free during beta!

## 🎮 User Commands

### `/start`
Welcome message and bot introduction

### `/help`
Show all available commands

### `/regions`
Select regions to track deals (IL, US, IN)

### `/deals`
View 10 newest deals per region
- Ordered by latest first
- Includes PS Store links

### `/watch <game>`
Add game to wishlist
- You'll get notified when it goes on sale

### `/unwatch <game>`
Remove game from wishlist

### `/watchlist`
View your tracked games

### `/compare <game>`
Compare prices across all regions

### `/alert <game> <price|discount%>`
Set a price alert for a specific game
- `/alert God of War 100` - Alert when price drops below 100
- `/alert Elden Ring 50%` - Alert when discount reaches 50%
- Alerts are created for all your subscribed regions

### `/alerts`
View your active price alerts

### `/delalert <number>`
Delete a price alert by its list number

### `/search <query>`
Search for games in the database

### `/settings`
View your bot settings

### `/premium`
Info about premium features (coming soon)

### `/donate`
Support the bot development

### `/support`
Same as /donate

---

## 🔧 Admin Commands

### `/scrape_now`
Trigger immediate scrape (10 pages per region)

### `/scrape_full`
Trigger full scrape (50 pages per region)

### `/scrape_psp`
Trigger PSPrices scrape

### `/check_amazon`
Check PlayStation gift card availability on Amazon India

---

## 📊 Command Summary

| Command | Access | Description |
|---------|--------|-------------|
| `/start` | Everyone | Welcome message |
| `/help` | Everyone | Show commands |
| `/regions` | Everyone | Select regions |
| `/deals` | Everyone | View deals |
| `/watch` | Everyone | Add to wishlist |
| `/unwatch` | Everyone | Remove from wishlist |
| `/watchlist` | Everyone | View watchlist |
| `/compare` | Everyone | Compare prices |
| `/alert` | Everyone | Set price alert |
| `/alerts` | Everyone | View alerts |
| `/delalert` | Everyone | Delete alert |
| `/search` | Everyone | Search games |
| `/settings` | Everyone | View settings |
| `/premium` | Everyone | Premium info |
| `/donate` | Everyone | Support the bot |
| `/support` | Everyone | Support the bot |
| `/scrape_now` | Admin | Quick scrape |
| `/scrape_full` | Admin | Full scrape |
| `/scrape_psp` | Admin | PSPrices scrape |
| `/check_amazon` | Admin | Check gift card |

---

## 📅 Automatic Schedule

- **Daily scrape:** 02:00 UTC (5 pages per region)
- **Amazon check:** Every 3 hours
- **Price alerts check:** After each scrape
- **Cleanup:** 03:00 UTC (expired deals)

---

## 🎮 Amazon Gift Card Monitor

The bot automatically checks Amazon India PlayStation gift card availability every 3 hours.

**Product:** PlayStation Gift Card
**URL:** https://www.amazon.in/Playstation-Gift-Redeemable-Flat-Cashback/dp/B0C1H473H8

**Manual Check:** Use `/check_amazon` command
