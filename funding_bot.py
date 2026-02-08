import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL = "katherakarthik7@gmail.com"
PASSWORD = "YOUR_GMAIL_APP_PASSWORD"

RSS_FEEDS = [
    "https://inc42.com/buzz/feed/",
    "https://yourstory.com/tag/funding/feed",
    "https://www.vccircle.com/tag/funding/feed",
    "https://economictimes.indiatimes.com/small-biz/startups/funding/rssfeeds/89409759.cms",
]

FUNDING_PATTERN = re.compile(
    r"(raises|raised|bags|secures|gets|closes).*?(funding|round|investment)",
    re.IGNORECASE,
)

AMOUNT_PATTERN = re.compile(
    r"(\$ ?\d+\.?\d*\s?(million|billion|m|bn)?|₹ ?\d+\.?\d*\s?(crore|lakh)?)",
    re.IGNORECASE,
)

INVESTOR_PATTERN = re.compile(
    r"(from|led by|backed by)\s([A-Z][A-Za-z0-9 ,&\-]+)",
    re.IGNORECASE,
)


def extract_startup(title):
    words = title.split()
    return " ".join(words[:3])


def extract_amount(text):
    m = AMOUNT_PATTERN.search(text)
    return m.group(0) if m else "Not found"


def extract_investor(text):
    m = INVESTOR_PATTERN.search(text)
    return m.group(2) if m else "Not found"


def extract_article(entry):
    title = entry.title

    if not FUNDING_PATTERN.search(title):
        return None

    try:
        r = requests.get(entry.link, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "lxml")

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)

        startup = extract_startup(title)
        amount = extract_amount(text)
        investor = extract_investor(text)

        return {
            "startup_name": startup,
            "two_line_description": text[:200],
            "who_invested": investor,
            "how_much_invested": amount,
            "founders_linkedin": f"https://www.linkedin.com/search/results/all/?keywords={startup}%20founder",
            "link": entry.link
        }

    except:
        return None


def collect_news():
    results = []
    seen = set()

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:10]:
            if entry.link in seen:
                continue

            data = extract_article(entry)

            if data:
                results.append(data)
                seen.add(entry.link)

    return results


def send_email(df):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Startup Funding Report"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    html = df.to_html(index=False, escape=False)
    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, EMAIL, msg.as_string())
    server.quit()


def main():
    data = collect_news()

    if not data:
        data = [{
            "startup_name": "No funding news detected",
            "two_line_description": "-",
            "who_invested": "-",
            "how_much_invested": "-",
            "founders_linkedin": "-",
            "link": "-"
        }]

    df = pd.DataFrame(data)
    send_email(df)
    print("Email sent successfully!")


if __name__ == "__main__":
    main()
