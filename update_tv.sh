#!/bin/zsh
# Rebuild the Home TV playlist for each TV and copy it over.
#   ./update_tv.sh              all TVs in tvs/
#   ./update_tv.sh downstairs   just one
# Each TV has tvs/NAME.env (git-ignored) with its Smartiflix login and address:
#   XTREAM_SERVER=http://...  XTREAM_USER=...  XTREAM_PASS=...  TV=192.168.x.x:5555
# Run after editing lineup.txt, or if channels stop playing (Smartiflix renumbered them).
# The Mac must be on the same network as the TV, and USB debugging must stay on.
cd "${0:A:h}"
setopt pipefail
GUIDE=https://0xrowdy.github.io/home-tv-guide/epg.xml.gz
PRIMARY=upstairs   # its lineup is what the shared guide on GitHub is built from

names=("$@"); (( $#names )) || names=(tvs/*.env(:t:r))
failed=()
for name in $names; do
  env=tvs/$name.env
  [[ -f $env ]] || { echo "no $env"; failed+=$name; continue; }
  echo "== $name"
  python3 -I resolve.py $env out/$name.tsv | tail -2 || { failed+=$name; continue; }
  python3 -I build_m3u.py $env out/$name.tsv out/$name.m3u $GUIDE
  tv=$(grep '^TV=' $env | cut -d= -f2)
  adb connect $tv >/dev/null 2>&1
  if [[ $(adb -s $tv get-state 2>/dev/null) == device ]] && adb -s $tv push out/$name.m3u "/sdcard/Download/Home TV.m3u" >/dev/null; then
    echo "copied to $tv. TiviMate picks it up on next start (or Settings > Playlists > Home TV > Update playlist)."
  else
    echo "could not reach $tv (TV off, different network, or USB debugging off)"; failed+=$name
  fi
done

if [[ -f out/$PRIMARY.tsv ]] && ! cmp -s out/$PRIMARY.tsv lineup_resolved.tsv; then
  cp out/$PRIMARY.tsv lineup_resolved.tsv
fi
if ! git diff --quiet -- lineup.txt lineup_resolved.tsv; then
  git add lineup.txt lineup_resolved.tsv && git commit -qm "Update lineup" && git push -q
  echo "Guide channel list updated on GitHub; the guide rebuilds in about a minute."
fi
(( $#failed )) && { echo "not updated: $failed"; exit 1; }
exit 0
