#!/bin/bash
# concat scenes, mix in music, loudness-normalise
cd /tmp/claude-0/proj
rm -f list.txt
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13; do echo "file 'media_E$i/videos/e$i/1080p30/E$i.mp4'" >> list.txt; done
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy voice_video.mp4
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 voice_video.mp4)
ffmpeg -v error -y -stream_loop -1 -i music_loop.wav -t $D -af "afade=t=in:d=3,afade=t=out:st=$(echo "$D-4"|bc):d=4,volume=0.16" music_full.wav
ffmpeg -v error -y -i voice_video.mp4 -i music_full.wav -filter_complex "[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,volume=1.0[v];[1:a]anull[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart final.mp4
ls -la final.mp4; ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of csv=p=0 final.mp4
