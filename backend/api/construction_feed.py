"""Refresh construction notices for the local preview from official NCU sites."""

import json
import logging
import re
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Thread
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from .construction import BUILDINGS_FILE, build_name_index, refresh_lock
from .construction_store import ConstructionStore
from .crawl import API, DATA, HEADERS, URL as OGA_LIST

TAIPEI = timezone(timedelta(hours=8))
PHYSICS_LIST = "https://www.phy.ncu.edu.tw/"
SPORTS_LIST = "https://pe.ncu.edu.tw/category/11.html"
POLL_MINUTES = 30
TIMEOUT = 15
logger = logging.getLogger(__name__)

# Full-width punctuation is normalized before parsing. No range is inferred
# from isolated or reversed dates.
DAY = r"(?:(\d{3,4})[年/.-])?(\d{1,2})[月/.-](\d{1,2})(?:日|號)?"
DATE_RANGE = re.compile(
    rf"(?<![\d/]){DAY}(?:\s*\([^)]+\))?\s*(?:起)?\s*(?:至|到|~|–|—|-|、)\s*{DAY}(?!\d)"
)
COMPACT_RANGE = re.compile(r"(?<!\d)(\d{3})(\d{2})(\d{2})\s*[-~]\s*(?:(\d{3}))?(\d{2})(\d{2})(?!\d)")
START_DATE = re.compile(rf"(?<![\d/]){DAY}\s*起")
IMMEDIATE_END = re.compile(rf"即日起\s*至\s*{DAY}")


def normalize(text):
    return unicodedata.normalize("NFKC", text)


def plain_text(html):
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)


def as_date(year, month, day, default_year):
    year = int(year) if year else default_year
    if year < 1911:
        year += 1911
    return date(year, int(month), int(day))


def date_range(title, body, published):
    for value in (title, body):
        text = re.sub(r"\s+", "", normalize(value))
        match = COMPACT_RANGE.search(text) or DATE_RANGE.search(text)
        if match:
            y1, m1, d1, y2, m2, d2 = match.groups()
            try:
                start = as_date(y1, m1, d1, published.year)
                end = as_date(y2, m2, d2, start.year)
                if start <= end:
                    return start.isoformat(), end.isoformat()
            except ValueError:
                continue
        match = IMMEDIATE_END.search(text)
        if match:
            try:
                end = as_date(*match.groups(), published.year)
                if published <= end:
                    return published.isoformat(), end.isoformat()
            except ValueError:
                continue
    match = START_DATE.search(re.sub(r"\s+", "", normalize(title)))
    if match:
        try:
            return as_date(*match.groups(), published.year).isoformat(), None
        except ValueError:
            pass
    return None, None


def building_from_title(title, name_index):
    title = normalize(title).replace(" ", "").casefold()
    names = {name for name, ids in name_index.items() if len(ids) == 1 and len(name) >= 3}
    # The official physics notice uses the short name, and the map names the
    # same building 健雄館(科四館). Count it once if both forms appear.
    aliases = {"健雄館": "健雄館(科四館)"}
    matches = {aliases.get(name, name) for name in names | aliases.keys() if name in title}
    # "XX館旁" sports areas must not mark the adjacent building as under work.
    if any(term in title for term in ("球場", "停車場", "人行道", "步道")):
        return None
    return next(iter(matches)) if len(matches) == 1 else None


def official_record(identity, title, published, body, source, link, name_index):
    start, end = date_range(title, body, published)
    building = building_from_title(title, name_index)
    return {
        "Id": identity,
        "NewsTitle": title,
        "PublishDate": published.isoformat(),
        "source_name": source,
        "source_url": link,
        "announcement_type": "construction",
        "processing_status": "success",
        "location": {"building": building},
        "construction": {"start_date": start, "end_date": end},
        "needs_review": not (start and end and building),
    }


def get_document(url):
    request = Request(url, headers={"User-Agent": "NCU Campus Map/1.0"})
    with urlopen(request, timeout=TIMEOUT) as response:
        return BeautifulSoup(response.read(), "html.parser")


def from_general_affairs(name_index):
    request = Request(API, data=json.dumps(DATA).encode("utf-8"), headers=HEADERS)
    with urlopen(request, timeout=TIMEOUT) as response:
        entries = json.load(response)
    if not isinstance(entries, list) or any(
        not isinstance(item, dict) or not {"name", "uid", "publishStartDate"} <= item.keys()
        for item in entries
    ):
        raise ValueError("Unexpected NCU public announcement response")
    records = []
    for entry in entries:
        title = entry["name"]
        if "施工" not in title and "工程" not in title and "修繕" not in title:
            continue
        published = date.fromisoformat(entry["publishStartDate"])
        if published <= datetime.now(TAIPEI).date():
            records.append(official_record(
                entry["uid"], title, published, plain_text(entry.get("content")),
                "總務處營繕組", OGA_LIST, name_index,
            ))
    return records


