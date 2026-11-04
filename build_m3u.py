"""Write the Home TV playlist (out/home.m3u) from lineup_resolved.tsv.

The playlist contains your Smartiflix login inside each stream URL, so it is
written to out/ (git-ignored) and only ever copied straight to the TV.

Usage: python3 build_m3u.py [guide_url]
"""
import os, sys

def load_env(path=".env"):
    env = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v
    return env

def main(guide_url=""):
    env = load_env()
    base = f'{env["XTREAM_SERVER"]}/live/{env["XTREAM_USER"]}/{env["XTREAM_PASS"]}'
    os.makedirs("out", exist_ok=True)
    header = f'#EXTM3U url-tvg="{guide_url}"' if guide_url else "#EXTM3U"
    lines = [header]
    for row in open("lineup_resolved.tsv", encoding="utf-8"):
        num, group, name, sid, epg, logo = row.rstrip("\n").split("\t")
        if sid == "None":
            continue
        attrs = f'tvg-chno="{num}" tvg-id="{epg}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}"'
        lines += [f"#EXTINF:-1 {attrs},{name}", f"{base}/{sid}.ts"]
    with open("out/home.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote out/home.m3u with {(len(lines) - 1) // 2} channels")

if __name__ == "__main__":
    main(*sys.argv[1:2])
