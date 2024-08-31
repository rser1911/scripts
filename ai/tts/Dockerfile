FROM python:3.11
COPY . /root
WORKDIR /root
RUN apt-get update && apt-get install ffmpeg -y && python3 -m pip install torch numpy ruaccent runorm && touch test.txt && mkdir mnt && python3 tts.py test.txt
ENTRYPOINT ["python3", "tts.py"] 
