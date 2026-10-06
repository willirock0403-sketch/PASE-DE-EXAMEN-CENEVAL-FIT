"""Arma la línea de tiempo del video y la pista de voz completa.

Uso: python3 linea_de_tiempo.py <carpeta_audio>
Lee <carpeta_audio>/cues.json (de narracion.py) y escribe timeline.json y voz.wav.
Cada escena dura lo que pide la página (data-dur) o lo que tarde la voz, lo que sea mayor.
"""
import json, os, sys, wave

LEAD, GAP, TAIL = 0.7, 0.3, 0.9   # mismos márgenes que usa el reproductor de la página
d = sys.argv[1]
data = json.load(open(os.path.join(d, 'cues.json')))
rate = None; pcm = []; timeline = []; t0 = 0.0

for s in data:
    t, cues = LEAD, []
    for c in s['cues']:
        cues.append({'t': round(t, 3), 'text': c['text'], 'file': c['file']})
        t += c['len'] + GAP
    dur = max(s['dur'], t - GAP + TAIL)
    timeline.append({'start': round(t0, 3), 'dur': round(dur, 3), 'cues': cues})
    t0 += dur

with wave.open(data[0]['cues'][0]['file']) as w:
    rate, width, ch = w.getframerate(), w.getsampwidth(), w.getnchannels()
buf = bytearray(int(t0 * rate + 1) * width * ch)
for sc in timeline:
    for c in sc['cues']:
        with wave.open(c['file']) as w: frames = w.readframes(w.getnframes())
        off = int((sc['start'] + c['t']) * rate) * width * ch
        buf[off:off + len(frames)] = frames
with wave.open(os.path.join(d, 'voz.wav'), 'wb') as w:
    w.setnchannels(ch); w.setsampwidth(width); w.setframerate(rate); w.writeframes(bytes(buf))
json.dump({'total': round(t0, 3), 'scenes': timeline}, open(os.path.join(d, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
print('duración total: %.1f s' % t0)
