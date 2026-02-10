# 📈 Startup Funding Bot

Startup Funding Bot automatically collects **Indian startup funding news** and sends a daily email report.

It runs automatically using GitHub Actions and helps track which startups raised funding recently.

---

## 🚀 What This Bot Does

Every day, the bot:

1. Collects funding news from trusted startup news sources.
2. Detects articles where startups raised funding.
3. Extracts:
   - Startup/company name
   - Funding amount raised
   - Short company description
   - Founder LinkedIn search link (optional)
4. Sends a clean report to your email.

---

## 📬 Example Output

| Company | Amount Raised | Description | Founder LinkedIn |
|----------|--------------|-------------|------------------|
| StartupX | $10M | StartupX builds AI tools for retailers... | LinkedIn link |

Delivered daily via email.

---

## 🧠 Why This Project?

Startup funding news is scattered across many websites.  
This bot automates the process so founders, investors, and analysts can easily track funding activity.

This project is also useful as a:

- Data Engineering practice project
- Automation project
- Startup intelligence tool
- Resume/portfolio project

---

## ⚙️ How It Works

News Sources
↓
Funding Article Detection
↓
Information Extraction
↓
Email Report Generation
↓
Daily Email Sent



Automation is handled using **GitHub Actions**.

---

## 🗂 Project Structure


startup-funding-bot/
│
├── funding_bot.py # Main bot script
├── requirements.txt # Python dependencies
└── .github/workflows/
└── daily.yml # GitHub Actions workflow


---

## 🛠 Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/startup-funding-bot.git
cd startup-funding-bot


### 2. Install Dependencies
pip install -r requirements.txt


### 3. Configure Email

Edit funding_bot.py:

EMAIL = "your_email@gmail.com"
PASSWORD = "your_gmail_app_password"


Use a Gmail App Password, not your real password.

### 4. Run Locally
python funding_bot.py

### 5. Automate with GitHub Actions

Push code to GitHub.
The workflow runs automatically every day.

You can also manually run from:

GitHub → Actions → Run workflow


Dependencies

requests

feedparser

pandas

beautifulsoup4

lxml








Run Locally
python funding_bot.py



pip install -r requirements.txt
🔧 Customization Ideas
You can extend this project to:

Store funding data in database

Build funding analytics dashboard

Track investor activity

Send Slack/Telegram alerts

Create startup trend reports

🐞 Troubleshooting
No email received?
Check:

Spam folder

Gmail login permissions

GitHub Actions logs

📄 License

This project is open-source and free to use.




