## Translate text to audio
(for notes, books, etc..)

### Requirements

* python
* ffmpeg

### Install

```
apt-get install ffmpeg
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install torch numpy ruaccent runorm
python3 tts.py <file.txt>
```

