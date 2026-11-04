"""Resolve lineup.txt against Smartiflix's stream list and the epgshare01 guide ids.

Usage: python3 resolve.py <streams.json> <us2_ids.txt> <sports_ids.txt>
Writes lineup_resolved.tsv (number, group, name, stream_id, epg_id, logo) and prints a review table.
"""
import json, re, sys

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

def main(streams_path, us2_path, sports_path):
    streams = json.load(open(streams_path, encoding="utf-8"))
    by_name = {}
    for s in streams:
        by_name.setdefault(s["name"], []).append(s)
    ids = load_ids(us2_path) + load_ids(sports_path)
    rows, problems = [], 0
    for line in open("lineup.txt", encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        num, group, name, sname, hint = [p.strip() for p in line.rstrip("\n").split("|")]
        cat = None
        if "@" in sname:
            sname, cat = sname.rsplit("@", 1)
        matches = [s for s in by_name.get(sname, []) if cat is None or s["category_id"] == cat]
        sid = matches[0]["stream_id"] if matches else None
        logo = matches[0].get("stream_icon", "") if matches else ""
        epg, alts = best_epg(hint, ids)
        flag = []
        if not sid: flag.append("NO STREAM")
        if len(matches) > 1: flag.append(f"{len(matches)} same-name streams")
        if hint and not epg: flag.append("NO GUIDE")
        problems += bool(flag)
        rows.append((num, group, name, sid, epg or "", logo))
        print(f"{num:>4} {name[:26]:26} {str(sid):>8}  {(epg or '-')[:44]:44} {' / '.join(flag)}  {'alt: ' + ', '.join(alts) if alts and not flag else ''}")
    with open("lineup_resolved.tsv", "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print(f"\n{len(rows)} channels, {problems} with problems")

if __name__ == "__main__":
    main(*sys.argv[1:4])
