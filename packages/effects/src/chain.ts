import { OfflineAudioContext } from 'web-audio-api';
import { DelayEffect } from './effects/delay.js';
import { ReverbEffect } from './effects/reverb.js';
import { FilterEffect } from './effects/filter.js';
import { DistortionEffect } from './effects/distortion.js';
import { VinylEffect } from './effects/vinyl.js';
import { TapeSaturationEffect } from './effects/tape_saturation.js';
import { MultiTapDelayEffect } from './effects/multi_tap_delay.js';
import { GranularDelayEffect } from './effects/granular_delay.js';
import type { EffectsConfig } from './config.js';

type EffectName = 'delay' | 'reverb' | 'filter' | 'distortion' | 'vinyl' | 'tapeSaturation' | 'multiTapDelay' | 'granularDelay';

/** Complete dub techno effects chain: filter, distortion, delay, reverb, vinyl. */
export class DubTechnoEffectsChain {
  private config: EffectsConfig;
  private effects: Map<EffectName, { setParam: (param: string, value: number) => void }>;

  constructor(config: EffectsConfig) {
    this.config = config;
    this.effects = new Map();
  }

  setParam(effectName: EffectName, paramName: string, value: number): void {
    const effect = this.effects.get(effectName);
    if (effect) {
      effect.setParam(paramName, value);
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const duration = length / sampleRate;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const filter = new FilterEffect(ctx, this.config.filter);
    const distortion = new DistortionEffect(ctx, this.config.distortion);
    const delay = new DelayEffect(ctx, this.config.delay);
    const reverb = new ReverbEffect(ctx, this.config.reverb);
    const vinyl = new VinylEffect(ctx, this.config.vinyl, duration);
    const tapeSaturation = new TapeSaturationEffect(ctx, this.config.tapeSaturation);
    const multiTapDelay = new MultiTapDelayEffect(ctx, this.config.multiTapDelay);
    const granularDelay = new GranularDelayEffect(ctx, this.config.granularDelay);

    this.effects.set('filter', filter);
    this.effects.set('distortion', distortion);
    this.effects.set('delay', delay);
    this.effects.set('reverb', reverb);
    this.effects.set('vinyl', vinyl);
    this.effects.set('tapeSaturation', tapeSaturation);
    this.effects.set('multiTapDelay', multiTapDelay);
    this.effects.set('granularDelay', granularDelay);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    source.connect(filter.input);
    filter.output.connect(distortion.input);
    distortion.output.connect(delay.input);
    delay.output.connect(reverb.input);
    reverb.output.connect(vinyl.input);
    vinyl.output.connect(tapeSaturation.input);
    tapeSaturation.output.connect(multiTapDelay.input);
    multiTapDelay.output.connect(granularDelay.input);
    granularDelay.output.connect(ctx.destination);

    source.start(0);

    return await ctx.startRendering();
  }
}
