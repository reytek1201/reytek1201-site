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
