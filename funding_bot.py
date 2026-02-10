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

AMOUNT_PATTERN = re.compile(
    r"(\$ ?\d+\.?\d*\s?(million|billion|mn|bn|m|b)?|₹ ?\d+\.?\d*\s?(crore|cr|lakh|l)?|rs\.? ?\d+\.?\d*\s?(crore|cr|lakh|l)?)",
    re.IGNORECASE,
)

FUNDING_WORDS = ["raise", "raised", "raises", "funding", "secures", "bags", "bagged"]


def is_funding_title(title: str) -> bool:
    t = title.lower()
    return any(word in t for word in FUNDING_WORDS)


def extract_company(title: str) -> str:
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
    m = AMOUNT_PATTERN.search(text_title)
    if m:
        return m.group(0).strip()
    m = AMOUNT_PATTERN.search(text_body)
    if m:
        return m.group(0).strip()
    return "Not found"


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_description_and_investors(soup: BeautifulSoup):
    """
    Use the first few <p> tags (intro) for summary and scan them for investors.
    """
    paragraphs = soup.find_all("p")

    # Take first 3–4 non-empty paragraphs as intro
    intro_paras = []
    for p in paragraphs:
        txt = clean_text(p.get_text(separator=" ", strip=True))
        if txt:
            intro_paras.append(txt)
        if len(intro_paras) >= 4:
            break

    full_intro = " ".join(intro_paras)
    if not full_intro:
        full_intro = "No description available."

    # Build 1–2 sentence summary
    sentences = re.split(r"(?<=[.!?])\s+", full_intro)
    summary = " ".join(sentences[:2])
    summary = summary[:400]

    # Try to extract investors from intro text
    investors = extract_investors(full_intro)

    return summary, investors


def extract_investors(text: str) -> str:
    """
    Very simple heuristic: capture text after 'led by', 'from', 'backed by', 'including', etc.
    This will not be perfect but usually gives decent 'who invested' info.
    """
    lower = text.lower()

    patterns = [
        r"led by ([^.]+)",
        r"from ([^.]+)",
        r"backed by ([^.]+)",
        r"including ([^.]+)",
        r"co-led by ([^.]+)",
    ]

    for pat in patterns:
        m = re.search(pat, lower)
        if m:
            # Grab the original text slice for nicer casing
            start, end = m.span(1)
            raw = text[start:end]
            return clean_text(raw)

    return "Not clearly specified"


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

        description, investors = get_description_and_investors(soup)
        amount = extract_amount(title, description)
        company = extract_company(title)

        query = urllib.parse.quote(f"{company} founder")
        linkedin_search = (
            f"https://www.linkedin.com/search/results/all/?keywords={query}"
        )

        return {
            "company_name": company,
            "amount_raised": amount,
            "who_invested": investors,
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

    df = df.copy()

    # Make founder_linkedin and link clickable
    df["founder_linkedin"] = df["founder_linkedin"].apply(
        lambda url: f'<a href="{url}">{url}</a>' if url.startswith("http") else url
    )
    df["link"] = df["link"].apply(
        lambda url: f'<a href="{url}">Article</a>' if url.startswith("http") else url
    )

    # Order columns nicely
    cols = [
        "company_name",
        "amount_raised",
        "who_invested",
        "two_line_description",
        "founder_linkedin",
        "link",
    ]
    df = df[cols]

    table_html = df.to_html(index=False, escape=False)

    # Wrap table in styled HTML
    html = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          font-family: Arial, sans-serif;
          font-size: 14px;
          color: #222;
        }}
        h2 {{
          color: #0b5394;
        }}
        table {{
          border-collapse: collapse;
          width: 100%;
        }}
        th, td {{
          border: 1px solid #ddd;
          padding: 8px;
          vertical-align: top;
        }}
        th {{
          background-color: #0b5394;
          color: #ffffff;
          text-align: left;
        }}
        tr:nth-child(even) {{
          background-color: #f9f9f9;
        }}
        tr:hover {{
          background-color: #f1f1f1;
        }}
        a {{
          color: #1155cc;
          text-decoration: none;
        }}
        a:hover {{
          text-decoration: underline;
        }}
      </style>
    </head>
    <body>
      <h2>Daily Startup Funding Report</h2>
      {table_html}
    </body>
    </html>
    """

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
                "who_invested": "-",
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
