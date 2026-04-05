import { OfflineAudioContext } from 'web-audio-api';
import type { TapeSaturationConfig } from '../config.js';

/**
 * Tape saturation effect using tanh soft-clipping.
 * Adds warm, analog-style saturation to audio.
 */
export class TapeSaturationEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: TapeSaturationConfig;
  private shaper: ReturnType<OfflineAudioContext['createWaveShaper']>;
  private wet: ReturnType<OfflineAudioContext['createGain']>;
  private dry: ReturnType<OfflineAudioContext['createGain']>;
  private merge: ReturnType<OfflineAudioContext['createGain']>;
  private biasOsc: ReturnType<OfflineAudioContext['createOscillator']>;
  private biasGain: ReturnType<OfflineAudioContext['createGain']>;

  constructor(
    private ctx: OfflineAudioContext,
    config: TapeSaturationConfig
  ) {
    this.config = config;

    this.input = ctx.createGain();
    this.shaper = ctx.createWaveShaper();
    this.wet = ctx.createGain();
    this.dry = ctx.createGain();
    this.merge = ctx.createGain();
    this.biasOsc = ctx.createOscillator();
    this.biasGain = ctx.createGain();
    this.output = ctx.createGain();

    this.applyConfig();

    this.input.connect(this.dry);
    this.input.connect(this.shaper);
    this.shaper.connect(this.wet);
    this.dry.connect(this.merge);
    this.wet.connect(this.merge);
    this.merge.connect(this.output);

    this.biasOsc.connect(this.biasGain);
    this.biasGain.connect(this.output);
    this.biasOsc.start(0);
  }

  private applyConfig(): void {
    const c = this.config;
    const driveNorm = c.drive / 10;

    // Generate tanh soft-clip curve
    const curve = this.makeTanhCurve(driveNorm);
    this.shaper.curve = curve;
    this.shaper.oversample = '4x';

    const mixRatio = c.wetDryMix / 100;
    this.wet.gain.value = c.enabled ? mixRatio : 0;
    this.dry.gain.value = c.enabled ? 1 - mixRatio : 1;

    if (c.biasTone) {
      this.biasOsc.frequency.value = c.biasTone.frequency;
      this.biasGain.gain.value = c.biasTone.amplitude;
    } else {
      this.biasGain.gain.value = 0;
    }
  }

  private makeTanhCurve(drive: number): Float32Array {
    const samples = 44100;
    const curve = new Float32Array(samples);
    const k = drive;

    for (let i = 0; i < samples; i++) {
      const x = (i * 2) / samples - 1;
      curve[i] = Math.tanh(k * x) / (Math.tanh(k) + 1e-7);
    }

    return curve;
  }

  setParam(param: string, value: number): void {
    switch (param) {
      case 'drive': {
        const curve = this.makeTanhCurve(value / 10);
        this.shaper.curve = curve;
        break;
      }
      case 'wetDryMix': {
        const mixRatio = value / 100;
        this.wet.gain.value = mixRatio;
        this.dry.gain.value = 1 - mixRatio;
        break;
      }
      case 'biasFrequency':
        this.biasOsc.frequency.value = value;
        break;
      case 'biasAmplitude':
        this.biasGain.gain.value = value;
        break;
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new TapeSaturationEffect(ctx, this.config);
    source.connect(effect.input);
    effect.output.connect(ctx.destination);
    source.start(0);

    return await ctx.startRendering();
  }
}
