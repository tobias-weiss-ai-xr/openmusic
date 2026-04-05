import { OfflineAudioContext } from 'web-audio-api';

/** Granular delay effect configuration. */
export interface GranularDelayConfig {
  grainSizeMs: number;
  grainDensity: number;
  randomizationAmount: number;
  feedback: number;
  wetDryMix: number;
  enabled: boolean;
}

/**
 * Granular delay effect using web-audio-api.
 * Creates textured, evolving repeats with grain-based processing.
 */
export class GranularDelayEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: GranularDelayConfig;
  private delayNodes: ReturnType<OfflineAudioContext['createDelay']>[];
  private grainGains: ReturnType<OfflineAudioContext['createGain']>[];
  private feedbackGain: ReturnType<OfflineAudioContext['createGain']>;
  private wetGain: ReturnType<OfflineAudioContext['createGain']>;
  private dryGain: ReturnType<OfflineAudioContext['createGain']>;
  private merge: ReturnType<OfflineAudioContext['createGain']>;

  constructor(
    private ctx: OfflineAudioContext,
    config: GranularDelayConfig
  ) {
    this.config = config;
    this.delayNodes = [];
    this.grainGains = [];

    this.input = ctx.createGain();
    this.feedbackGain = ctx.createGain();
    this.wetGain = ctx.createGain();
    this.dryGain = ctx.createGain();
    this.merge = ctx.createGain();
    this.output = ctx.createGain();

    this.buildGrainChain();
    this.applyConfig();
  }

  private buildGrainChain(): void {
    const numGrains = 8;
    const maxDelay = 2;

    for (let i = 0; i < numGrains; i++) {
      const delay = this.ctx.createDelay(maxDelay);
      const gain = this.ctx.createGain();

      const grainDelayMs = this.config.grainSizeMs * (i + 1);
      delay.delayTime.value = grainDelayMs / 1000;

      const randomOffset = ((Math.random() - 0.5) * this.config.randomizationAmount) / 100;
      delay.delayTime.value *= 1 + randomOffset;

      gain.gain.value = 1 / numGrains;

      this.delayNodes.push(delay);
      this.grainGains.push(gain);
    }

    this.input.connect(this.dryGain);
    this.dryGain.connect(this.merge);

    for (let i = 0; i < numGrains; i++) {
      this.input.connect(this.delayNodes[i]);
      this.delayNodes[i].connect(this.grainGains[i]);
      this.grainGains[i].connect(this.merge);
      this.grainGains[i].connect(this.feedbackGain);
      this.feedbackGain.connect(this.delayNodes[i]);
    }

    this.merge.connect(this.wetGain);
    this.wetGain.connect(this.output);
  }

  private applyConfig(): void {
    const c = this.config;
    const feedbackNorm = c.feedback / 100;
    this.feedbackGain.gain.value = feedbackNorm * 0.5;

    const mixRatio = c.wetDryMix / 100;
    this.wetGain.gain.value = c.enabled ? mixRatio : 0;
    this.dryGain.gain.value = c.enabled ? 1 - mixRatio : 1;
  }

  setParam(param: string, value: number): void {
    switch (param) {
      case 'grainSizeMs': {
        for (let i = 0; i < this.delayNodes.length; i++) {
          const delayMs = value * (i + 1);
          this.delayNodes[i].delayTime.value = delayMs / 1000;
        }
        break;
      }
      case 'feedback':
        this.feedbackGain.gain.value = (value / 100) * 0.5;
        break;
      case 'wetDryMix': {
        const mixRatio = value / 100;
        this.wetGain.gain.value = mixRatio;
        this.dryGain.gain.value = 1 - mixRatio;
        break;
      }
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const newCtx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = newCtx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new GranularDelayEffect(newCtx, this.config);
    source.connect(effect.input);
    effect.output.connect(newCtx.destination);
    source.start(0);

    return await newCtx.startRendering();
  }
}
