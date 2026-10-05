// REYTEK deck: a turntable voice. Plays one decoded track at any signed rate
// (forward, slowed, stopped, reversed) so scratching, backspins and power-downs
// come from the same physics that turns the platter.
class DeckProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.L = null; this.R = null; this.len = 0; this.bufRate = sampleRate;
    this.pos = 0; this.rate = 0; this.cur = 0; this.k = 0.0016;
    this.gain = 1; this.needle = false; this.id = -1; this.seq = 0;
    this.count = 0; this.pop = 0; this.hiss = 0;
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
  process(inputs, outputs) {
    const out = outputs[0], oL = out[0], oR = out[1] || out[0], n = oL.length;
    const L = this.L, R = this.R, len = this.len, step = this.bufRate / sampleRate, g = this.gain;
    for (let i = 0; i < n; i++) {
      this.cur += (this.rate - this.cur) * this.k;
      const r = this.cur;
      let sl = 0, sr = 0;
      if (this.needle) {
        if (L) {
          const p = this.pos, i0 = Math.floor(p);
          if (i0 >= 0 && i0 < len - 1) {
            const f = p - i0;
            sl = (L[i0] + (L[i0 + 1] - L[i0]) * f) * g;
            sr = (R[i0] + (R[i0 + 1] - R[i0]) * f) * g;
          }
        }
        // surface noise: soft hiss and the odd pop, scaled by how fast the groove moves
        const a = Math.min(1.5, Math.abs(r));
        this.hiss = this.hiss * 0.6 + (Math.random() - 0.5) * 0.4;
        const h = this.hiss * 0.0028 * a;
        if (Math.random() < 0.000035 * (0.25 + a)) this.pop = (Math.random() * 0.08 + 0.03) * (Math.random() < 0.5 ? -1 : 1);
        const pp = this.pop; this.pop *= 0.8;
        sl += h + pp; sr += h + pp * 0.85;
        this.pos += r * step;
      }
      oL[i] = sl; oR[i] = sr;
    }
    this.count += n;
    if (this.count >= 1024) {
      this.count = 0;
      this.port.postMessage({ pos: this.pos / this.bufRate, id: this.id, seq: this.seq });
    }
    return true;
  }
}
registerProcessor('deck', DeckProcessor);
