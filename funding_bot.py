import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL = "karthikkattera8688@gmail.com"
PASSWORD = "uugn mvbr xqpb fcqt"

RSS_FEEDS = [
    "https://inc42.com/buzz/feed/",
    "https://yourstory.com/tag/funding/feed",
    "https://www.vccircle.com/tag/funding/feed",
]

AMOUNT_PATTERN = re.compile(
    r"(\$ ?\d+\.?\d*\s?(million|billion|m|bn)?|₹ ?\d+\.?\d*\s?(crore|lakh)?)",
    re.IGNORECASE,
)

FUNDING_WORDS = ["raise", "raised", "raises", "funding", "secures", "bags"]


def is_funding_title(title):
    t = title.lower()
    return any(word in t for word in FUNDING_WORDS)


def extract_company(title):
    return title.split("raises")[0].split("raised")[0][:60].strip()


def extract_amount(text):
    m = AMOUNT_PATTERN.search(text)
    return m.group(0) if m else "Not found"


def get_description(soup):
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)
    return text[:200]


def extract_article(entry):
    title = entry.title

    if not is_funding_title(title):
        return None

    try:
        r = requests.get(entry.link, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "lxml")

        description = get_description(soup)
        amount = extract_amount(description)
        company = extract_company(title)

        linkedin_search = f"https://www.linkedin.com/search/results/all/?keywords={company}%20founder"

        return {
            "company_name": company,
            "amount_raised": amount,
            "two_line_description": description,
            "founder_linkedin": linkedin_search,
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

    return results[:20]


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
            "company_name": "No funding news found",
            "amount_raised": "-",
            "two_line_description": "-",
            "founder_linkedin": "-",
            "link": "-"
        }]

    df = pd.DataFrame(data)
    send_email(df)
    print("Email sent successfully!")


if __name__ == "__main__":
    main()
