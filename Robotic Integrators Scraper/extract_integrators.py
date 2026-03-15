#!/usr/bin/env python3
"""
Extract integrator/company data from saved MHTML pages. Supports multiple
sources (FANUC, ABB, etc.); company is inferred from folder name or can be
extended via COMPANY_CONFIG.
"""

import csv
import email
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup


def load_html_from_mhtml(mhtml_path: Path) -> str:
    """Extract and decode HTML from an MHTML file."""
    with open(mhtml_path, "rb") as f:
        msg = email.message_from_binary_file(f)

    html_bytes = None
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html_bytes = part.get_payload(decode=True)
            break

    if html_bytes is None:
        raise ValueError("No text/html part found in MHTML file")

    html = html_bytes.decode("utf-8", errors="replace")
    return html


def normalize_html(html: str) -> str:
    """
    Remove newline characters so that search patterns (e.g. class="robot-item ")
    are not split across lines. Decode quoted-printable style =3D if still present.
    """
    # In case we're reading raw file and =3D wasn't decoded: replace =3D with =
    html = html.replace("=3D", "=")
    # Collapse all newlines so tags aren't split
    html = re.sub(r"\s*[\r\n]+\s*", " ", html)
    return html


def extract_integrators_fanuc(html: str) -> list[dict]:
    """Parse HTML and yield one dict per robot-item: name, address, website, email."""
    soup = BeautifulSoup(html, "html.parser")

    # Match div.robot-item (class may be "robot-item " or "robot-item")
    items = soup.find_all("div", class_=re.compile(r"robot-item\s*"))
    rows = []

    for div in items:
        details = div.find("div", class_=re.compile(r"robot-details"))
        if not details:
            continue

        # Name: first h3 in robot-details
        name_el = details.find("h3")
        name = (name_el.get_text(strip=True) or "").strip() if name_el else ""

        # Address: first h4 in robot-details (fix QP line-wrap e.g. "United Sta tes" -> "United States")
        address_el = details.find("h4")
        address = (address_el.get_text(strip=True) or "").strip() if address_el else ""
        address = re.sub(r"\bSta\s+tes\b", "States", address)

        website = ""
        email_addr = ""

        meta = details.find("div", class_=re.compile(r"robot-meta"))
        if meta:
            for a in meta.find_all("a", href=True):
                href = (a.get("href") or "").strip()
                if href.startswith("mailto:"):
                    email_addr = href[7:].strip()
                elif href.startswith("http") and "fanucamerica.com" not in href:
                    # "Visit our site" link
                    website = href

        rows.append({
            "name": name,
            "address": address,
            "website": website,
            "email": email_addr,
        })

    return rows


def extract_integrators_abb(html: str) -> list[dict]:
    """Parse ABB HTML: data-testid='companyWrapper' blocks; output name and address only."""
    soup = BeautifulSoup(html, "html.parser")
    wrappers = soup.find_all("div", attrs={"data-testid": "companyWrapper"})
    rows = []

    for wrapper in wrappers:
        name = ""
        name_el = wrapper.find("h2")
        if name_el:
            name = (name_el.get_text(strip=True) or "").strip()

        address = ""
        addr_div = wrapper.find("div", class_=re.compile(r"zchdv|sc-eByOUD"))
        if addr_div:
            lines = [d.get_text(strip=True) for d in addr_div.find_all("div") if d.get_text(strip=True)]
            address = ", ".join(lines)
            address = re.sub(r"\bSta\s+tes\b", "States", address)

        rows.append({"name": name, "address": address})

    return rows


def extract_integrators_kuka(html: str) -> list[dict]:
    """Parse KUKA HTML: div.mod-locationfinder__item blocks; name, address, website, email.
    Only includes entries for United States of America (filtered by data-country attribute
    so line-wrapped address text in the source does not cause misses).
    """
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("div", class_=re.compile(r"mod-locationfinder__item"))
    rows = []
    address_filter_country = "United States of America"

    for item in items:
        if address_filter_country not in (item.get("data-country") or ""):
            print(item.get("data-country"))
            continue

        name = ""
        name_el = item.find("h4")
        if name_el:
            name = (name_el.get_text(strip=True) or "").strip()

        address = ""
        loc_span = item.find("span", class_=re.compile(r"icon-location"))
        if loc_span:
            addr_block = loc_span.find_parent("div", class_=re.compile(r"item__col__iconText"))
            if addr_block:
                addr_text = addr_block.get_text(separator=" ", strip=True)
                address = " ".join(addr_text.split())
                # Fix address text broken by quoted-printable line wrap (e.g. "United Sta tes" -> "United States")
                address = re.sub(r"\bSta\s+tes\b", "States", address)

        website = ""
        email_addr = ""
        for a in item.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            if href.startswith("mailto:"):
                email_addr = href[7:].strip()
            elif href.startswith("http") and "kuka.com" not in href:
                if not website:
                    website = href

        rows.append({
            "name": name,
            "address": address,
            "website": website,
            "email": email_addr,
        })

    return rows


