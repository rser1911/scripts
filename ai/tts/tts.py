import os
import torch
import sys

device = torch.device('cpu')
#device = torch.device('gpu')
torch.set_num_threads(4)
local_file = 'tts.pt'

if not os.path.isfile(local_file):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt',
                                   local_file)  

model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
model.to(device)

sample_rate = 48000
speaker='xenia'


import re

# import wave
# import contextlib

# wf = wave.open('fifo.wav', 'wb')
# wf.setnchannels(1)
# wf.setsampwidth(2)
# wf.setframerate(sample_rate)
# for i, _audio in enumerate(audio):
#     wf.writeframes((audio[i] * 32767).numpy().astype('int16'))
# wf.close()

# f = open('fifo.wav', 'wb')
# for i, _audio in enumerate(audio):
#     f.write((audio[i] * 32767).numpy().astype('int16'))
# f.close()

from ruaccent import RUAccent
accentizer = RUAccent()
mydict = {'любой': 'люб+ой', 'ветер':'в+етер'}
accentizer.load(omograph_model_size='big_poetry', custom_dict = mydict, use_dictionary=True, tiny_mode=False, )
#text = 'на двери висит замок.' #  tiny, turbo2, turbo, big_poetry, medium_poetry, small_poetry
#print(accentizer.process_all(text))

from runorm import RUNorm
# Используйте load(workdir="./local_cache") для кэширования моделей в указанной папке.
# Доступные модели: small, medium, big
# Выбирайте устройство используемое pytorch с помощью переменной device
normalizer = RUNorm()
normalizer.load(model_size="big", device="cpu")

import subprocess
# ffmpeg -f s16le -ar 48000 -ac 1 -i fifo.wav fifo.mp3 -y
process = subprocess.Popen(["ffmpeg", "-f", "s16le", "-ar", "48000", "-ac", "1", "-i", "-", sys.argv[1] + ".mp3", "-y"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,) 


s = open(sys.argv[1], 'r').read()
s = re.split(r'([.?!\n])', s)

pause_part = b''.join([b'\x00\x00' * int(48000 / 3)])
count_part = int(len(s) / 2)
start = 0 
if len(sys.argv) > 2:
    start = int(sys.argv[2])

for i in range(start, count_part):
    text = s[i*2] + s[i*2 + 1]
    text = text.strip()
    if len(text) < 2:
        continue
    
    speaker='xenia'
    
    # header
    if re.search(r"^[А-Я,:\xa0 .!?0-9\"«»]+$", text):
        text = text.lower()
        speaker='baya'
    
    text = normalizer.norm(text)
    
    if not re.search(r"[а-яА-Я]", text):
        continue
        
    text = accentizer.process_all(text)
    
    print('[ ' + str(i) + ' / ' + str(count_part) + ' ] ' + text)
    
    audio = model.apply_tts(text=text,
                             speaker=speaker,
                             sample_rate=sample_rate)

    #for i, _audio in enumerate(audio):
    #    process.stdin.write((audio[i] * 32767).numpy().astype('int16'))
    process.stdin.write((audio * 32767).numpy().astype('int16'))
    process.stdin.write(pause_part)

process.stdin.close()

