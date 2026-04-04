import { OfflineAudioContext } from 'web-audio-api';
import type { ReverbConfig } from '../config.js';

function generateImpulseResponse(
  ctx: OfflineAudioContext,
  duration: number,
  decay: number,
) {
  const length = Math.ceil(ctx.sampleRate * duration);
  const buffer = ctx.createBuffer(2, length, ctx.sampleRate);

  for (let ch = 0; ch < 2; ch++) {
    const data = buffer.getChannelData(ch);
    for (let i = 0; i < length; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay);
    }
  }

  return buffer;
}

/** Reverb effect using convolution with configurable decay and pre-delay. */
export class ReverbEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: ReverbConfig;
  private convolver: ReturnType<OfflineAudioContext['createConvolver']>;
  private wet: ReturnType<OfflineAudioContext['createGain']>;
  private dry: ReturnType<OfflineAudioContext['createGain']>;
  private inputFilter: ReturnType<OfflineAudioContext['createBiquadFilter']>;
  private preDelay: ReturnType<OfflineAudioContext['createDelay']>;
  private merge: ReturnType<OfflineAudioContext['createGain']>;

  constructor(private ctx: OfflineAudioContext, config: ReverbConfig) {
    this.config = config;

    this.input = ctx.createGain();
    this.inputFilter = ctx.createBiquadFilter();
    this.preDelay = ctx.createDelay(0.1);
    this.convolver = ctx.createConvolver();
    this.wet = ctx.createGain();
    this.dry = ctx.createGain();
    this.merge = ctx.createGain();
    this.output = ctx.createGain();

    this.applyConfig();

    if (config.enabled) {
      this.input.connect(this.inputFilter);
      this.inputFilter.connect(this.preDelay);
      this.inputFilter.connect(this.dry);
      this.preDelay.connect(this.convolver);
      this.convolver.connect(this.wet);
      this.dry.connect(this.merge);
      this.wet.connect(this.merge);
      this.merge.connect(this.output);
    } else {
      this.input.connect(this.dry);
      this.dry.connect(this.output);
    }
  }

  private applyConfig(): void {
    const c = this.config;
    this.inputFilter.type = 'bandpass';
    this.inputFilter.frequency.value = c.inputFilterFreq;
    this.inputFilter.Q.value = c.inputFilterQ;
    this.preDelay.delayTime.value = c.preDelay / 1000;
    this.wet.gain.value = c.enabled ? c.mix : 0;
    this.dry.gain.value = c.enabled ? 1 - c.mix : 1;

    this.convolver.buffer = generateImpulseResponse(this.ctx, c.decay, 2.5);
  }

  setParam(param: string, value: number): void {
    switch (param) {
      case 'mix': this.wet.gain.value = value; this.dry.gain.value = 1 - value; break;
      case 'decay': {
        this.convolver.buffer = generateImpulseResponse(this.ctx, value, 2.5);
        break;
      }
      case 'inputFilterFreq': this.inputFilter.frequency.value = value; break;
      case 'inputFilterQ': this.inputFilter.Q.value = value; break;
      case 'preDelay': this.preDelay.delayTime.value = value / 1000; break;
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new ReverbEffect(ctx, this.config);
    source.connect(effect.input);
    effect.output.connect(ctx.destination);
    source.start(0);

    return await ctx.startRendering();
  }
}