def extract_integrators_yaskawa(html: str) -> list[dict]:
    """Parse Yaskawa/Motoman HTML: div.partner-grid blocks. Only name and optional
    location (City, ST) are on the page; no website or email in the listing.
    """
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("div", class_=re.compile(r"partner-grid"))
    rows = []

    for item in items:
        name = ""
        heading = item.find("div", class_=re.compile(r"body-heading"))
        if heading:
            name_el = heading.find("h2")
            if name_el:
                a = name_el.find("a")
                name = (a.get_text(strip=True) if a else name_el.get_text(strip=True) or "").strip()

        address = ""
        if heading:
            small = heading.find("small")
            if small:
                address = (small.get_text(strip=True) or "").strip()

        rows.append({"name": name, "address": address})

    return rows


# Registry: company key (e.g. "fanuc", "abb") -> extract function and CSV config.
# Add new companies here; folder name should match "{Company} pages" (e.g. "FANUC pages").
COMPANY_CONFIG = {
    "fanuc": {
        "extract": extract_integrators_fanuc,
        "fieldnames": ["name", "address", "website", "email"],
        "dedupe_by_website": True,
    },
    "abb": {
        "extract": extract_integrators_abb,
        "fieldnames": ["name", "address"],
        "dedupe_by_website": False,
    },
    "kuka": {
        "extract": extract_integrators_kuka,
        "fieldnames": ["name", "address", "website", "email"],
        "dedupe_by_website": True,
    },
    "yaskawa": {
        "extract": extract_integrators_yaskawa,
        "fieldnames": ["name", "address"],
        "dedupe_by_website": False,
    },
}


def _company_from_folder(folder_path: Path) -> str:
    """Infer company key from folder name (e.g. 'FANUC pages' -> 'fanuc')."""
    name = (folder_path.name or "").strip()
    if not name:
        return "fanuc"
    # "FANUC pages" / "ABB pages" -> first word lowercased
    first = name.split()[0].lower() if name else "fanuc"
    return first


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    default_folder = script_dir / "Yaskawa pages"

    # Usage: [folder] [output_path] [company]
    # Company is inferred from folder name (e.g. "FANUC pages" -> fanuc) unless given.
    folder_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_folder
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    company_override = sys.argv[3].strip().lower() if len(sys.argv) > 3 else None

    if not folder_path.is_dir():
        print(f"Folder not found: {folder_path}", file=sys.stderr)
        sys.exit(1)

    company = company_override or _company_from_folder(folder_path)
    if company not in COMPANY_CONFIG:
        valid = ", ".join(sorted(COMPANY_CONFIG.keys()))
        print(f"Unknown company '{company}' (from folder '{folder_path.name}'). Valid: {valid}", file=sys.stderr)
        sys.exit(1)

    config = COMPANY_CONFIG[company]
    if output_path is None:
        output_path = script_dir / f"{company} integrators.csv"

    # Collect MHTML and HTML pages
    page_extensions = (".mhtml", ".html", ".htm")
    pages = sorted(
        f for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in page_extensions
    )

    if not pages:
        print(f"No .mhtml, .html, or .htm files in: {folder_path}", file=sys.stderr)
        sys.exit(1)

    extract_fn = config["extract"]
    fieldnames = config["fieldnames"]

    all_rows = []
    for i, page_path in enumerate(pages, 1):
        print(f"[{i}/{len(pages)}] Reading: {page_path.name}")
        try:
            html = load_html_from_mhtml(page_path) if page_path.suffix.lower() == ".mhtml" else page_path.read_text(encoding="utf-8", errors="replace")
            if page_path.suffix.lower() != ".mhtml":
                html = html.replace("=3D", "=")
            html = normalize_html(html)
            rows = extract_fn(html)
            all_rows.extend(rows)
            print(f"  -> {len(rows)} integrators")
        except Exception as e:
            print(f"  -> Skipped: {e}", file=sys.stderr)

    print(f"Total: {len(all_rows)} integrators")

    if config.get("dedupe_by_website"):
        deduped = {}
        for row in all_rows:
            website = (row.get("website") or "").strip().lower()
            if website and website not in deduped:
                deduped[website] = row
        all_rows = list(deduped.values())
        print(f"Total unique: {len(all_rows)} integrators")

    all_rows.sort(key=lambda x: x.get("name", ""))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)

    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
