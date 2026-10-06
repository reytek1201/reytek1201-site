// REYTEK deck: a turntable voice. Plays one decoded track at any signed rate
// (forward, slowed, stopped, reversed) so scratching, backspins and power-downs
// come from the same physics that turns the platter.
// Clean playback: 4-point Hermite resampling, no added surface noise, and a
// short fade whenever the needle lands or lifts so it never clicks.
class DeckProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.L = null; this.R = null; this.len = 0; this.bufRate = sampleRate;
    this.pos = 0; this.rate = 0; this.cur = 0; this.k = 0.0016;
    this.gain = 1; this.needle = false; this.amp = 0; this.id = -1; this.seq = 0;
    this.count = 0;
    this.port.onmessage = (e) => {
      const m = e.data;
      if (m.t === 'load') {
        this.L = m.L; this.R = m.R || m.L; this.len = m.L.length; this.bufRate = m.sr;
        this.id = m.id; this.gain = m.gain || 1; this.pos = (m.at || 0) * m.sr; this.seq = m.seq || 0;
      } else if (m.t === 'seek') {
        this.pos = m.at * this.bufRate; this.seq = m.seq || this.seq;
      } else if (m.t === 'rate') {
        this.rate = m.v;
      } else if (m.t === 'needle') {
        this.needle = !!m.v;
      }
    };
  }
  sample(B, i0, f) {
    const n = this.len;
    const xm = B[i0 > 0 ? i0 - 1 : 0], x0 = B[i0], x1 = B[i0 + 1 < n ? i0 + 1 : n - 1], x2 = B[i0 + 2 < n ? i0 + 2 : n - 1];
    const c1 = 0.5 * (x1 - xm), c2 = xm - 2.5 * x0 + 2 * x1 - 0.5 * x2, c3 = 0.5 * (x2 - xm) + 1.5 * (x0 - x1);
    return ((c3 * f + c2) * f + c1) * f + x0;
  }
  process(inputs, outputs) {
    const out = outputs[0], oL = out[0], oR = out[1] || out[0], n = oL.length;
    const L = this.L, R = this.R, len = this.len, step = this.bufRate / sampleRate, g = this.gain;
    const ampTarget = this.needle ? 1 : 0, ampK = 1 / (sampleRate * 0.006);   // ~6 ms fade in/out
    for (let i = 0; i < n; i++) {
      this.cur += (this.rate - this.cur) * this.k;
      this.amp += Math.max(-ampK, Math.min(ampK, ampTarget - this.amp));
      let sl = 0, sr = 0;
      if (L && this.amp > 0) {
        const p = this.pos, i0 = Math.floor(p);
        if (i0 >= 0 && i0 < len - 1) {
          const f = p - i0, a = g * this.amp;
          sl = this.sample(L, i0, f) * a;
          sr = this.sample(R, i0, f) * a;
        }
      }
      if (this.needle) this.pos += this.cur * step;
      oL[i] = sl; oR[i] = sr;
    }
    this.count += n;
    if (this.count >= 4096) {   // ~11 position reports a second: enough to sync, light on the audio thread
      this.count = 0;
      this.port.postMessage({ pos: this.pos / this.bufRate, id: this.id, seq: this.seq });
    }
    return true;
  }
}
registerProcessor('deck', DeckProcessor);