def from_physics(name_index):
    document = get_document(PHYSICS_LIST)
    entries = document.select("a.item[rel=bookmark]")
    if not entries:
        raise ValueError("NCU physics notice list not found")
    records = {}
    for entry in entries:
        title_node = entry.select_one(".title")
        date_node = entry.select_one(".date")
        link = urljoin(PHYSICS_LIST, entry.get("href", ""))
        target = urlsplit(link)
        if not title_node or not date_node or target.scheme != "https" or target.netloc != urlsplit(PHYSICS_LIST).netloc:
            continue
        title = title_node.get_text(" ", strip=True)
        if "施工" not in title or link in records:
            continue
        published = date.fromisoformat(date_node.get_text(strip=True))
        # The dated announcement title is public and links to the department's original PDF.
        records[link] = official_record(
            link, title, published, "", "物理學系", link, name_index
        )
    return list(records.values())


def from_sports(name_index):
    document = get_document(SPORTS_LIST)
    entries = document.select('a[href*="/article/"]')
    if not entries:
        raise ValueError("NCU athletics notice list not found")
    records = {}
    for entry in entries:
        title = entry.get_text(" ", strip=True)
        if "施工" not in title and not ("工程" in title and "不開放" in title):
            continue
        path = urlsplit(entry.get("href", "")).path
        if not re.fullmatch(r"/article/\d+\.html", path):
            continue
        link = urljoin(SPORTS_LIST, path)
        if link in records:
            continue
        article = get_document(link)
        published_match = re.search(r"(\d{4}-\d{2}-\d{2})[ \d:]*發表此公告", article.get_text(" ", strip=True))
        heading = article.select_one("h1")
        content = article.select_one(".content.clearfix")
        if not published_match or not heading or not content:
            raise ValueError("NCU athletics article format changed")
        published = date.fromisoformat(published_match[1])
        records[link] = official_record(
            link, heading.get_text(" ", strip=True), published,
            content.get_text(" ", strip=True), "體育室場地組", link, name_index,
        )
    return list(records.values())


SOURCES = {
    "總務處營繕組": from_general_affairs,
    "物理學系": from_physics,
    "體育室場地組": from_sports,
}


class ConstructionFeed:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.store = ConstructionStore(cache_file.with_suffix(".sqlite3"))
        self.next_check = 0
        self.sources = self.store.read_sources()
        if self.sources:
            return
        try:
            self.sources = json.loads(cache_file.read_text(encoding="utf-8"))
            if not isinstance(self.sources, dict) or any(
                not isinstance(value, dict) or not isinstance(value.get("records", []), list)
                for value in self.sources.values()
            ):
                raise ValueError("Invalid local construction cache")
            self.store.save_sources(self.sources)
        except FileNotFoundError:
            self.sources = {}
        except (OSError, ValueError):
            logger.warning("Could not read local construction cache")
            self.sources = {}

    def snapshot(self):
        records, status = [], []
        sources = self.sources
        for name in SOURCES:
            data = sources.get(name, {})
            records.extend(data.get("records", []))
            status.append({
                "name": name,
                "checked_at": data.get("checked_at"),
                "updated_at": data.get("updated_at"),
                "status": data.get("status", "waiting"),
            })
        return records, {"interval_minutes": POLL_MINUTES, "sources": status}

    def refresh(self):
        names = build_name_index(json.loads(BUILDINGS_FILE.read_text(encoding="utf-8-sig"))["features"])
        updated = {}
        successful = 0
        for name, fetch in SOURCES.items():
            checked_at = datetime.now(TAIPEI).isoformat(timespec="seconds")
            try:
                records = fetch(names)
                successful += 1
                updated[name] = {
                    "status": "ready", "checked_at": checked_at,
                    "updated_at": checked_at, "records": records,
                }
            except (OSError, ValueError, KeyError, TypeError):
                logger.warning("Could not refresh construction source: %s", name, exc_info=True)
                updated[name] = {
                    **self.sources.get(name, {}),
                    "status": "error",
                    "checked_at": checked_at,
                }
        self.store.save_sources(updated)
        self.sources = updated
        self.next_check = time.monotonic() + POLL_MINUTES * 60
        if not successful:
            raise RuntimeError("All NCU construction sources are unavailable")
        return sum(len(source.get("records", [])) for source in updated.values())

    def run(self):
        while True:
            if time.monotonic() >= self.next_check and refresh_lock.acquire(blocking=False):
                try:
                    # A manual refresh may have finished while the lock was busy.
                    if time.monotonic() >= self.next_check:
                        self.refresh()
                except Exception:
                    self.next_check = time.monotonic() + POLL_MINUTES * 60
                    logger.exception("Scheduled construction update failed")
                finally:
                    refresh_lock.release()
            time.sleep(5)


def start_construction_feed(app):
    feed = ConstructionFeed(Path(app.instance_path) / "construction-live.json")
    app.extensions["construction_feed"] = feed
    Thread(target=feed.run, name="ncu-construction-feed", daemon=True).start()
