#!/usr/bin/env bash
# Assemble Apprentice demo v2: one picture segment per VO file (s0, s0b, s1–s9).
# Sync cannot drift: each beat is muxed with -shortest / VO-padded freeze.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIVE="$ROOT/docs/video/live"
VO="$LIVE/vo-v2"
WORK="$ROOT/docs/video/out/assemble-v2"
OUT="$ROOT/docs/video/youtube/apprentice-demo-final.mp4"

TERM="$LIVE/terminal-q02-attempt-2.mov"
CRDB="$LIVE/s8-cockroachdb-console.mov"
BEDROCK="$LIVE/s8-bedrock-console.mov"
TITLE="$ROOT/docs/video/slides/01-title.png"
CURVE="$ROOT/docs/media/learning-curve.png"
END="$ROOT/docs/video/slides/99-end.png"

# Terminal cuts (seconds) from OCR of terminal-q02-attempt-2.mov
# End each beat on the OUTCOME frame, strictly BEFORE the next SECTION banner.
# (Freezes clone the last frame for the rest of the VO — wrong last frame = visible bleed.)
S0B_START=2;    S0B_END=13.5   # HOW THIS RUNS agenda (S1 at 14.2)
S1_START=14.2;  S1_END=25.5    # before S2 at 26
# Bias starts toward OUTCOME so long VOs freeze on the matching still, not mid-scroll.
S2_START=30.0;  S2_END=35.0    # WRONG outcome; S3 banner at 35.5
S3_START=42.0;  S3_END=49.0    # 4 rules stored; S4 banner at 49.5
S4_START=55.0;  S4_END=60.5    # CORRECT outcome; S5 banner at 61
S5_START=66.0;  S5_END=71.0    # now 4 / t0 0; S6 banner at 71.5
S6_START=98.0;  S6_END=110.0   # report table + 44/44 outcome

# S8 console slices (seconds into each screen recording)
CRDB_SQL_START=24
BED_NOVA_START=0
BED_TITAN_START=23

mkdir -p "$WORK"

need() { [[ -f "$1" ]] || { echo "Missing: $1" >&2; exit 1; }; }
need "$TERM"; need "$CRDB"; need "$BEDROCK"; need "$TITLE"; need "$CURVE"; need "$END"
need "$VO/s0.mp3"; need "$VO/s0b.mp3"
for i in 1 2 3 4 5 6 7 8 9; do need "$VO/s$i.mp3"; done

VF="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30,format=yuv420p"

