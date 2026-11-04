"""Write one TV's Home TV playlist from its resolved lineup.

The playlist contains that TV's Smartiflix login inside each stream URL, so it is
written to out/ (git-ignored) and only ever copied straight to the TV.

Usage: python3 build_m3u.py <tvs/NAME.env> <resolved.tsv> <out.m3u> [guide_url]
"""
import os, sys

def load_env(path):
    env = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v
    return env

def main(env_path, resolved_path, out_path, guide_url=""):
    env = load_env(env_path)
    base = f'{env["XTREAM_SERVER"]}/live/{env["XTREAM_USER"]}/{env["XTREAM_PASS"]}'
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    header = f'#EXTM3U url-tvg="{guide_url}"' if guide_url else "#EXTM3U"
    lines = [header]
    for row in open(resolved_path, encoding="utf-8"):
        num, group, name, sid, epg, logo = row.rstrip("\n").split("\t")
        if sid == "None":
            continue
        attrs = f'tvg-chno="{num}" tvg-id="{epg}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}"'
        lines += [f"#EXTINF:-1 {attrs},{name}", f"{base}/{sid}.ts"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out_path} with {(len(lines) - 1) // 2} channels")

if __name__ == "__main__":
    main(*sys.argv[1:5])
