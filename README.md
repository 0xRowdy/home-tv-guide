# Home TV guide

A small TV guide (XMLTV) for a Denver-focused, cable-style channel lineup.

- `lineup.txt`: the channel lineup (number, group, name, source stream, guide hint)
- `resolve.py`: matches the lineup to stream IDs and guide channel IDs and writes `lineup_resolved.tsv`
- `build_epg.py`: builds `epg.xml.gz` from the free [epgshare01](https://epgshare01.online) US guides, keeping only lineup channels
- `build_m3u.py`: writes the playlist locally from a git-ignored `.env` (never committed)
- `update_tv.sh`: re-matches the lineup, rebuilds the playlist, copies it to the TV, and pushes lineup changes

GitHub Actions rebuilds the guide twice a day and publishes it to
https://0xrowdy.github.io/home-tv-guide/epg.xml.gz
