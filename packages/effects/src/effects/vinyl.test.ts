import { test, expect, describe } from 'vitest';
import { OfflineAudioContext, AudioBuffer } from 'web-audio-api';
import { VinylEffect } from './vinyl.js';
import type { VinylConfig } from '../config.js';

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

const defaultConfig: VinylConfig = {
  level: 0.18,
  hissLevel: 0.1,
  enabled: true,
};

describe('VinylEffect', () => {
  test('creates vinyl nodes and connects them', () => {
    const ctx = makeContext();
    const effect = new VinylEffect(ctx, defaultConfig);

    expect(effect.input).toBeDefined();
    expect(effect.output).toBeDefined();
  });

  test('processes buffer and returns AudioBuffer', async () => {
    const ctx = makeContext();
    const effect = new VinylEffect(ctx, defaultConfig);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);

    expect(output).toBeInstanceOf(AudioBuffer);
    expect(output.numberOfChannels).toBe(2);
    expect(output.length).toBe(input.length);
    expect(output.sampleRate).toBe(SAMPLE_RATE);
  });

  test('adds noise to the signal', async () => {
    const ctx = makeContext();
    const config: VinylConfig = { level: 0.5, hissLevel: 0.3, enabled: true };
    const effect = new VinylEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const inCh = input.getChannelData(0);
    const outCh = output.getChannelData(0);

    let diff = 0;
    for (let i = 0; i < inCh.length; i++) {
      diff += Math.abs(outCh[i] - inCh[i]);
    }
    diff /= inCh.length;

    expect(diff).toBeGreaterThan(0);
  });

  test('disabled effect passes signal through unchanged', async () => {
    const ctx = makeContext();
    const config: VinylConfig = { ...defaultConfig, enabled: false };
    const effect = new VinylEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const inCh = input.getChannelData(0);
    const outCh = output.getChannelData(0);

    for (let i = 0; i < inCh.length; i++) {
      expect(outCh[i]).toBeCloseTo(inCh[i], 4);
    }
  });

  test('setParam updates vinyl parameters', async () => {
    const ctx = makeContext();
    const effect = new VinylEffect(ctx, defaultConfig);

    effect.setParam('level', 0.3);
    effect.setParam('hissLevel', 0.2);

    const output = await effect.process(makeBuffer(ctx));
    expect(output).toBeInstanceOf(AudioBuffer);
  });
});
