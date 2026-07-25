/*
  Platypus mascot for the login screen.
  Vanilla JS, no dependencies, self contained.

  Usage:
    <script src="platypus-mascot.js"></script>
    <script>PlatypusMascot.start({ src: 'assets/platypus-mascot.png', cardSelector: '.login-card' });</script>

  Or set window.PLATYPUS_CONFIG before the script loads and it auto starts.
*/
(function (global) {
  'use strict';

  var DEFAULTS = {
    src: 'assets/platypus-mascot.png',
    cardSelector: '.login-card',   // element it headbutts and peeks near. Optional.
    height: 130,                   // rendered height in px
    zIndex: 40,                    // keep below modals, above background
    firstDelay: 1400,              // ms before the first stunt
    gapMin: 11000,                 // min ms between stunts
    gapMax: 20000,                 // max ms between stunts
    clickable: true,               // click it for a backflip and a line
    lines: [
      'Oi.',
      'Password is not on the sticky note.',
      'Still faster than the fax machine.',
      'Nice scrubs.',
      'Someone has to cover the shift.'
    ]
  };

  var CSS = [
    '#plat-mascot{position:fixed;left:0;top:0;pointer-events:none;opacity:0;',
    'will-change:transform;z-index:var(--plat-z,40)}',
    '#plat-mascot.plat-on{opacity:1}',
    '#plat-mascot img{display:block;height:var(--plat-h,130px);width:auto;',
    '-webkit-user-select:none;user-select:none;-webkit-user-drag:none;',
    'filter:drop-shadow(0 10px 14px rgba(0,0,0,.28))}',
    '#plat-mascot.plat-click{pointer-events:auto;cursor:pointer}',
    '.plat-flip{transform-origin:50% 100%}',
    '.plat-anim{transform-origin:50% 100%}',
    '@keyframes plat-waddle{',
    '0%{transform:translateY(0) rotate(-5deg)}',
    '25%{transform:translateY(-7px) rotate(0deg)}',
    '50%{transform:translateY(0) rotate(5deg)}',
    '75%{transform:translateY(-7px) rotate(0deg)}',
    '100%{transform:translateY(0) rotate(-5deg)}}',
    '@keyframes plat-scurry{',
    '0%{transform:translateY(0) rotate(-9deg)}',
    '50%{transform:translateY(-11px) rotate(9deg)}',
    '100%{transform:translateY(0) rotate(-9deg)}}',
    '@keyframes plat-look{',
    '0%,100%{transform:rotate(0deg)}',
    '20%{transform:rotate(-11deg)}',
    '55%{transform:rotate(11deg)}',
    '80%{transform:rotate(0deg)}}',
    '@keyframes plat-snooze{',
    '0%,100%{transform:translateY(0) scale(1,1) rotate(-3deg)}',
    '50%{transform:translateY(3px) scale(1.03,.96) rotate(-3deg)}}',
    '@keyframes plat-startle{',
    '0%,100%{transform:translate(0,0) rotate(0)}',
    '20%{transform:translate(-6px,-14px) rotate(-8deg)}',
    '40%{transform:translate(6px,-4px) rotate(8deg)}',
    '60%{transform:translate(-4px,-10px) rotate(-5deg)}',
    '80%{transform:translate(4px,-2px) rotate(4deg)}}',
    '@keyframes plat-flip{',
    '0%{transform:translateY(0) rotate(0)}',
    '40%{transform:translateY(-70px) rotate(-200deg)}',
    '100%{transform:translateY(0) rotate(-360deg)}}',
    '@keyframes plat-headbutt{',
    '0%,100%{transform:translateX(0) rotate(0)}',
    '45%{transform:translateX(var(--plat-hit,18px)) rotate(6deg)}',
    '60%{transform:translateX(calc(var(--plat-hit,18px) * -.6)) rotate(-6deg)}}',
    '.plat-shake{animation:plat-cardshake .5s cubic-bezier(.36,.07,.19,.97) both}',
    '@keyframes plat-cardshake{',
    '10%,90%{transform:translateX(-3px)}',
    '20%,80%{transform:translateX(5px)}',
    '30%,50%,70%{transform:translateX(-7px)}',
    '40%,60%{transform:translateX(7px)}}',
    '#plat-bubble{position:fixed;left:0;top:0;z-index:calc(var(--plat-z,40) + 1);',
    'pointer-events:none;opacity:0;transform:translateY(6px);',
    'transition:opacity .18s ease,transform .18s ease;',
    'background:#fff;color:#231f2e;border:2px solid #231f2e;border-radius:12px;',
    'padding:7px 12px;font:600 13px/1.25 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;',
    'white-space:nowrap;box-shadow:0 6px 16px rgba(0,0,0,.2)}',
    '#plat-bubble.plat-on{opacity:1;transform:translateY(0)}',
    '#plat-bubble:after{content:"";position:absolute;bottom:-8px;left:22px;',
    'width:12px;height:12px;background:#fff;border-right:2px solid #231f2e;',
    'border-bottom:2px solid #231f2e;transform:rotate(45deg)}'
  ].join('');

  var cfg, root, flip, anim, img, bubble, timer = null;
  var busy = false, started = false, lastAction = -1;
  var size = { w: 90, h: 130 };

  function wait(ms) {
    return new Promise(function (r) { setTimeout(r, ms); });
  }

  function rand(min, max) { return min + Math.random() * (max - min); }

  function vw() { return window.innerWidth; }
  function vh() { return window.innerHeight; }

  function placeAt(x, y) {
    root.style.transition = 'none';
    root.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    void root.offsetWidth;
  }

  function moveTo(x, y, ms, ease) {
    root.style.transition = 'transform ' + ms + 'ms ' + (ease || 'linear');
    root.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    return wait(ms + 30);
  }

  function setAnim(value) {
    anim.style.animation = value || 'none';
  }

  function face(dir) {
    flip.style.transform = dir === 'left' ? 'scaleX(-1)' : 'scaleX(1)';
  }

  function show() { root.classList.add('plat-on'); }

  function hide() {
    root.classList.remove('plat-on');
    setAnim('none');
    anim.style.transform = '';
    placeAt(-9999, -9999);
  }

  function floorY() { return vh() - size.h - 8; }

  function card() {
    if (!cfg.cardSelector) return null;
    var el = document.querySelector(cfg.cardSelector);
    if (!el) return null;
    var r = el.getBoundingClientRect();
    if (!r.width) return null;
    return { el: el, rect: r };
  }

  function say(text, ms) {
    var r = root.getBoundingClientRect();
    bubble.textContent = text;
    bubble.style.left = Math.max(8, Math.min(vw() - 220, r.left + size.w * 0.5 - 24)) + 'px';
    bubble.style.top = Math.max(8, r.top - 48) + 'px';
    bubble.classList.add('plat-on');
    return wait(ms || 1600).then(function () {
      bubble.classList.remove('plat-on');
    });
  }

  /* ---------- the stunts ---------- */

  // 1. Waddles in, stops for a look around, waddles out.
  function waddleAcross() {
    var toRight = Math.random() < 0.5;
    var y = floorY();
    var startX = toRight ? -size.w - 30 : vw() + 30;
    var endX = toRight ? vw() + 30 : -size.w - 30;
    var midX = rand(vw() * 0.3, vw() * 0.7);

    placeAt(startX, y);
    face(toRight ? 'right' : 'left');
    setAnim('plat-waddle .38s linear infinite');
    show();

    return moveTo(midX, y, Math.abs(midX - startX) * 6)
      .then(function () {
        setAnim('plat-look 1.4s ease-in-out 1');
        return wait(1500);
      })
      .then(function () {
        setAnim('plat-waddle .38s linear infinite');
        return moveTo(endX, y, Math.abs(endX - midX) * 6);
      })
      .then(hide);
  }

  // 2. Pops up from the bottom of the screen, has a squiz, ducks back down.
  function peek() {
    var c = card();
    var x = c ? c.rect.left + c.rect.width * 0.5 - size.w * 0.5 : vw() * 0.5 - size.w * 0.5;
    x = Math.max(10, Math.min(vw() - size.w - 10, x + rand(-80, 80)));
    var down = vh() + 10;
    var up = vh() - size.h * 0.62;

    placeAt(x, down);
    face(Math.random() < 0.5 ? 'left' : 'right');
    setAnim('none');
    show();

    return moveTo(x, up, 520, 'cubic-bezier(.2,1.4,.5,1)')
      .then(function () {
        setAnim('plat-look 1.6s ease-in-out 1');
        return wait(1700);
      })
      .then(function () {
        setAnim('none');
        return moveTo(x, down, 340, 'cubic-bezier(.5,0,.9,.4)');
      })
      .then(hide);
  }

  // 3. Runs up to the login card, headbutts it, bolts.
  function mischief() {
    var c = card();
    if (!c) return waddleAcross();

    var fromLeft = Math.random() < 0.5;
    var y = Math.min(floorY(), c.rect.bottom - size.h * 0.45);
    var targetX = fromLeft
      ? c.rect.left - size.w * 0.8
      : c.rect.right - size.w * 0.2;
    targetX = Math.max(-size.w * 0.3, Math.min(vw() - size.w * 0.7, targetX));
    var startX = fromLeft ? -size.w - 30 : vw() + 30;

    placeAt(startX, y);
    face(fromLeft ? 'right' : 'left');
    setAnim('plat-scurry .22s linear infinite');
    show();

    return moveTo(targetX, y, Math.abs(targetX - startX) * 3.2, 'cubic-bezier(.2,.6,.4,1)')
      .then(function () {
        setAnim('none');
        return wait(320);
      })
      .then(function () {
        anim.style.setProperty('--plat-hit', (fromLeft ? 22 : -22) + 'px');
        setAnim('plat-headbutt .42s ease-out 1');
        return wait(200);
      })
      .then(function () {
        c.el.classList.remove('plat-shake');
        void c.el.offsetWidth;
        c.el.classList.add('plat-shake');
        return wait(500);
      })
      .then(function () {
        c.el.classList.remove('plat-shake');
        face(fromLeft ? 'left' : 'right');
        setAnim('plat-scurry .16s linear infinite');
        return moveTo(startX, y, 900, 'cubic-bezier(.4,0,1,.6)');
      })
      .then(hide);
  }

  // 4. Belly slides across the floor and pops back upright.
  function bellySlide() {
    var toRight = Math.random() < 0.5;
    var y = floorY() + size.h * 0.18;
    var startX = toRight ? -size.w - 40 : vw() + 40;
    var stopX = toRight ? vw() * 0.62 : vw() * 0.38 - size.w;

    placeAt(startX, y);
    face(toRight ? 'right' : 'left');
    setAnim('none');
    anim.style.transform = 'rotate(' + (toRight ? 74 : 74) + 'deg)';
    show();

    return moveTo(stopX, y, 780, 'cubic-bezier(.05,.8,.3,1)')
      .then(function () {
        anim.style.transform = '';
        setAnim('plat-startle .5s ease-out 1');
        return wait(600);
      })
      .then(function () {
        setAnim('plat-waddle .4s linear infinite');
        return moveTo(toRight ? vw() + 40 : -size.w - 40, floorY(), 1600);
      })
      .then(hide);
  }

  // 5. Asleep in the corner, wakes up startled, bolts off screen.
  function snooze() {
    var onRight = Math.random() < 0.5;
    var x = onRight ? vw() - size.w - 24 : 24;
    var y = floorY();

    placeAt(x, y);
    face(onRight ? 'left' : 'right');
    setAnim('plat-snooze 2.4s ease-in-out infinite');
    show();

    return wait(4200)
      .then(function () {
        setAnim('plat-startle .5s ease-out 1');
        return wait(560);
      })
      .then(function () {
        face(onRight ? 'right' : 'left');
        setAnim('plat-scurry .17s linear infinite');
        return moveTo(onRight ? vw() + 40 : -size.w - 40, y, 700, 'cubic-bezier(.4,0,1,.6)');
      })
      .then(hide);
  }

  var ACTIONS = [waddleAcross, peek, mischief, bellySlide, snooze];

  function pick() {
    var i = Math.floor(Math.random() * ACTIONS.length);
    if (i === lastAction) i = (i + 1) % ACTIONS.length;
    lastAction = i;
    return ACTIONS[i];
  }

  function run(fn) {
    if (busy) return Promise.resolve();
    busy = true;
    return Promise.resolve()
      .then(fn)
      .catch(function (e) { console.warn('platypus', e); })
      .then(function () {
        busy = false;
        hide();
      });
  }

  function schedule(delay) {
    clearTimeout(timer);
    timer = setTimeout(function () {
      if (document.hidden) { schedule(4000); return; }
      run(pick()).then(function () {
        schedule(rand(cfg.gapMin, cfg.gapMax));
      });
    }, delay);
  }

  function onClick() {
    if (busy) return;
    busy = true;
    var line = cfg.lines[Math.floor(Math.random() * cfg.lines.length)];
    setAnim('plat-flip .7s cubic-bezier(.3,0,.4,1) 1');
    say(line, 1700).then(function () {
      setAnim('none');
      busy = false;
    });
  }

  function build() {
    var style = document.createElement('style');
    style.id = 'plat-style';
    style.textContent = CSS;
    document.head.appendChild(style);

    root = document.createElement('div');
    root.id = 'plat-mascot';
    root.setAttribute('aria-hidden', 'true');
    root.style.setProperty('--plat-h', cfg.height + 'px');
    root.style.setProperty('--plat-z', cfg.zIndex);
    if (cfg.clickable) root.classList.add('plat-click');

    flip = document.createElement('div');
    flip.className = 'plat-flip';
    anim = document.createElement('div');
    anim.className = 'plat-anim';
    img = document.createElement('img');
    img.src = cfg.src;
    img.alt = '';
    img.draggable = false;

    anim.appendChild(img);
    flip.appendChild(anim);
    root.appendChild(flip);
    document.body.appendChild(root);

    bubble = document.createElement('div');
    bubble.id = 'plat-bubble';
    document.body.appendChild(bubble);

    placeAt(-9999, -9999);

    if (cfg.clickable) root.addEventListener('click', onClick);

    img.addEventListener('load', function () {
      size.h = cfg.height;
      size.w = img.naturalWidth * (cfg.height / img.naturalHeight);
    });
  }

  var api = {
    start: function (options) {
      if (started) return api;
      cfg = Object.assign({}, DEFAULTS, options || {});

      var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (reduced) return api;

      var go = function () {
        started = true;
        build();
        schedule(cfg.firstDelay);
        document.addEventListener('visibilitychange', function () {
          if (document.hidden) clearTimeout(timer);
          else if (!busy) schedule(3000);
        });
      };

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', go);
      } else {
        go();
      }
      return api;
    },
    // Fire a specific stunt: 'waddle', 'peek', 'mischief', 'slide', 'snooze'
    play: function (name) {
      var map = {
        waddle: waddleAcross, peek: peek, mischief: mischief,
        slide: bellySlide, snooze: snooze
      };
      if (!started || !map[name]) return Promise.resolve();
      clearTimeout(timer);
      return run(map[name]).then(function () {
        schedule(rand(cfg.gapMin, cfg.gapMax));
      });
    },
    stop: function () {
      clearTimeout(timer);
      if (root) hide();
    }
  };

  global.PlatypusMascot = api;

  if (global.PLATYPUS_CONFIG) api.start(global.PLATYPUS_CONFIG);
})(window);
