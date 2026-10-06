# PASE-DE-EXAMEN-CENEVAL-FIT

Guía en video para el registro en línea al EXANI-II (Facultad de Ingeniería Tampico, UAT).
La página es `index.html`; el video es `video/registro-exani-ii.mp4`.

## Cómo volver a generar el video

`video/fuente.html` es la versión animada del video (escenas, textos en pantalla y narración en `NARR`).
Si cambia algún texto ahí, regenere el MP4:

```sh
pip install piper-tts
# voz es_MX-claude-high de Piper (por ejemplo, de github.com/k2-fsa/sherpa-onnx/releases, tts-models)
python3 video/narracion.py video/fuente.html es_MX-claude-high.onnx /tmp/audio
python3 video/linea_de_tiempo.py /tmp/audio
node video/render.js video/fuente.html /tmp/audio/timeline.json /tmp/audio/voz.wav video/registro-exani-ii.mp4
ffmpeg -y -ss 3 -i video/registro-exani-ii.mp4 -frames:v 1 -q:v 3 video/portada.jpg
```

`render.js` necesita Playwright con Chromium y `ffmpeg`.
