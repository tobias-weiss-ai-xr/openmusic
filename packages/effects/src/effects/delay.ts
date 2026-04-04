import { OfflineAudioContext } from 'web-audio-api';
import type { DelayConfig } from '../config.js';

/** Dub techno delay effect with configurable feedback and tap timing. */
export class DelayEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: DelayConfig;
  private primaryDelay: ReturnType<OfflineAudioContext['createDelay']>;
  private primaryFeedback: ReturnType<OfflineAudioContext['createGain']>;
  private secondaryDelay: ReturnType<OfflineAudioContext['createDelay']>;
  private secondaryFeedback: ReturnType<OfflineAudioContext['createGain']>;
  private primaryWet: ReturnType<OfflineAudioContext['createGain']>;
  private secondaryWet: ReturnType<OfflineAudioContext['createGain']>;
  private dry: ReturnType<OfflineAudioContext['createGain']>;
  private merge: ReturnType<OfflineAudioContext['createGain']>;

  constructor(private ctx: OfflineAudioContext, config: DelayConfig) {
    this.config = config;

    this.input = ctx.createGain();
    this.dry = ctx.createGain();
    this.merge = ctx.createGain();
    this.output = ctx.createGain();

    this.primaryDelay = ctx.createDelay(5);
    this.primaryFeedback = ctx.createGain();
    this.primaryWet = ctx.createGain();

    this.secondaryDelay = ctx.createDelay(5);
    this.secondaryFeedback = ctx.createGain();
    this.secondaryWet = ctx.createGain();

    this.applyConfig();

    this.input.connect(this.dry);
    this.dry.connect(this.merge);

    this.input.connect(this.primaryDelay);
    this.primaryDelay.connect(this.primaryWet);
    this.primaryDelay.connect(this.primaryFeedback);
    this.primaryFeedback.connect(this.primaryDelay);
    this.primaryWet.connect(this.merge);

    this.input.connect(this.secondaryDelay);
    this.secondaryDelay.connect(this.secondaryWet);
    this.secondaryDelay.connect(this.secondaryFeedback);
    this.secondaryFeedback.connect(this.secondaryDelay);
    this.secondaryWet.connect(this.merge);

    this.merge.connect(this.output);
  }

  private applyConfig(): void {
    const c = this.config;
    const primaryMix = c.enabled ? c.primaryMix : 0;
    const secondaryMix = c.enabled ? c.secondaryMix : 0;

    this.primaryDelay.delayTime.value = c.primaryTime;
    this.primaryFeedback.gain.value = Math.min(c.primaryFeedback, 0.94);
    this.primaryWet.gain.value = primaryMix;

    this.secondaryDelay.delayTime.value = c.secondaryTime;
    this.secondaryFeedback.gain.value = Math.min(c.secondaryFeedback, 0.94);
    this.secondaryWet.gain.value = secondaryMix;

    const totalWet = primaryMix + secondaryMix;
    this.dry.gain.value = totalWet > 0 ? 1 : 1;
  }

  setParam(param: string, value: number): void {
    switch (param) {
      case 'primaryTime': this.primaryDelay.delayTime.value = value; break;
      case 'primaryFeedback': this.primaryFeedback.gain.value = Math.min(value, 0.94); break;
      case 'primaryMix': this.primaryWet.gain.value = value; break;
      case 'secondaryTime': this.secondaryDelay.delayTime.value = value; break;
      case 'secondaryFeedback': this.secondaryFeedback.gain.value = Math.min(value, 0.94); break;
      case 'secondaryMix': this.secondaryWet.gain.value = value; break;
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new DelayEffect(ctx, this.config);
    source.connect(effect.input);
    effect.output.connect(ctx.destination);
    source.start(0);

    return await ctx.startRendering();
  }
}
