"""Build a small guide (XMLTV) for just the channels in the Home TV lineup.

Downloads the free epgshare01 US guides, keeps only the channels listed in
lineup_resolved.tsv, and writes site/epg.xml.gz. No credentials needed.

Usage: python3 build_epg.py [cache_dir]
"""
import datetime as dt
import gzip, os, sys, urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

SOURCES = [
    "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz",
]
KEEP_PAST = dt.timedelta(hours=6)  # so "what just aired" still shows

def load_lineup(path="lineup_resolved.tsv"):
    wanted = {}
    for line in open(path, encoding="utf-8"):
        num, group, name, sid, epg, logo = line.rstrip("\n").split("\t")
        if epg:
            wanted.setdefault(epg, (name, logo))
    return wanted

def fetch(url, cache_dir):
    path = os.path.join(cache_dir, url.rsplit("/", 1)[1])
    req = urllib.request.Request(url, headers={"User-Agent": "home-tv-epg/1.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return path

def parse_time(s):
    return dt.datetime.strptime(s, "%Y%m%d%H%M%S %z")

def main(cache_dir="cache"):
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs("site", exist_ok=True)
    wanted = load_lineup()
    cutoff = dt.datetime.now(dt.timezone.utc) - KEEP_PAST
    found, programmes = set(), 0
    out = gzip.open("site/epg.xml.gz", "wt", encoding="utf-8")
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="home-tv-epg">\n')
    for cid, (name, logo) in wanted.items():
        icon = f"<icon src={quoteattr(logo)}/>" if logo else ""
        out.write(f"<channel id={quoteattr(cid)}><display-name>{escape(name)}</display-name>{icon}</channel>\n")
    for url in SOURCES:
        path = fetch(url, cache_dir)
        for _, el in ET.iterparse(gzip.open(path), events=("end",)):
            if el.tag == "programme":
                cid = el.get("channel")
                if cid in wanted and parse_time(el.get("stop")) > cutoff:
                    found.add(cid)
                    programmes += 1
                    out.write(ET.tostring(el, encoding="unicode").strip() + "\n")
                el.clear()
            elif el.tag == "channel":
                el.clear()
        os.remove(path)
    out.write("</tv>\n")
    out.close()
    missing = sorted(set(wanted) - found)
    print(f"channels with guide: {len(found)}/{len(wanted)}, programmes: {programmes}")
    if missing:
        print("no programmes today for:", ", ".join(missing))
    if len(found) < 0.8 * len(wanted):
        sys.exit("guide coverage dropped below 80%, not publishing")

if __name__ == "__main__":
    main(*sys.argv[1:2])
