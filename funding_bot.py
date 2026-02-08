import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL = "karthikkattera8688@gmail.com"
PASSWORD = "uugn mvbr xqpb fcqt"

# Funding-focused feeds
RSS_FEEDS = [
    "https://inc42.com/buzz/feed/",
    "https://yourstory.com/tag/funding/feed",
    "https://www.vccircle.com/tag/funding/feed",
    "https://economictimes.indiatimes.com/small-biz/startups/funding/rssfeeds/89409759.cms",
]

FUNDING_KEYWORDS = [
    "raise", "raised", "raises",
    "funding", "investment",
    "seed", "series", "round",
    "backed", "capital"
]


def is_funding_article(text):
    text = text.lower()
    return any(word in text for word in FUNDING_KEYWORDS)


def extract_article(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "lxml")

        paragraphs = soup.find_all("p")
        article_text = " ".join(p.get_text() for p in paragraphs)

        if not is_funding_article(article_text):
            return None

        title = soup.title.text if soup.title else "Unknown Startup"

        return {
            "startup_name": title.split("|")[0][:60],
            "two_line_description": article_text[:220],
            "who_invested": "Mentioned in article",
            "how_much_invested": "Mentioned in article",
            "founders_linkedin": "Search LinkedIn",
            "link": url
        }

    except Exception as e:
        print("Error reading:", url)
        return None


def collect_news():
    results = []
    seen = set()

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:10]:
            if entry.link in seen:
                continue

            data = extract_article(entry.link)

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
            "two_line_description": "Feeds returned no funding articles.",
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
