import { OfflineAudioContext } from 'web-audio-api';

/** Multi-tap delay configuration. */
export interface MultiTapDelayConfig {
  taps: Array<{
    time: number;
    feedback: number;
    pan: number;
    gain: number;
  }>;
  masterFeedback: number;
  wetDryMix: number;
  enabled: boolean;
}

/**
 * Multi-tap delay effect with programmable delay times per tap,
 * individual feedback, and pan controls.
 */
export class MultiTapDelayEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: MultiTapDelayConfig;
  private delays: ReturnType<OfflineAudioContext['createDelay']>[];
  private feedbacks: ReturnType<OfflineAudioContext['createGain']>[];
  private panners: ReturnType<OfflineAudioContext['createStereoPanner']>[];
  private tapGains: ReturnType<OfflineAudioContext['createGain']>[];
  private dry: ReturnType<OfflineAudioContext['createGain']>;
  private wetMerge: ReturnType<OfflineAudioContext['createGain']>;

  constructor(
    private ctx: OfflineAudioContext,
    config: MultiTapDelayConfig
  ) {
    this.config = config;

    this.input = ctx.createGain();
    this.dry = ctx.createGain();
    this.wetMerge = ctx.createGain();
    this.output = ctx.createGain();

    const numTaps = config.taps.length;
    this.delays = [];
    this.feedbacks = [];
    this.panners = [];
    this.tapGains = [];

    for (let i = 0; i < numTaps; i++) {
      const delay = ctx.createDelay(5);
      const feedback = ctx.createGain();
      const panner = ctx.createStereoPanner();
      const tapGain = ctx.createGain();

      this.delays.push(delay);
      this.feedbacks.push(feedback);
      this.panners.push(panner);
      this.tapGains.push(tapGain);

      delay.delayTime.value = config.taps[i].time;
      feedback.gain.value = config.taps[i].feedback;
      panner.pan.value = config.taps[i].pan;
      tapGain.gain.value = config.taps[i].gain;
    }

    this.applyConfig();

    this.input.connect(this.dry);
    this.dry.connect(this.wetMerge);
    this.wetMerge.connect(this.output);

    for (let i = 0; i < numTaps; i++) {
      this.input.connect(this.delays[i]);
      this.delays[i].connect(this.feedbacks[i]);
      this.feedbacks[i].connect(this.delays[i]);
      this.feedbacks[i].connect(this.panners[i]);
      this.panners[i].connect(this.tapGains[i]);
      this.tapGains[i].connect(this.wetMerge);
    }
  }

  private applyConfig(): void {
    const c = this.config;

    for (let i = 0; i < c.taps.length; i++) {
      this.feedbacks[i].gain.value = c.taps[i].feedback * c.masterFeedback;
      this.tapGains[i].gain.value = c.enabled ? c.taps[i].gain : 0;
    }

    const mixRatio = c.wetDryMix / 100;
    this.wetMerge.gain.value = c.enabled ? mixRatio : 0;
    this.dry.gain.value = c.enabled ? 1 - mixRatio : 1;
  }

  setParam(param: string, value: number): void {
    const parts = param.split('_');
    if (parts.length !== 2) return;

    const tapIndex = parseInt(parts[1], 10);
    const prop = parts[0];

    if (tapIndex >= 0 && tapIndex < this.config.taps.length) {
      switch (prop) {
        case 'time':
          this.delays[tapIndex].delayTime.value = value;
          break;
        case 'feedback':
          this.feedbacks[tapIndex].gain.value = value * this.config.masterFeedback;
          break;
        case 'pan':
          this.panners[tapIndex].pan.value = value;
          break;
        case 'gain':
          this.tapGains[tapIndex].gain.value = value;
          break;
      }
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new MultiTapDelayEffect(ctx, this.config);
    source.connect(effect.input);
    effect.output.connect(ctx.destination);
    source.start(0);

    return await ctx.startRendering();
  }
}
