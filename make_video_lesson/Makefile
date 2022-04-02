all:
	gcc toggle-decorations.c -Wall -o toggle-decorations `pkg-config --cflags --libs x11`
	gcc alphademo-png.c -o alphapng `pkg-config --cflags --libs gtk+-2.0`
clean:
	rm -f toggle-decorations alphapng out.mp4 out.ok.mp4 slide.png slide.mp4
