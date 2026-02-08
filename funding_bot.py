import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL = "karthikkattera8688@gmail.com"
PASSWORD = "uugn mvbr xqpb fcqt"

RSS_FEEDS = [
    "https://inc42.com/feed/",
    "https://yourstory.com/feed",
    "https://economictimes.indiatimes.com/small-biz/startups/rssfeeds/119240706.cms",
    "https://www.livemint.com/rss/startups",
    "https://www.vccircle.com/feed",
    "https://www.outlookbusiness.com/rss",
]

def extract_article(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")

        text = soup.get_text(" ", strip=True)

        if "raise" not in text.lower():
            return None

        title = soup.title.text if soup.title else "Unknown"

        return {
            "startup_name": title.split("raises")[0][:50],
            "two_line_description": text[:200],
            "who_invested": "Check article",
            "how_much_invested": "Mentioned in article",
            "founders_linkedin": "Search LinkedIn",
            "link": url
        }

    except:
        return None

def collect_news():
    results = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:5]:
            data = extract_article(entry.link)
            if data:
                results.append(data)

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
        print("No funding news today.")
        return

    df = pd.DataFrame(data)
    send_email(df)

    print("Email sent successfully!")

if __name__ == "__main__":
    main()
