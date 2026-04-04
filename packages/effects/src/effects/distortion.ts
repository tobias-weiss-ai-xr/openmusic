import { OfflineAudioContext } from 'web-audio-api';
import type { DistortionConfig } from '../config.js';

function makeSoftClipCurve(amount: number): Float32Array {
  const samples = 44100;
  const curve = new Float32Array(samples);
  const k = amount * 100;

  for (let i = 0; i < samples; i++) {
    const x = (i * 2) / samples - 1;
    curve[i] = ((3 + k) * x * 20 * (Math.PI / 180)) / (Math.PI + k * Math.abs(x));
  }

  return curve;
}

/** Tape-style saturation effect for warm analog distortion. */
export class DistortionEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: DistortionConfig;
  private shaper: ReturnType<OfflineAudioContext['createWaveShaper']>;
  private wet: ReturnType<OfflineAudioContext['createGain']>;
  private dry: ReturnType<OfflineAudioContext['createGain']>;
  private merge: ReturnType<OfflineAudioContext['createGain']>;

  constructor(private ctx: OfflineAudioContext, config: DistortionConfig) {
    this.config = config;

    this.input = ctx.createGain();
    this.shaper = ctx.createWaveShaper();
    this.wet = ctx.createGain();
    this.dry = ctx.createGain();
    this.merge = ctx.createGain();
    this.output = ctx.createGain();

    this.applyConfig();

    this.input.connect(this.dry);
    this.input.connect(this.shaper);
    this.shaper.connect(this.wet);
    this.dry.connect(this.merge);
    this.wet.connect(this.merge);
    this.merge.connect(this.output);
  }

  private applyConfig(): void {
    const c = this.config;
    this.shaper.curve = makeSoftClipCurve(c.enabled ? c.amount : 0);
    this.shaper.oversample = '4x';
    this.wet.gain.value = c.enabled ? c.mix : 0;
    this.dry.gain.value = 1;
  }

  setParam(param: string, value: number): void {
    switch (param) {
      case 'amount': this.shaper.curve = makeSoftClipCurve(value); break;
      case 'mix': this.wet.gain.value = value; break;
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new DistortionEffect(ctx, this.config);
    source.connect(effect.input);
    effect.output.connect(ctx.destination);
    source.start(0);

    return await ctx.startRendering();
  }
}
