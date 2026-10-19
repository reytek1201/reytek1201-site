/* ---------- one player for the whole site: the Music page's rows drive it, and it keeps playing across pages ---------- */
(() => {
  window.RTPlayer = window.RTPlayer || (() => {
    const audio = new Audio(); audio.preload = 'none';
    const p = { audio, src: null, title: null, queue: [] };
    p.play = (src, title, queue) => {
      if (queue) p.queue = queue;
      if (src !== p.src) { p.src = src; p.title = title; audio.src = src; }
      if (window.RTDeck && window.RTDeck.playing()) window.RTDeck.stop();
      return audio.play().catch(() => {});
    };
    p.pause = () => audio.pause();
    p.toggle = () => (audio.paused ? p.play(p.src, p.title) : p.pause());
    p.playing = () => !!p.src && !audio.paused;
    audio.addEventListener('ended', () => {
      const i = p.queue.findIndex(q => q.src === p.src);
      if (i >= 0 && i < p.queue.length - 1) p.play(p.queue[i + 1].src, p.queue[i + 1].title);
    });
    return p;
  })();

  /* lock screen, car display and headset buttons: the plain audio element is what keeps playing with the screen off */
  (() => {
    const ms = navigator.mediaSession;
    if (!ms || typeof MediaMetadata === 'undefined') return;
    const P = window.RTPlayer, a = P.audio;
    const at = () => P.queue.findIndex(q => q.src === P.src);
    const meta = () => {
      if (!P.title) return;
      const q = P.queue[at()];
      try { ms.metadata = new MediaMetadata({ title: P.title, artist: 'Reytek', album: 'reytek1201.com', artwork: q && q.cover ? [{ src: q.cover, sizes: '640x640', type: 'image/webp' }] : [] }); } catch (e) {}
    };
    const go = d => { const q = P.queue[at() + d]; if (q) P.play(q.src, q.title); };
    const set = (name, fn) => { try { ms.setActionHandler(name, fn); } catch (e) {} };
    const pos = () => { try { if (a.duration && isFinite(a.duration)) ms.setPositionState({ duration: a.duration, position: Math.min(a.currentTime, a.duration), playbackRate: a.playbackRate || 1 }); } catch (e) {} };
    ['play', 'playing', 'loadedmetadata'].forEach(ev => a.addEventListener(ev, () => { meta(); ms.playbackState = 'playing'; }));
    a.addEventListener('pause', () => { ms.playbackState = 'paused'; });
    ['loadedmetadata', 'seeked', 'play', 'pause', 'ratechange'].forEach(ev => a.addEventListener(ev, pos));
    set('play', () => { a.play().catch(() => {}); });
    set('pause', () => a.pause());
    set('previoustrack', () => { if (a.currentTime > 3 || at() <= 0) a.currentTime = 0; else go(-1); });
    set('nexttrack', () => go(1));
    set('seekto', e => { a.currentTime = e.seekTime; });
    set('seekbackward', e => { a.currentTime = Math.max(0, a.currentTime - (e.seekOffset || 10)); });
    set('seekforward', e => { a.currentTime = Math.min(a.duration || 1e9, a.currentTime + (e.seekOffset || 10)); });
  })();

  /* everything on the site that makes sound: this player, the turntable, and the homepage's synthesized loop */
  window.RTSite = window.RTSite || {
    sounding() { try { const P = window.RTPlayer, D = window.RTDeck, A = window.RTAmbient; return !!((P && P.playing()) || (D && D.playing && D.playing()) || (A && A.playing())); } catch (e) { return false; } },
    // every step on its own, so one failing can't leave another sound running; the turntable also stops mid-load, mid-backspin or mid-gap
    quiet() {
      const P = window.RTPlayer, D = window.RTDeck, A = window.RTAmbient;
      try { if (P && P.audio) P.audio.pause(); } catch (e) {}
      try { if (D && ((D.playing && D.playing()) || (D.active && D.active()))) D.stop(); } catch (e) {}
      try { if (A && A.silence) A.silence(); else if (A && A.playing()) A.stop(); } catch (e) {}
    }
  };
})();
