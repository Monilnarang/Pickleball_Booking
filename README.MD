# 🏓 UCI Pickleball Booking Bot

This bot automates court bookings on the [UCI Campus Recreation website](https://my.campusrec.uci.edu/booking) using Selenium, Chrome, and Docker.

## ✅ Features

- Logs in with your **UCInetID and password**
- Handles **Duo 2FA** and clicks "Yes, this is my device"
- Checks all facilities for **7–10 PM** booking slots
- Automatically clicks the **first available slot**
- Can be run headlessly in Docker for nightly automation

---

## 🚀 Setup Instructions

### 1. Clone and Prepare Environment

Create `.env` and update with your credentials:

```env
UCI_ID=your_ucinetid
UCI_PASSWORD=your_password
```


### Setting Up cron
Using Crontab to run the script at 12:00 AM every day:
To update:
```
crontab -l > ~/Desktop/my_crontab.txt
```
make changes
```
crontab ~/Desktop/my_crontab.txt
```

View crons
```
crontab -l
```
