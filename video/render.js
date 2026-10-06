// Graba el video de fuente.html cuadro por cuadro y lo codifica en MP4 con la voz.
// Uso: node render.js <fuente.html> <timeline.json> <voz.wav> <salida.mp4> [fps] [solo_cuadros_de_prueba]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');

const [src, tlFile, voz, out, fpsArg, probe] = process.argv.slice(2);
const FPS = +(fpsArg || 30);
const tl = JSON.parse(fs.readFileSync(tlFile, 'utf8'));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(src));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => {
    window.play = function () {};            // el video lo controla este script, no el reproductor
    pause();
    var intro = document.getElementById('intro'); if (intro) intro.remove();
    document.body.classList.remove('intro-on');
    var st = document.createElement('style');
    st.textContent = 'body>*:not(main),.hero,.sec,#bar{display:none!important}' +
      'main.page{padding:0!important}' +
      '#player{position:fixed!important;left:0;top:0;width:1920px;height:1080px;margin:0!important;max-width:none!important;border-radius:0!important;box-shadow:none!important}' +
      '#viewport{width:1920px!important;height:1080px!important}' +
      '#stage{transform:none!important;left:0!important;top:0!important}';
    document.head.appendChild(st);
    window.__scene = -1;
    window.__frame = function (n, t, text) {
      if (n !== window.__scene) {
        go(n);
        if (n === 0) document.getElementById('wipe').classList.remove('go');
        window.__scene = n;
      }
      document.getAnimations().forEach(function (a) { a.pause(); a.currentTime = t * 1000; });
      var cc = document.getElementById('cc');
      if (cc.textContent !== text) cc.textContent = text;
    };
  });

  const frames = [];
  const total = Math.ceil(tl.total * FPS);
  for (let f = 0; f < total; f++) {
    const T = f / FPS;
    let n = tl.scenes.findIndex((s, k) => T < s.start + s.dur || k === tl.scenes.length - 1);
    const sc = tl.scenes[n], t = T - sc.start;
    let text = sc.cues[0].text;
    sc.cues.forEach(c => { if (t >= c.t) text = c.text; });
    frames.push([n, t, text]);
  }

  if (probe) {  // solo unos cuadros sueltos, para revisar
    for (const s of probe.split(',')) {
      const f = Math.round(parseFloat(s) * FPS), [n, t, text] = frames[f];
      await page.evaluate(([n, t, text]) => window.__frame(n, t, text), [n, t, text]);
      await page.screenshot({ path: `${out}-${s}.png` });
    }
    await browser.close(); return;
  }

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', voz,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '22', '-pix_fmt', 'yuv420p', '-tune', 'stillimage',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));

  for (let f = 0; f < frames.length; f++) {
    await page.evaluate(a => window.__frame(a[0], a[1], a[2]), frames[f]);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (FPS * 10) === 0) console.log(`${(f / FPS).toFixed(0)} / ${tl.total.toFixed(0)} s`);
  }
  ff.stdin.end();
  const code = await done;
  await browser.close();
  if (code !== 0) { console.error('ffmpeg falló', code); process.exit(1); }
  console.log('listo:', out);
})();
