#!/bin/zsh
# Re-match the lineup to Smartiflix, rebuild the Home TV playlist, and copy it to the TV.
# Run this after editing lineup.txt, or if channels stop playing (Smartiflix renumbered them).
# Needs: the Mac on the home Wi-Fi, and USB debugging still enabled on the TV.
set -e
cd "${0:A:h}"
TV=${TV:-192.168.68.56:5555}
GUIDE=https://0xrowdy.github.io/home-tv-guide/epg.xml.gz

python3 -I resolve.py
python3 -I build_m3u.py "$GUIDE"

adb connect "$TV" >/dev/null
adb -s "$TV" push out/home.m3u "/sdcard/Download/Home TV.m3u"
echo "Playlist copied. In TiviMate: Settings > Playlists > Home TV > Update playlist (or just restart TiviMate)."

if ! git diff --quiet -- lineup.txt lineup_resolved.tsv; then
  git add lineup.txt lineup_resolved.tsv
  git commit -qm "Update lineup"
  git push -q
  echo "Guide channel list updated on GitHub; the guide rebuilds in about a minute."
fi
