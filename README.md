# VideoAssistant
Video analysis software for sport.
VideoAssistant simplifies cutting of clips form training or competition, especially if you want to trim a long video into many short videos.

## Features
 * Simple design and tagging
 * Adjustable playback speed
 * Up to four nameable tags at the same time
 * Frame accurate cutting
 * Merge all clips of the same tag to one video or render multiple short clips
 
## Requirements
 * 64 bit version of Windows 7/ 8/ 10
 * VLC media player (64 bit)
 * Microsoft Visual Studio redistributable runtime (Download: https://www.microsoft.com/de-DE/download/details.aspx?id=52685)

## Install
1. Download the latest release of the compiled software from https://github.com/Leon-1207/VideoAssistant/releases
2. If you have downloaded the .rar file extract it on your computer.
3. VideoAssistant needs the 64 bit version VLC media player from VideoLAN to work.
4. Make sure that the main folder of the VLC media player (the folder VLC should contain files like vlc.exe) is located at this location:
```
C:\Program Files (x86)\VideoLAN
```
If you have installed VLC at another location, you can simply move to the path mentioned above (it should still work).

## Getting started
1. Run video_assistant.exe
2. Load a video file (in the upper menu: Video -> Open Video)
3. Name your tags (otherwise the are called A, B, C, D) (menu: Tag -> Edit Tags)
4. Start tagging [Tagging](https://github.com/Leon-1207/VideoAssistant/blob/master/README.md#tagging)
5. (optional) Save your work (strg/ ctrl + s or menu: File -> Save Data)
6. Render the result(s) (menu: Video -> Render Video)

## Tagging
 * Red marked parts of the video wont be in the output video
 * Each color (except red) represents a tag
 * You can use up to four different tags
 * Parts of the video can be marked by pressing "y" to start the tagging. Pressing "y" again will end the tagging, the time between start and end will be marked with the selected tag.
 * Switch the selected tag by pressing "a", "b", "c" or "d" ("a" -> select tag A, "b" --> select tag B ...)
 * To mark parts of the video red/ overwrite existing marked sequences press press "x". It works like pressing "y" except that the sequence will be marked red.
 * Use "m" to cancel the tagging (after you have pressed "y" or "x")
 * Alternatively to pressing "c" you can tag a previously set interval by pressing "v" (to adjust it: menu: Tag -> Open Tagging Settings)
 
## Keyboard shortcuts
 * y: start/ end tagging
 * x: start/ end tagging (red)
 * m: cancel tagging
 * v: tag interval
 * a/ b/ c/ d: select tag
 * SPACE: play/ pause video
 * left arrow: rewind
 * right arrow: fast forward
 * Ctrl + s/ Strg + s: Save

## License
[GNU General Public License v3.0](./LICENSE)