vo_dur() { ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1"; }

still_to() {
  local img="$1" dur="$2" out="$3"
  ffmpeg -y -loop 1 -i "$img" -t "$dur" -vf "$VF" -c:v libx264 -preset fast -crf 18 -an "$out" </dev/null
}

clip_to_vo() {
  local src="$1" start="$2" end="$3" vo="$4" out="$5"
  local raw="$WORK/$(basename "$out" .mp4)-raw.mp4"
  local target pad pic_dur
  target=$(vo_dur "$vo")
  pic_dur=$(python3.11 -c "print(max(0.2, float('$end') - float('$start')))")
  ffmpeg -y -i "$src" -ss "$start" -t "$pic_dur" -vf "$VF" -c:v libx264 -preset fast -crf 18 -an "$raw" </dev/null
  pad=$(python3.11 -c "print(max(float('$target'), 0.2))")
  ffmpeg -y -i "$raw" -i "$vo" \
    -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=${pad},trim=duration=${target},setpts=PTS-STARTPTS[v];[1:a]apad=whole_dur=${target},atrim=0:${target},alimiter=limit=0.95[a]" \
    -map "[v]" -map "[a]" \
    -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -t "$target" \
    "$out" </dev/null
}

still_to_vo() {
  local img="$1" vo="$2" out="$3"
  local target raw
  target=$(vo_dur "$vo")
  raw="$WORK/$(basename "$out" .mp4)-still.mp4"
  still_to "$img" "$target" "$raw"
  ffmpeg -y -i "$raw" -i "$vo" \
    -c:v copy -c:a aac -b:a 192k -shortest \
    "$out" </dev/null
}

consoles_to_vo() {
  local vo="$1" out="$2"
  local target d_crdb d_nova d_titan a b c
  target=$(vo_dur "$vo")
  read -r d_crdb d_nova d_titan < <(python3.11 -c "
t=float('$target')
print(f'{t*0.45:.3f} {t*0.30:.3f} {t*0.25:.3f}')
")
  a="$WORK/s8a.mp4"; b="$WORK/s8b-nova.mp4"; c="$WORK/s8b-titan.mp4"
  ffmpeg -y -i "$CRDB" -ss "$CRDB_SQL_START" -t "$d_crdb" -vf "$VF" -c:v libx264 -preset fast -crf 18 -an "$a" </dev/null
  ffmpeg -y -i "$BEDROCK" -ss "$BED_NOVA_START" -t "$d_nova" -vf "$VF" -c:v libx264 -preset fast -crf 18 -an "$b" </dev/null
  ffmpeg -y -i "$BEDROCK" -ss "$BED_TITAN_START" -t "$d_titan" -vf "$VF" -c:v libx264 -preset fast -crf 18 -an "$c" </dev/null
  ffmpeg -y -i "$a" -i "$b" -i "$c" -i "$vo" \
    -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=${d_crdb},trim=duration=${d_crdb},setpts=PTS-STARTPTS[v0];[1:v]tpad=stop_mode=clone:stop_duration=${d_nova},trim=duration=${d_nova},setpts=PTS-STARTPTS[v1];[2:v]tpad=stop_mode=clone:stop_duration=${d_titan},trim=duration=${d_titan},setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v];[3:a]apad=whole_dur=${target},atrim=0:${target},alimiter=limit=0.95[a]" \
    -map "[v]" -map "[a]" \
    -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -t "$target" \
    "$out" </dev/null
}

echo "Building S0 title…"
still_to_vo "$TITLE" "$VO/s0.mp3" "$WORK/s0.mp4"

echo "Building S0b agenda…"
clip_to_vo "$TERM" "$S0B_START" "$S0B_END" "$VO/s0b.mp3" "$WORK/s0b.mp4"

echo "Building S1–S6 terminal beats…"
clip_to_vo "$TERM" "$S1_START" "$S1_END" "$VO/s1.mp3" "$WORK/s1.mp4"
clip_to_vo "$TERM" "$S2_START" "$S2_END" "$VO/s2.mp3" "$WORK/s2.mp4"
clip_to_vo "$TERM" "$S3_START" "$S3_END" "$VO/s3.mp3" "$WORK/s3.mp4"
clip_to_vo "$TERM" "$S4_START" "$S4_END" "$VO/s4.mp3" "$WORK/s4.mp4"
clip_to_vo "$TERM" "$S5_START" "$S5_END" "$VO/s5.mp3" "$WORK/s5.mp4"
clip_to_vo "$TERM" "$S6_START" "$S6_END" "$VO/s6.mp3" "$WORK/s6.mp4"

echo "Building S7 curve…"
still_to_vo "$CURVE" "$VO/s7.mp3" "$WORK/s7.mp4"

echo "Building S8 consoles…"
consoles_to_vo "$VO/s8.mp3" "$WORK/s8.mp4"

echo "Building S9 end…"
still_to_vo "$END" "$VO/s9.mp3" "$WORK/s9.mp4"

cat >"$WORK/concat.txt" <<EOF
file '$WORK/s0.mp4'
file '$WORK/s0b.mp4'
file '$WORK/s1.mp4'
file '$WORK/s2.mp4'
file '$WORK/s3.mp4'
file '$WORK/s4.mp4'
file '$WORK/s5.mp4'
file '$WORK/s6.mp4'
file '$WORK/s7.mp4'
file '$WORK/s8.mp4'
file '$WORK/s9.mp4'
EOF

ffmpeg -y -f concat -safe 0 -i "$WORK/concat.txt" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 192k \
  "$OUT" </dev/null

echo
echo "Wrote $OUT"
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
ls -lh "$OUT"
for seg in s0 s0b s1 s2 s3 s4 s5 s6 s7 s8 s9; do
  d=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$WORK/$seg.mp4")
  printf '  %s picture+VO = %.2fs\n' "$seg" "$d"
done
