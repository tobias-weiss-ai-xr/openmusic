import { OfflineAudioContext } from 'web-audio-api';
import type { FilterConfig } from '../config.js';

/** Bandpass filter effect with LFO modulation for dub techno sweeps. */
export class FilterEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: FilterConfig;
  private filter: ReturnType<OfflineAudioContext['createBiquadFilter']>;
  private lfo: ReturnType<OfflineAudioContext['createOscillator']>;
  private lfoGain: ReturnType<OfflineAudioContext['createGain']>;

  constructor(private ctx: OfflineAudioContext, config: FilterConfig) {
    this.config = config;

    this.input = ctx.createGain();
    this.filter = ctx.createBiquadFilter();
    this.lfo = ctx.createOscillator();
    this.lfoGain = ctx.createGain();
    this.output = ctx.createGain();

    this.applyConfig();

    this.lfo.connect(this.lfoGain);
    this.lfoGain.connect(this.filter.frequency);
    this.lfo.start(0);

    if (config.enabled) {
      this.input.connect(this.filter);
      this.filter.connect(this.output);
    } else {
      this.input.connect(this.output);
    }
  }

  private applyConfig(): void {
    const c = this.config;
    this.filter.type = c.type;
    this.filter.frequency.value = c.frequency;
    this.filter.Q.value = c.Q;

    this.lfo.type = 'sine';
    this.lfo.frequency.value = c.lfoRate;
    this.lfoGain.gain.value = c.lfoDepth;
  }

  setParam(param: string, value: number): void {
    switch (param) {
      case 'frequency': this.filter.frequency.value = value; break;
      case 'Q': this.filter.Q.value = value; break;
      case 'lfoRate': this.lfo.frequency.value = value; break;
      case 'lfoDepth': this.lfoGain.gain.value = value; break;
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new FilterEffect(ctx, this.config);
    source.connect(effect.input);
    effect.output.connect(ctx.destination);
    source.start(0);

    return await ctx.startRendering();
  }
}
