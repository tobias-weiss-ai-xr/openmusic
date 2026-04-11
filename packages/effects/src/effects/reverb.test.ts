import { test, expect, describe } from 'vitest';
import { OfflineAudioContext, AudioBuffer } from 'web-audio-api';
import { ReverbEffect } from './reverb.js';
import type { ReverbConfig } from '../config.js';

const SAMPLE_RATE = 44100;
const DURATION = 1;

function makeContext(): OfflineAudioContext {
  return new OfflineAudioContext(2, SAMPLE_RATE * DURATION, SAMPLE_RATE);
}

function makeBuffer(ctx: OfflineAudioContext): AudioBuffer {
  const buf = ctx.createBuffer(2, SAMPLE_RATE * DURATION, SAMPLE_RATE);
  for (let ch = 0; ch < 2; ch++) {
    const data = buf.getChannelData(ch);
    for (let i = 0; i < data.length; i++) {
      data[i] = Math.sin((2 * Math.PI * 440 * i) / SAMPLE_RATE) * 0.5;
    }
  }
  return buf;
}

const defaultConfig: ReverbConfig = {
  decay: 3.0,
  preDelay: 30,
  mix: 0.4,
  inputFilterFreq: 800,
  inputFilterQ: 2,
  enabled: true,
};

describe('ReverbEffect', () => {
  test('creates reverb nodes and connects them', () => {
    const ctx = makeContext();
    const effect = new ReverbEffect(ctx, defaultConfig);

    expect(effect.input).toBeDefined();
    expect(effect.output).toBeDefined();
  });

  test('processes buffer and returns AudioBuffer', async () => {
    const ctx = makeContext();
    const effect = new ReverbEffect(ctx, defaultConfig);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);

    expect(output).toBeInstanceOf(AudioBuffer);
    expect(output.numberOfChannels).toBe(2);
    expect(output.length).toBe(input.length);
    expect(output.sampleRate).toBe(SAMPLE_RATE);
  }, 15000);

  test('reverb tail extends beyond dry signal', async () => {
    const ctx = makeContext();
    const config: ReverbConfig = { ...defaultConfig, mix: 1, decay: 0.5 };
    const effect = new ReverbEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const channel = output.getChannelData(0);

    const lastQuarter = Math.floor(channel.length * 0.75);
    let maxInLastQuarter = 0;
    for (let i = lastQuarter; i < channel.length; i++) {
      maxInLastQuarter = Math.max(maxInLastQuarter, Math.abs(channel[i]));
    }

    expect(maxInLastQuarter).toBeGreaterThan(0);
  });

  test('disabled effect passes signal through unchanged', async () => {
    const ctx = makeContext();
    const config: ReverbConfig = { ...defaultConfig, enabled: false };
    const effect = new ReverbEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const inCh = input.getChannelData(0);
    const outCh = output.getChannelData(0);

    for (let i = 0; i < inCh.length; i++) {
      expect(outCh[i]).toBeCloseTo(inCh[i], 4);
    }
  });

  test('setParam updates reverb parameters', async () => {
    const ctx = makeContext();
    const effect = new ReverbEffect(ctx, defaultConfig);

    effect.setParam('mix', 0.7);
    effect.setParam('decay', 4.0);
    effect.setParam('inputFilterFreq', 1000);

    const output = await effect.process(makeBuffer(ctx));
    expect(output).toBeInstanceOf(AudioBuffer);
  });
});
