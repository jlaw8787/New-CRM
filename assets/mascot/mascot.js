/*
  Login screen mascot. Plays hidden MP4 clips, chroma keys the baked white
  background off in real time on a canvas, and sits next to the login card.
  Vanilla JS, no dependencies.
*/
(function () {
  'use strict';

  /* ---- tunables, nudge these ---- */
  var WHITE_THRESHOLD = 244;              // min(r,g,b) above this is background white
  var FEATHER_PX = 1.5;                   // edge feather radius, in working canvas px
  var BG_RGB = { r: 253, g: 253, b: 253 }; // measured flat background color, used to strip white spill
  var DISPLAY_HEIGHT = 160;               // on screen height in css px
  var CYCLE_MIN_MS = 9000;
  var CYCLE_MAX_MS = 20000;
  var POLL_MS = 900;                      // how often we check if the login screen is still up

  var CLIPS = [
    { name: 'wave', src: 'assets/mascot/mascot-wave.mp4' },
    { name: 'stethoscope', src: 'assets/mascot/mascot-stethoscope.mp4' }
  ];

  var wrap, video, canvas, ctx;
  var rafId = null, cycleTimer = null, pollTimer = null;
  var currentIndex = -1;
  var stopped = false;
  var everDrawn = false;
  var mql = null;

  function clamp255(v) { return v < 0 ? 0 : (v > 255 ? 255 : v); }

  /* ---------- chroma key ---------- */

  // H.264 chroma subsampling leaves single pixel dips of a few units in an
  // otherwise flat background (e.g. blue channel at 241 next to 253
  // neighbors). A raw per-pixel threshold turns each dip into a one-pixel
  // wall that blocks the flood fill locally, leaving isolated background
  // islands that survive as speckle. Averaging the min channel over its 3x3
  // neighborhood before thresholding smooths those dips back above the
  // line while leaving genuine character-colored pixels, whose neighbors
  // are similarly saturated, untouched.
  function smoothedMinChannel(data, width, height) {
    var size = width * height;
    var minCh = new Uint8ClampedArray(size);
    var i, o, r, g, b;
    for (i = 0; i < size; i++) {
      o = i * 4;
      r = data[o]; g = data[o + 1]; b = data[o + 2];
      minCh[i] = r < g ? (r < b ? r : b) : (g < b ? g : b);
    }

    var smooth = new Uint8ClampedArray(size);
    var x, y, dx, dy, xx, yy, sum, n;
    for (y = 0; y < height; y++) {
      for (x = 0; x < width; x++) {
        sum = 0; n = 0;
        for (dy = -1; dy <= 1; dy++) {
          yy = y + dy;
          if (yy < 0 || yy >= height) continue;
          for (dx = -1; dx <= 1; dx++) {
            xx = x + dx;
            if (xx < 0 || xx >= width) continue;
            sum += minCh[yy * width + xx];
            n++;
          }
        }
        smooth[y * width + x] = sum / n;
      }
    }
    return smooth;
  }

  function floodFillBackgroundMask(data, width, height) {
    var size = width * height;
    var bg = new Uint8Array(size);
    var stack = new Int32Array(size);
    var sp = 0;
    var candidate = smoothedMinChannel(data, width, height);

    function isBgCandidate(i) {
      return candidate[i] > WHITE_THRESHOLD;
    }

    function seed(i) {
      if (bg[i] === 0 && isBgCandidate(i)) { bg[i] = 1; stack[sp++] = i; }
    }

    var x, y;
    for (x = 0; x < width; x++) { seed(x); seed((height - 1) * width + x); }
    for (y = 0; y < height; y++) { seed(y * width); seed(y * width + width - 1); }

    while (sp > 0) {
      var i = stack[--sp];
      x = i % width;
      y = (i - x) / width;
      if (x > 0 && bg[i - 1] === 0 && isBgCandidate(i - 1)) { bg[i - 1] = 1; stack[sp++] = i - 1; }
      if (x < width - 1 && bg[i + 1] === 0 && isBgCandidate(i + 1)) { bg[i + 1] = 1; stack[sp++] = i + 1; }
      if (y > 0 && bg[i - width] === 0 && isBgCandidate(i - width)) { bg[i - width] = 1; stack[sp++] = i - width; }
      if (y < height - 1 && bg[i + width] === 0 && isBgCandidate(i + width)) { bg[i + width] = 1; stack[sp++] = i + width; }
    }

    return bg;
  }

  // Separable box blur with a fractional radius, so a feather of 1.5px is
  // an honest blend between a 1px and a 2px box rather than a hard round.
  function boxBlurFloat(src, width, height, radius) {
    var rFloor = Math.floor(radius);
    var frac = radius - rFloor;
    var tmp = new Float32Array(width * height);
    var out = new Float32Array(width * height);
    var x, y, k, sum, weight, row, xx, yy;

    for (y = 0; y < height; y++) {
      row = y * width;
      for (x = 0; x < width; x++) {
        sum = 0; weight = 0;
        for (k = -rFloor; k <= rFloor; k++) {
          xx = x + k;
          if (xx < 0) xx = 0; else if (xx >= width) xx = width - 1;
          sum += src[row + xx];
          weight += 1;
        }
        if (frac > 0) {
          xx = x - rFloor - 1; if (xx < 0) xx = 0;
          sum += src[row + xx] * frac; weight += frac;
          xx = x + rFloor + 1; if (xx >= width) xx = width - 1;
          sum += src[row + xx] * frac; weight += frac;
        }
        tmp[row + x] = sum / weight;
      }
    }

    for (x = 0; x < width; x++) {
      for (y = 0; y < height; y++) {
        sum = 0; weight = 0;
        for (k = -rFloor; k <= rFloor; k++) {
          yy = y + k;
          if (yy < 0) yy = 0; else if (yy >= height) yy = height - 1;
          sum += tmp[yy * width + x];
          weight += 1;
        }
        if (frac > 0) {
          yy = y - rFloor - 1; if (yy < 0) yy = 0;
          sum += tmp[yy * width + x] * frac; weight += frac;
          yy = y + rFloor + 1; if (yy >= height) yy = height - 1;
          sum += tmp[yy * width + x] * frac; weight += frac;
        }
        out[y * width + x] = sum / weight;
      }
    }
    return out;
  }

  function applyChromaKey(data, width, height) {
    var size = width * height;
    var bg = floodFillBackgroundMask(data, width, height);

    var af = new Float32Array(size);
    var i;
    for (i = 0; i < size; i++) af[i] = bg[i] ? 0 : 255;

    if (FEATHER_PX > 0) af = boxBlurFloat(af, width, height, FEATHER_PX);

    for (i = 0; i < size; i++) {
      var a = af[i];
      var o = i * 4;
      if (a <= 0) { data[o + 3] = 0; continue; }
      if (a >= 255) { data[o + 3] = 255; continue; }

      // Edge pixel: undo the white the encoder blended in, so the fringe
      // does not carry a pale halo when composited over a dark background.
      var av = a / 255;
      var r = data[o], g = data[o + 1], b = data[o + 2];
      data[o] = clamp255((r - BG_RGB.r * (1 - av)) / av);
      data[o + 1] = clamp255((g - BG_RGB.g * (1 - av)) / av);
      data[o + 2] = clamp255((b - BG_RGB.b * (1 - av)) / av);
      data[o + 3] = a;
    }
  }

  /* ---------- dom + layout ---------- */

  function buildDom() {
    wrap = document.createElement('div');
    wrap.id = 'mascot-wrap';
    wrap.setAttribute('aria-hidden', 'true');

    canvas = document.createElement('canvas');
    canvas.id = 'mascot-canvas';
    canvas.style.height = DISPLAY_HEIGHT + 'px';
    canvas.style.width = 'auto';
    wrap.appendChild(canvas);
    document.body.appendChild(wrap);

    ctx = canvas.getContext('2d', { willReadFrequently: true });

    video = document.createElement('video');
    video.id = 'mascot-video';
    video.muted = true;
    video.defaultMuted = true;
    video.loop = true;
    video.playsInline = true;
    video.preload = 'auto';
    video.setAttribute('muted', '');
    video.setAttribute('playsinline', '');
    video.setAttribute('webkit-playsinline', '');
    video.style.cssText = 'position:fixed;left:-9999px;top:-9999px;width:1px;height:1px;opacity:0;pointer-events:none';
    document.body.appendChild(video);

    video.addEventListener('loadedmetadata', onMetadata);
    video.addEventListener('error', onVideoError);
  }

  function onMetadata() {
    var aspect = video.videoWidth && video.videoHeight ? video.videoWidth / video.videoHeight : 1;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.height = Math.round(DISPLAY_HEIGHT * dpr);
    canvas.width = Math.round(DISPLAY_HEIGHT * dpr * aspect);
    positionMascot();
  }

  function onVideoError() {
    if (stopped) return;
    playClip(pickClip(currentIndex));
  }

  function positionMascot() {
    if (!wrap) return;
    var card = document.querySelector('.lc');
    var wrapRect = wrap.getBoundingClientRect();
    var w = wrapRect.width || 120;
    var h = wrapRect.height || DISPLAY_HEIGHT;

    if (!card) {
      wrap.style.left = (window.innerWidth - w - 20) + 'px';
      wrap.style.top = (window.innerHeight - h - 20) + 'px';
      return;
    }

    var r = card.getBoundingClientRect();
    var left = r.right + 14;
    var top = r.bottom - h + 6;

    if (left + w > window.innerWidth - 8) {
      left = r.left - w + 26;
      if (left < 8) {
        left = Math.max(8, r.left + (r.width - w) / 2);
        top = r.bottom + 10;
      }
    }
    if (top + h > window.innerHeight - 8) top = window.innerHeight - h - 8;
    if (top < 8) top = 8;

    wrap.style.left = left + 'px';
    wrap.style.top = top + 'px';
  }

  /* ---------- playback ---------- */

  function pickClip(excludeIndex) {
    if (CLIPS.length <= 1) return 0;
    var i;
    do { i = Math.floor(Math.random() * CLIPS.length); } while (i === excludeIndex);
    return i;
  }

  function playClip(index) {
    currentIndex = index;
    video.src = CLIPS[index].src;
    video.currentTime = 0;
    if (!shouldPause()) {
      var p = video.play();
      if (p && p.catch) p.catch(function () {});
    }
  }

  function scheduleNext() {
    clearTimeout(cycleTimer);
    var delay = CYCLE_MIN_MS + Math.random() * (CYCLE_MAX_MS - CYCLE_MIN_MS);
    cycleTimer = setTimeout(function () {
      if (stopped) return;
      if (!shouldPause()) playClip(pickClip(currentIndex));
      scheduleNext();
    }, delay);
  }

  /* ---------- pause / resume ---------- */

  function shouldPause() {
    if (window.localStorage && localStorage.getItem('mascotForceVisible') === '1') return false;
    return document.hidden || (mql && mql.matches);
  }

  function applyPauseState() {
    if (stopped) return;
    if (shouldPause()) {
      if (!video.paused) video.pause();
      wrap.classList.remove('on');
    } else {
      if (video.paused && video.readyState >= 2) {
        var p = video.play();
        if (p && p.catch) p.catch(function () {});
      }
      if (everDrawn) wrap.classList.add('on');
    }
  }

  /* ---------- render loop ---------- */

  function tick() {
    rafId = requestAnimationFrame(tick);
    if (stopped || shouldPause()) return;
    if (video.readyState < 2 || video.paused || video.ended) return;
    if (!canvas.width || !canvas.height) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    var frame;
    try {
      frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
    } catch (e) {
      return;
    }
    applyChromaKey(frame.data, canvas.width, canvas.height);
    ctx.putImageData(frame, 0, 0);

    if (!everDrawn) {
      everDrawn = true;
      applyPauseState();
    }
  }

  /* ---------- login state ---------- */

  // Keyed off #ls rather than the password field itself: index.html swaps
  // the login card body to loading skeletons while it awaits data, which
  // removes #l-auth-pw from the DOM for a moment that has nothing to do
  // with a successful login. #ls only ever goes hidden from completeLogin,
  // which is the actual "password field is gone for good" moment.
  function loginActive() {
    var ls = document.getElementById('ls');
    if (!ls || !document.body.contains(ls)) return false;

    var lsStyle = window.getComputedStyle(ls);
    if (lsStyle.display === 'none' || lsStyle.visibility === 'hidden') return false;

    return true;
  }

  function pollLoginState() {
    if (stopped) return;
    if (!loginActive()) stopMascot();
  }

  /* ---------- lifecycle ---------- */

  function stopMascot() {
    if (stopped) return;
    stopped = true;

    clearInterval(pollTimer);
    clearTimeout(cycleTimer);
    if (rafId) cancelAnimationFrame(rafId);

    window.removeEventListener('resize', positionMascot);
    document.removeEventListener('visibilitychange', applyPauseState);
    if (mql) {
      try { mql.removeEventListener('change', applyPauseState); } catch (e) {}
    }

    if (video) {
      video.pause();
      video.removeAttribute('src');
      video.load();
      if (video.parentNode) video.parentNode.removeChild(video);
    }
    if (wrap && wrap.parentNode) wrap.parentNode.removeChild(wrap);
  }

  function init() {
    if (!document.getElementById('ls')) return;

    mql = window.matchMedia('(prefers-reduced-motion: reduce)');

    buildDom();
    positionMascot();
    window.addEventListener('resize', positionMascot);
    document.addEventListener('visibilitychange', applyPauseState);
    try { mql.addEventListener('change', applyPauseState); } catch (e) {}

    pollTimer = setInterval(pollLoginState, POLL_MS);
    rafId = requestAnimationFrame(tick);

    playClip(pickClip(-1));
    scheduleNext();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
