import { test, expect, describe } from 'vitest';
import { OfflineAudioContext, AudioBuffer } from 'web-audio-api';
import { FilterEffect } from './filter.js';
import type { FilterConfig } from '../config.js';

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
      data[i] = Math.sin(2 * Math.PI * 440 * i / SAMPLE_RATE) * 0.5;
    }
  }
  return buf;
}

const defaultConfig: FilterConfig = {
  type: 'bandpass',
  frequency: 800,
  Q: 2,
  lfoRate: 0.2,
  lfoDepth: 100,
  enabled: true,
};

describe('FilterEffect', () => {
  test('creates filter nodes and connects them', () => {
    const ctx = makeContext();
    const effect = new FilterEffect(ctx, defaultConfig);

    expect(effect.input).toBeDefined();
    expect(effect.output).toBeDefined();
  });

  test('processes buffer and returns AudioBuffer', async () => {
    const ctx = makeContext();
    const effect = new FilterEffect(ctx, defaultConfig);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);

    expect(output).toBeInstanceOf(AudioBuffer);
    expect(output.numberOfChannels).toBe(2);
    expect(output.length).toBe(input.length);
    expect(output.sampleRate).toBe(SAMPLE_RATE);
  });

  test('bandpass filter attenuates out-of-band frequencies', async () => {
    const ctx = makeContext();
    const buf = ctx.createBuffer(1, SAMPLE_RATE * DURATION, SAMPLE_RATE);
    const data = buf.getChannelData(0);
    for (let i = 0; i < data.length; i++) {
      data[i] = Math.sin(2 * Math.PI * 50 * i / SAMPLE_RATE) * 0.5;
    }

    const config: FilterConfig = { ...defaultConfig, frequency: 800, Q: 10 };
    const effect = new FilterEffect(ctx, config);

    const output = await effect.process(buf);
    const outData = output.getChannelData(0);

    let rmsInput = 0;
    let rmsOutput = 0;
    for (let i = 0; i < data.length; i++) {
      rmsInput += data[i] * data[i];
      rmsOutput += outData[i] * outData[i];
    }
    rmsInput = Math.sqrt(rmsInput / data.length);
    rmsOutput = Math.sqrt(rmsOutput / outData.length);

    expect(rmsOutput).toBeLessThan(rmsInput);
  });

  test('disabled effect passes signal through unchanged', async () => {
    const ctx = makeContext();
    const config: FilterConfig = { ...defaultConfig, enabled: false };
    const effect = new FilterEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const inCh = input.getChannelData(0);
    const outCh = output.getChannelData(0);

    for (let i = 0; i < inCh.length; i++) {
      expect(outCh[i]).toBeCloseTo(inCh[i], 4);
    }
  });

  test('setParam updates filter parameters', async () => {
    const ctx = makeContext();
    const effect = new FilterEffect(ctx, defaultConfig);

    effect.setParam('frequency', 1200);
    effect.setParam('Q', 4);
    effect.setParam('lfoRate', 0.5);
    effect.setParam('lfoDepth', 200);

    const output = await effect.process(makeBuffer(ctx));
    expect(output).toBeInstanceOf(AudioBuffer);
  });
});
