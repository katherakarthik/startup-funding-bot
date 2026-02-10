import requests
import feedparser
import pandas as pd
from bs4 import BeautifulSoup
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.parse

EMAIL = "karthikkattera8688@gmail.com"
PASSWORD = "uugn mvbr xqpb fcqt"

RSS_FEEDS = [
    "https://inc42.com/buzz/feed/",
    "https://yourstory.com/tag/funding/feed",
    "https://www.vccircle.com/tag/funding/feed",
]

# Examples it should capture:
# "$35 million", "$35m", "35m", "$35 Mn", "₹200 crore", "Rs 200 crore"
AMOUNT_PATTERN = re.compile(
    r"(\$ ?\d+\.?\d*\s?(million|billion|mn|bn|m|b)?|₹ ?\d+\.?\d*\s?(crore|cr|lakh|l)?|rs\.? ?\d+\.?\d*\s?(crore|cr|lakh|l)?)",
    re.IGNORECASE,
)

FUNDING_WORDS = ["raise", "raised", "raises", "funding", "secures", "bags", "bagged"]


def is_funding_title(title: str) -> bool:
    t = title.lower()
    return any(word in t for word in FUNDING_WORDS)


def extract_company(title: str) -> str:
    """
    Try to cut off at common funding verbs:
    'Nvidia raises $35M Series A led by...' -> 'Nvidia'
    'Fintech startup XYZ bags funding from...' -> 'Fintech startup XYZ'
    """
    lower = title.lower()
    cut_words = [" raises", " raised", " bags", " bagged", " secures", " gets", " lands"]
    end = len(title)
    for w in cut_words:
        idx = lower.find(w)
        if idx != -1:
            end = idx
            break
    company = title[:end].strip(" :-–—")
    return company[:80].strip()


def extract_amount(text_title: str, text_body: str) -> str:
    """
    Look for amount first in the title, then in the body text.
    """
    m = AMOUNT_PATTERN.search(text_title)
    if m:
        return m.group(0).strip()
    m = AMOUNT_PATTERN.search(text_body)
    if m:
        return m.group(0).strip()
    return "Not found"


def get_description(soup: BeautifulSoup) -> str:
    """
    Collect paragraph text, then return 1–2 sentences as a concise summary.
    """
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return "No description available."

    # Split into sentences (simple heuristic)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:2])  # first two sentences
    # Keep it reasonably short
    return summary[:400]


def extract_article(entry):
    title = entry.title

    if not is_funding_title(title):
        return None

    try:
        r = requests.get(
            entry.link,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        description = get_description(soup)
        amount = extract_amount(title, description)
        company = extract_company(title)

        # Properly URL-encoded LinkedIn search (valid URL)
        query = urllib.parse.quote(f"{company} founder")
        linkedin_search = (
            f"https://www.linkedin.com/search/results/all/?keywords={query}"
        )

        return {
            "company_name": company,
            "amount_raised": amount,
            "two_line_description": description,
            "founder_linkedin": linkedin_search,
            "link": entry.link,
        }

    except Exception:
        return None


def collect_news():
    results = []
    seen = set()

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:10]:
            link = getattr(entry, "link", None)
            if not link or link in seen:
                continue

            data = extract_article(entry)
            if data:
                results.append(data)
                seen.add(link)

    return results[:20]


def send_email(df: pd.DataFrame):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Startup Funding Report"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    # Make founder_linkedin clickable and show it nicely
    df = df.copy()
    df["founder_linkedin"] = df["founder_linkedin"].apply(
        lambda url: f'<a href="{url}">{url}</a>' if url.startswith("http") else url
    )
    df["link"] = df["link"].apply(
        lambda url: f'<a href="{url}">Article</a>' if url.startswith("http") else url
    )

    html = df.to_html(index=False, escape=False)
    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, EMAIL, msg.as_string())
    server.quit()


def main():
    data = collect_news()

    if not data:
        data = [
            {
                "company_name": "No funding news found",
                "amount_raised": "-",
                "two_line_description": "-",
                "founder_linkedin": "-",
                "link": "-",
            }
        ]

    df = pd.DataFrame(data)
    send_email(df)
    print("Email sent successfully!")


if __name__ == "__main__":
    main()
