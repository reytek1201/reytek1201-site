/* ---------- Reytek Vision: the site's TV ----------
   Every video is a channel. The page shows a poster on standby; pressing it (or a channel in the guide) tunes in:
   a short scanline flash, the channel number on screen, then the YouTube player (privacy mode, controls off) with
   the site's own controls under the screen. The player's code loads only on tune-in. When a video starts, every
   other sound on the site stops; when the site's sound starts, the video pauses. Leaving the page removes the player. */
(() => {
  const track = (name, params) => { try { if (window.gtag) window.gtag('event', name, params); } catch (e) {} };
  const fmt = s => { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };

  window.RT.onPage(() => {
    const tv = document.getElementById('tv');
    if (!tv) return;
    let chans = [];
    try { chans = JSON.parse((document.getElementById('visData') || {}).textContent || '[]'); } catch (e) {}
    if (!chans.length) return;
    const $ = id => document.getElementById(id);
    const el = {
      vision: $('vision'), set: $('tvSet'), screen: $('tvScreen'), mount: $('tvVideo'), standby: $('tvStandby'), poster: $('tvPoster'),
      cue: $('tvCue'), osd: $('tvOsd'), stat: $('tvStatic'), end: $('tvEnd'), endK: $('tvEndK'), endT: $('tvEndT'), endGo: $('tvEndGo'), endStay: $('tvEndStay'),
      play: $('tvPlay'), seek: $('tvSeek'), time: $('tvTime'), mute: $('tvMute'), full: $('tvFull'), up: $('tvUp'), down: $('tvDown'),
      nowK: $('tvNowK'), nowT: $('tvNowT'), nowB: $('tvNowB'), nowLink: $('tvNowLink'), tally: $('tvTally'), live: $('tvLive')
    };
    const guide = [...document.querySelectorAll('.vg-chan')];
    const reduce = matchMedia('(prefers-reduced-motion: reduce)');
    const ac = new AbortController(), on = { signal: ac.signal };
    const YT_HOST = 'https://www.youtube-nocookie.com';
    const FS = el.set.requestFullscreen ? 'requestFullscreen' : el.set.webkitRequestFullscreen ? 'webkitRequestFullscreen' : null;
    let player = null, apiP = null, ready = false, idx = 0, tuned = false, st = -1, dragging = false;
    let osdT = 0, endT = 0, tuneSeq = 0;

    if (!FS) el.full.hidden = true;
    if (chans.length < 2) { el.up.disabled = true; el.down.disabled = true; }

    const setState = s => {
      tv.dataset.state = s;
      el.tally.textContent = { standby: 'Standby', tuning: 'Tuning', playing: 'On air', paused: 'Paused', ended: 'Signal ends' }[s] || '';
      const playing = s === 'playing';
      el.play.setAttribute('aria-pressed', playing ? 'true' : 'false');
      el.play.setAttribute('aria-label', playing ? 'Pause' : 'Play');
    };
    const posterUrl = c => /^https?:/.test(c.poster) ? c.poster : rtUrl(c.poster);
    const select = (i, announce) => {
      idx = (i + chans.length) % chans.length;
      const c = chans[idx];
      if (c.rgb) tv.style.setProperty('--vc', c.rgb); else tv.style.removeProperty('--vc');
      guide.forEach((li, n) => { li.classList.toggle('on', n === idx); li.querySelector('.tick').textContent = n === idx && tuned ? 'On air' : ''; });
      el.nowK.textContent = 'CH.' + c.n + (c.meta ? ' · ' + c.meta : '');
      el.nowT.textContent = c.title; el.nowB.textContent = c.blurb; el.nowB.hidden = !c.blurb;
      el.nowLink.href = 'https://www.youtube.com/watch?v=' + c.id;
      el.cue.textContent = 'CH.' + c.n;
      el.standby.setAttribute('aria-label', 'Tune in to channel ' + c.n + ': ' + c.title);
      if (!tuned && el.poster) { el.poster.src = posterUrl(c); }
      if (announce) el.live.textContent = 'Channel ' + c.n + ': ' + c.title;
    };
    const showOsd = text => {
      el.osd.textContent = text; el.osd.classList.add('on');
      clearTimeout(osdT); osdT = setTimeout(() => el.osd.classList.remove('on'), 2200);
    };
    const flash = () => {
      if (reduce.matches) return;
      el.stat.classList.remove('go'); void el.stat.offsetWidth; el.stat.classList.add('go');
    };
    const clearEnd = () => { clearInterval(endT); el.end.hidden = true; };

    const loadApi = () => apiP || (apiP = new Promise((res, rej) => {
      if (window.YT && window.YT.Player) return res();
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => { try { if (prev) prev(); } catch (e) {} res(); };
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api'; s.onerror = () => { apiP = null; rej(new Error('player')); };
      document.head.appendChild(s);
    }));

    const onState = e => {
      st = e.data;
      if (st === 1) {
        setState('playing');
        if (window.RTSite) window.RTSite.quiet();
        el.seek.disabled = false; el.mute.disabled = false;
      } else if (st === 2) setState('paused');
      else if (st === 0) onEnd();
    };
    const tune = async i => {
      const seq = ++tuneSeq;
      clearEnd();
      tuned = true;
      select(i, true);
      const c = chans[idx];
      el.standby.hidden = true;
      setState('tuning');
      flash(); showOsd('CH.' + c.n);
      if (window.RTSite) window.RTSite.quiet();   // the site's music stops the moment you tune in
      try { await loadApi(); } catch (e) {
        if (seq !== tuneSeq) return;
        tuned = false; el.standby.hidden = false; setState('standby'); select(idx);
        el.live.textContent = 'The player could not load. Use Watch on YouTube instead.';
        return;
      }
      if (seq !== tuneSeq) return;
      if (!player) {
        const d = document.createElement('div');
        el.mount.replaceChildren(d);
        const noFs = !document.fullscreenEnabled && !document.webkitFullscreenEnabled;   // iPhone: let the system player take over
        player = new YT.Player(d, {
          host: YT_HOST, videoId: c.id,
          playerVars: { autoplay: 1, controls: 0, rel: 0, playsinline: noFs ? 0 : 1, fs: 0, modestbranding: 1, iv_load_policy: 3, disablekb: 1, origin: location.origin },
          events: {
            onReady: () => { ready = true; try { player.playVideo(); } catch (e) {} },
            onStateChange: onState
          }
        });
      } else if (ready) { player.loadVideoById(c.id); }
      track('video_play', { video: c.id });
    };

    const onEnd = () => {
      setState('ended');
      el.endStay.hidden = chans.length < 2;
      if (chans.length > 1) {
        const nx = chans[(idx + 1) % chans.length];
        let n = 5;
        const paint = () => { el.endK.textContent = 'Next · CH.' + nx.n; el.endT.textContent = nx.title + ' in ' + n; };
        el.endGo.textContent = 'Tune now';
        el.endGo.onclick = () => tune(idx + 1);
        el.endStay.onclick = () => { clearEnd(); };
        paint(); el.end.hidden = false;
        clearInterval(endT);
        endT = setInterval(() => { n -= 1; if (n <= 0) { clearInterval(endT); tune(idx + 1); } else paint(); }, 1000);
      } else {
        el.endK.textContent = 'Signal ends'; el.endT.textContent = '';
        el.endGo.textContent = 'Watch again';
        el.endGo.onclick = () => { clearEnd(); try { player.seekTo(0, true); player.playVideo(); } catch (e) {} };
        el.end.hidden = false;
      }
      el.endGo.focus({ preventScroll: true });
    };

    // controls
    el.standby.addEventListener('click', () => tune(idx), on);
    guide.forEach((li, n) => li.querySelector('button').addEventListener('click', () => tune(n), on));
    el.up.addEventListener('click', () => tune(idx + 1), on);
    el.down.addEventListener('click', () => tune(idx - 1), on);
    el.play.addEventListener('click', () => {
      if (!tuned) return tune(idx);
      if (!player || !ready) return;
      try { if (st === 1) player.pauseVideo(); else { clearEnd(); player.playVideo(); } } catch (e) {}
    }, on);
    el.mute.addEventListener('click', () => {
      if (!player || !ready) return;
      try { const m = player.isMuted(); if (m) player.unMute(); else player.mute(); el.mute.setAttribute('aria-pressed', m ? 'false' : 'true'); el.mute.setAttribute('aria-label', m ? 'Mute' : 'Unmute'); } catch (e) {}
    }, on);
    el.seek.addEventListener('input', () => { dragging = true; try { el.time.textContent = fmt(el.seek.value / 1000 * player.getDuration()); } catch (e) {} }, on);
    el.seek.addEventListener('change', () => { dragging = false; try { player.seekTo(el.seek.value / 1000 * player.getDuration(), true); } catch (e) {} }, on);
    const fullOn = () => !!(document.fullscreenElement || document.webkitFullscreenElement);
    const toggleFull = () => {
      if (!FS) return;
      try { if (fullOn()) (document.exitFullscreen || document.webkitExitFullscreen).call(document); else el.set[FS](); } catch (e) {}
    };
    el.full.addEventListener('click', toggleFull, on);
    const fsChange = () => { el.full.setAttribute('aria-pressed', fullOn() ? 'true' : 'false'); };
    document.addEventListener('fullscreenchange', fsChange, on);
    document.addEventListener('webkitfullscreenchange', fsChange, on);

    // keyboard, while focus is on the TV or the guide: up/down channel, space play/pause, F full screen, M mute
    document.addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey || !el.vision.contains(e.target)) return;
      if (e.target.matches && e.target.matches('input')) return;
      const k = e.key;
      if (k === 'ArrowUp' && chans.length > 1) { e.preventDefault(); tune(idx - 1); }
      else if (k === 'ArrowDown' && chans.length > 1) { e.preventDefault(); tune(idx + 1); }
      else if ((k === 'f' || k === 'F') && FS) { e.preventDefault(); toggleFull(); }
      else if (k === 'm' || k === 'M') { e.preventDefault(); el.mute.click(); }
      else if (k === ' ' && !(e.target.closest && e.target.closest('button, a'))) { e.preventDefault(); el.play.click(); }
    }, on);

    // progress, and the handoff: if the site's sound starts while the video plays, the video pauses
    const poll = setInterval(() => {
      if (!player || !ready || typeof player.getCurrentTime !== 'function') return;
      try {
        const d = player.getDuration() || 0, t = player.getCurrentTime() || 0;
        if (!dragging) { el.seek.value = d ? Math.round(t / d * 1000) : 0; el.time.textContent = fmt(t); }
        if (st === 1 && window.RTSite && window.RTSite.sounding()) player.pauseVideo();
      } catch (e) {}
    }, 250);

    // a link ending in #<channel> selects it (standby: nothing plays until pressed)
    const fromHash = () => {
      const slug = decodeURIComponent((location.hash || '').slice(1));
      const i = chans.findIndex(c => c.slug === slug);
      if (i >= 0 && !tuned) select(i, false);
    };
    fromHash();
    addEventListener('hashchange', fromHash, on);
    select(idx, false);

    return () => {
      ac.abort(); clearInterval(poll); clearInterval(endT); clearTimeout(osdT);
      try { if (fullOn()) (document.exitFullscreen || document.webkitExitFullscreen).call(document); } catch (e) {}
      try { if (player && player.destroy) player.destroy(); } catch (e) {}
    };
  });
})();
