# import io
import os
import re
# from jupyterplot import ProgressPlot
# import threading
import wave

import numpy as np
# torch.set_num_threads(1)
# import torchaudio
# import matplotlib.pylab as plt
# torchaudio.set_audio_backend("soundfile")
import pyaudio

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import torch

import locale
import requests
import datetime

from silero_vad import load_silero_vad
from openai import OpenAI

torch.set_num_threads(4)

# device = torch.device('cpu')
# local_file = 'tts.pt'
# if not os.path.isfile(local_file):
#     torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', local_file)
# model2 = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
# model2.to(device)

model = load_silero_vad(onnx=False)


def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1 / 32768
    sound = sound.squeeze()  # depends on the use case
    return sound


FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = int(SAMPLE_RATE / 10)

num_samples = 512

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

pygame.mixer.init()

sample_rate = 48000
# speaker = 'xenia'
speaker = 'eugene'


def stop():
    input("Press Enter to stop the recording:")
    global continue_recording
    continue_recording = False


def start_recording():
    global history

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    data = []
    voiced_confidences = []

    start = False
    pos = 0
    while True:
        audio_chunk = stream.read(num_samples)
        pos = pos + 1
        if pos == 1000 and not start:
            history = [{"role": "system", "content": syscontent}, ]
            print('---------------------')
            print()
            pygame.mixer.music.load('pop_up_004_45050.mp3')
            pygame.mixer.music.play()

        # in case you want to save the audio later
        data.append(audio_chunk)
        while len(data) >= 70 and not start:
            data.pop(0)

        audio_int16 = np.frombuffer(audio_chunk, np.int16)

        audio_float32 = int2float(audio_int16)

        # get the confidences and add them to the list to plot them later
        new_confidence = model(torch.from_numpy(audio_float32), 16000).item()
        voiced_confidences.append(new_confidence)
        if len(voiced_confidences) > 30:
            voiced_confidences.pop(0)

        conf = sum(voiced_confidences) / 30  # kalman
        # print(new_confidence)

        if conf > 0.4 and not start:
            start = True
            print('>', end='', flush=True)

        if conf < 0.1 and start:
            print('>', end='', flush=True)
            break

    stream.stop_stream()  # "Stop Audio Recording
    stream.close()  # "Close Audio Recording

    audio.terminate()

    pygame.mixer.music.load('vfyvfyfy44.mp3')
    pygame.mixer.music.play()

    wf = wave.open('2.wav', 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(data[:-30]))
    wf.close()

    with open('2.wav', 'rb') as f:
        result = requests.post('http://127.0.0.1:1235/inference', files={'file': f}, data={'response_format': 'text'})
        print("" + result.text)

    if result.text.strip() == '':
        return

    res = result.text.strip().lower()
    if res == 'начни заново.' or res == 'начни заново':
        history = [{"role": "system", "content": syscontent}, ]
        print('---------------------')
        print()
        pygame.mixer.music.load('pop_up_004_45050.mp3')
        pygame.mixer.music.play()
        return

    history.append({"role": "user", "content": result.text})

    completion = client.chat.completions.create(
        model="IlyaGusev/saiga_mistral_7b_gguf/model-q4_K.gguf",
        messages=history,
        temperature=0.7,
        max_tokens=400,
        stream=True,
    )

    new_message = {"role": "assistant", "content": ""}

    part = 1
    endflag = False

    def i_completion(comp):
        for c in comp:
            yield c
        yield None

    print('@ ', end="", flush=True)
    for chunk in i_completion(completion):
        if chunk is not None and not chunk.choices[0].delta.content:
            continue

        if chunk is None:
            last = new_message["content"][-1]
            if last != '.' and last != '!' and last != '?':
                new_message["content"] += '.'
        else:
            new_message["content"] += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content, end="", flush=True)

        parts = re.split(r'([.?!\n]|, )', new_message["content"])
        while len(parts) > part:
            txt = parts[part - 1] + parts[part]
            txt = txt.strip()

            txt = txt.replace('Для конечности', 'Наконец')

            if txt == '' or txt == '.':
                part = part + 2
                continue

            # print("@ " + txt)
            if len(txt) > 2 and txt[0] == '#' and txt[1] == '#':
                # fixme test this
                new_message["content"] = ''.join(parts[0:part - 1])
                endflag = True
                print('@@@ break')
                break

            r = requests.get('http://localhost:9898/process', params={'VOICE': speaker, 'INPUT_TEXT': txt},
                             stream=True)
            if r.status_code == 200:
                with open('test' + str(part) + '.wav', 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
            else:
                part = part + 2
                continue

            # audio_paths = model2.save_wav(text=txt,
            #         speaker=speaker,
            #         sample_rate=sample_rate)

            # if chunk is not None and pygame.mixer.music.get_busy():
            #     break

            while pygame.mixer.music.get_busy():
                continue

            pygame.mixer.music.load('test' + str(part) + '.wav')
            pygame.mixer.music.play()

            part = part + 2

        if endflag:
            break

    print()
    while pygame.mixer.music.get_busy():
        continue

    print()
    history.append(new_message)

    pygame.mixer.music.load('vfyvfyfy44.mp3')
    pygame.mixer.music.play()


def get_date(date):
    day_list = ['первое', 'второе', 'третье', 'четвёртое',
                'пятое', 'шестое', 'седьмое', 'восьмое',
                'девятое', 'десятое', 'одиннадцатое', 'двенадцатое',
                'тринадцатое', 'четырнадцатое', 'пятнадцатое', 'шестнадцатое',
                'семнадцатое', 'восемнадцатое', 'девятнадцатое', 'двадцатое',
                'двадцать первое', 'двадцать второе', 'двадцать третье',
                'двадацать четвёртое', 'двадцать пятое', 'двадцать шестое',
                'двадцать седьмое', 'двадцать восьмое', 'двадцать девятое',
                'тридцатое', 'тридцать первое']
    month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    date_list = date.split('.')
    return (day_list[int(date_list[0]) - 1] + ' ' +
            month_list[int(date_list[1]) - 1] + ', ' +
            'две тысячи двадцать четвертый год')


locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

today = datetime.datetime.now()
mydate = get_date(datetime.datetime.strftime(today, '%d.%m.%Y')) + ", " + datetime.datetime.strftime(today, '%A')
# print("% " + mydate)

syscontent = ("Тебя зовут Андрей. Тебе тридцать два года.")
syscontent = syscontent + ("Говори от "
              "первого лица.  Отвечай только на русском, кратко, по делу, не более 30 слов, без смайликов. Сегодня " + mydate + ".")

history = [{"role": "system", "content": syscontent}, ]

while True:
    start_recording()
