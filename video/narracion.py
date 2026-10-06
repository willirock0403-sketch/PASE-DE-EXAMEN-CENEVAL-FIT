"""Genera la narración del video (una pista por frase de subtítulo) con Piper.

Uso: python3 narracion.py <fuente.html> <modelo.onnx> <carpeta_salida>
Escribe <salida>/cues.json con el texto y la duración de cada frase, y un .wav por frase.
"""
import json, re, subprocess, sys, wave, os

src, model, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
html = open(src, encoding='utf-8').read()
narr = json.loads('[' + re.search(r'var NARR = \[(.*?)\n\];', html, re.S).group(1) + ']')
durs = [float(x) for x in re.findall(r'class="scene[^"]*" data-dur="([\d.]+)"', html)]
assert len(narr) == len(durs), (len(narr), len(durs))

def cues(txt):  # mismo corte en frases que usa la página para los subtítulos
    parts = [p.strip() for p in re.findall(r'[^.!?:]+[.!?:]+|[^.!?:]+$', txt) if p.strip()]
    res, buf = [], ''
    for p in parts:
        if buf and len(buf + ' ' + p) > 118: res.append(buf); buf = p
        else: buf = buf + ' ' + p if buf else p
    if buf: res.append(buf)
    return [s[0].upper() + s[1:] for s in res]

# cómo debe pronunciarse (solo para la voz; el subtítulo conserva el texto original)
SAY = [(r'EXANI-II', 'EXANI dos'), (r'\bUAT\b', 'U A T'), (r'\bEDC\b', 'E D C'),
       (r'\bPDF\b', 'P D F'), (r'CENEVAL', 'Ceneval'), (r'\bCURP\b', 'curp')]
def say(s):
    for a, b in SAY: s = re.sub(a, b, s)
    return s

data = []
for n, txt in enumerate(narr):
    scene = {'dur': durs[n], 'cues': []}
    for k, c in enumerate(cues(txt)):
        f = os.path.join(out, f'{n:02d}-{k:02d}.wav')
        subprocess.run([sys.executable, '-m', 'piper', '-m', model, '-f', f, '--sentence-silence', '0.15'],
                       input=say(c).encode(), check=True, capture_output=True)
        with wave.open(f) as w: d = w.getnframes() / w.getframerate()
        scene['cues'].append({'text': c, 'file': f, 'len': round(d, 3)})
    data.append(scene)
json.dump(data, open(os.path.join(out, 'cues.json'), 'w'), ensure_ascii=False, indent=1)
for n, s in enumerate(data): print(n, s['dur'], round(sum(c['len'] for c in s['cues']), 2), len(s['cues']))
