import { OfflineAudioContext } from 'web-audio-api';
import type { VinylConfig } from '../config.js';

function generateCrackleBuffer(ctx: OfflineAudioContext, duration: number) {
  const length = Math.ceil(ctx.sampleRate * duration);
  const buffer = ctx.createBuffer(2, length, ctx.sampleRate);

  for (let ch = 0; ch < 2; ch++) {
    const data = buffer.getChannelData(ch);
    let lastSpike = 0;
    for (let i = 0; i < length; i++) {
      const t = i / ctx.sampleRate;
      if (t - lastSpike > 0.01 + Math.random() * 0.05) {
        data[i] = (Math.random() * 2 - 1) * 0.3;
        lastSpike = t;
      } else {
        data[i] = (Math.random() * 2 - 1) * 0.02;
      }
    }
  }

  return buffer;
}

function generateHissBuffer(ctx: OfflineAudioContext, duration: number) {
  const length = Math.ceil(ctx.sampleRate * duration);
  const buffer = ctx.createBuffer(2, length, ctx.sampleRate);

  for (let ch = 0; ch < 2; ch++) {
    const data = buffer.getChannelData(ch);
    for (let i = 0; i < length; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.1;
    }
  }

  return buffer;
}

export class VinylEffect {
  input: ReturnType<OfflineAudioContext['createGain']>;
  output: ReturnType<OfflineAudioContext['createGain']>;
  private config: VinylConfig;
  private crackleGain: ReturnType<OfflineAudioContext['createGain']>;
  private hissGain: ReturnType<OfflineAudioContext['createGain']>;
  private dry: ReturnType<OfflineAudioContext['createGain']>;
  private merge: ReturnType<OfflineAudioContext['createGain']>;

  constructor(
    private ctx: OfflineAudioContext,
    config: VinylConfig,
    private duration = 10,
  ) {
    this.config = config;

    this.input = ctx.createGain();
    this.crackleGain = ctx.createGain();
    this.hissGain = ctx.createGain();
    this.dry = ctx.createGain();
    this.merge = ctx.createGain();
    this.output = ctx.createGain();

    this.applyConfig();
    this.input.connect(this.dry);
    this.dry.connect(this.merge);
    this.merge.connect(this.output);
  }

  private applyConfig(): void {
    const c = this.config;
    this.crackleGain.gain.value = c.enabled ? c.level : 0;
    this.hissGain.gain.value = c.enabled ? c.hissLevel : 0;
    this.dry.gain.value = 1;
  }

  setParam(param: string, value: number): void {
    switch (param) {
      case 'level': this.crackleGain.gain.value = value; break;
      case 'hissLevel': this.hissGain.gain.value = value; break;
    }
  }

  async process(inputBuffer: AudioBuffer) {
    const { numberOfChannels, length, sampleRate } = inputBuffer;
    const duration = length / sampleRate;
    const ctx = new OfflineAudioContext(numberOfChannels, length, sampleRate);

    const source = ctx.createBufferSource();
    source.buffer = inputBuffer as any;

    const effect = new VinylEffect(ctx, this.config, duration);

    source.connect(effect.input);

    if (this.config.enabled) {
      const crackleBuf = generateCrackleBuffer(ctx, duration);
      const crackleSrc = ctx.createBufferSource();
      crackleSrc.buffer = crackleBuf;
      crackleSrc.connect(effect.crackleGain);
      effect.crackleGain.connect(effect.merge);
      crackleSrc.start(0);

      const hissBuf = generateHissBuffer(ctx, duration);
      const hissSrc = ctx.createBufferSource();
      hissSrc.buffer = hissBuf;
      hissSrc.connect(effect.hissGain);
      effect.hissGain.connect(effect.merge);
      hissSrc.start(0);
    }

    effect.output.connect(ctx.destination);
    source.start(0);

    return await ctx.startRendering();
  }
}
