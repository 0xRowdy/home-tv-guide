"""Resolve lineup.txt against Smartiflix's stream list and the epgshare01 guide ids.

Usage: python3 resolve.py <tvs/NAME.env> <out.tsv>
Reads that TV's Smartiflix login, downloads its stream list and the epgshare01
US guide channel lists, then writes <out.tsv>
(number, group, name, stream_id, epg_id, logo) and prints a review table.
Stream IDs can differ between accounts, so each TV gets its own file.
"""
import gzip, json, os, re, sys, tempfile, urllib.request
import xml.etree.ElementTree as ET

GUIDES = ["https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
          "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz"]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "TiviMate/5.3.3"})
    return urllib.request.urlopen(req, timeout=300)

def fetch_streams(tmp, env_path):
    env = dict(l.strip().split("=", 1) for l in open(env_path) if "=" in l)
    url = f'{env["XTREAM_SERVER"]}/player_api.php?username={env["XTREAM_USER"]}&password={env["XTREAM_PASS"]}&action=get_live_streams'
    path = os.path.join(tmp, "streams.json")
    with get(url) as r, open(path, "wb") as f:
        f.write(r.read())
    return path

def fetch_guide_ids(url, tmp):
    """Write id|display-name|programme-count lines for one epgshare01 file."""
    gz = os.path.join(tmp, "guide.xml.gz")
    with get(url) as r, open(gz, "wb") as f:
        f.write(r.read())
    names, cnt = {}, {}
    for _, el in ET.iterparse(gzip.open(gz), events=("end",)):
        if el.tag == "channel":
            names[el.get("id")] = el.findtext("display-name") or ""
        elif el.tag == "programme":
            cnt[el.get("channel")] = cnt.get(el.get("channel"), 0) + 1
        el.clear()
    path = os.path.join(tmp, url.rsplit("/", 1)[1] + ".ids")
    with open(path, "w", encoding="utf-8") as f:
        for k, v in names.items():
            f.write(f"{k}|{v.replace('|', ' ')}|{cnt.get(k, 0)}\n")
    return path

def norm(s):
    s = s.lower().replace("&", " and ").replace("+", " plus ")
    s = re.sub(r"\.(us2|us_locals1|us_sports1|us)$", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).split()

BAD = {"pacific", "west", "alternate", "alt", "español", "espanol", "spanish", "overflow",
       "stream", "streaming", "outer", "market", "en", "sd", "zone", "plus", "latino", "satellite"}

def load_ids(path):
    out = []
    for line in open(path, encoding="utf-8"):
        cid, name, cnt = line.rstrip("\n").rsplit("|", 2)
        if int(cnt) > 0:
            out.append((cid, name))
    return out

def best_epg(hint, ids):
    if not hint:
        return None, []
    if re.fullmatch(r"K[A-Z]{3}-(DT|LD)", hint):
        return f"{hint}.us_locals1", []
    h = norm(hint)
    cands = []
    for cid, name in ids:
        toks = norm(cid)
        if all(t in toks for t in h):
            extra = [t for t in toks if t not in h]
            penalty = sum(3 for t in extra if t in BAD and t not in h) + len(extra)
            cands.append((penalty, cid))
    cands.sort()
    return (cands[0][1] if cands else None), [c for _, c in cands[1:4]]

def main(env_path, out_path):
    with tempfile.TemporaryDirectory() as tmp:
        streams = json.load(open(fetch_streams(tmp, env_path), encoding="utf-8"))
        ids = [i for url in GUIDES for i in load_ids(fetch_guide_ids(url, tmp))]
    by_name = {}
    for s in streams:
        by_name.setdefault(s["name"], []).append(s)
    rows, problems = [], 0
    for line in open("lineup.txt", encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.rstrip("\n").split("|")]
        num, group, name, sname, hint = parts[:5]
        logo_override = parts[5] if len(parts) > 5 else ""
        cat = None
        if "@" in sname:
            sname, cat = sname.rsplit("@", 1)
        matches = [s for s in by_name.get(sname, []) if cat is None or s["category_id"] == cat]
        sid = matches[0]["stream_id"] if matches else None
        logo = logo_override or (matches[0].get("stream_icon", "") if matches else "")
        epg, alts = best_epg(hint, ids)
        flag = []
        if not sid: flag.append("NO STREAM")
        if len(matches) > 1: flag.append(f"{len(matches)} same-name streams")
        if hint and not epg: flag.append("NO GUIDE")
        problems += any(f.startswith("NO ") for f in flag)
        rows.append((num, group, name, sid, epg or "", logo))
        print(f"{num:>4} {name[:26]:26} {str(sid):>8}  {(epg or '-')[:44]:44} {' / '.join(flag)}  {'alt: ' + ', '.join(alts) if alts and not flag else ''}")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print(f"\n{len(rows)} channels, {problems} with problems")
    missing = [r for r in rows if not r[3]]
    if missing:
        print(f"WARNING: {len(missing)} channels not found on Smartiflix (left out of the playlist): "
              + ", ".join(r[2] for r in missing))

if __name__ == "__main__":
    main(*sys.argv[1:3])
