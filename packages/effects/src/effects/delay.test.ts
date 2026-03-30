import { test, expect, describe } from 'vitest';
import { OfflineAudioContext, AudioBuffer } from 'web-audio-api';
import { DelayEffect } from './delay.js';
import type { DelayConfig } from '../config.js';

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

const defaultConfig: DelayConfig = {
  primaryTime: 0.375,
  primaryFeedback: 0.4,
  primaryMix: 0.5,
  secondaryTime: 0.28125,
  secondaryFeedback: 0.3,
  secondaryMix: 0.4,
  enabled: true,
};

describe('DelayEffect', () => {
  test('creates delay nodes and connects them', () => {
    const ctx = makeContext();
    const effect = new DelayEffect(ctx, defaultConfig);

    expect(effect.input).toBeDefined();
    expect(effect.output).toBeDefined();
  });

  test('processes buffer and returns AudioBuffer', async () => {
    const ctx = makeContext();
    const effect = new DelayEffect(ctx, defaultConfig);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);

    expect(output).toBeInstanceOf(AudioBuffer);
    expect(output.numberOfChannels).toBe(2);
    expect(output.length).toBe(input.length);
    expect(output.sampleRate).toBe(SAMPLE_RATE);
  });

  test('delayed signal is audible after delay time', async () => {
    const ctx = makeContext();
    const config: DelayConfig = {
      ...defaultConfig,
      primaryTime: 0.1,
      primaryFeedback: 0,
      primaryMix: 1,
      secondaryTime: 0,
      secondaryFeedback: 0,
      secondaryMix: 0,
    };
    const effect = new DelayEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const channel = output.getChannelData(0);

    const delaySamples = Math.floor(0.1 * SAMPLE_RATE);
    let maxBeforeDelay = 0;
    for (let i = 0; i < delaySamples; i++) {
      maxBeforeDelay = Math.max(maxBeforeDelay, Math.abs(channel[i]));
    }

    let maxAfterDelay = 0;
    for (let i = delaySamples; i < channel.length; i++) {
      maxAfterDelay = Math.max(maxAfterDelay, Math.abs(channel[i]));
    }

    expect(maxAfterDelay).toBeGreaterThan(maxBeforeDelay);
  });

  test('feedback creates repeating echoes', async () => {
    const ctx = makeContext();
    const config: DelayConfig = {
      ...defaultConfig,
      primaryTime: 0.1,
      primaryFeedback: 0.5,
      primaryMix: 1,
      secondaryTime: 0,
      secondaryFeedback: 0,
      secondaryMix: 0,
    };
    const effect = new DelayEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const channel = output.getChannelData(0);

    const echo2Start = Math.floor(0.2 * SAMPLE_RATE);
    let maxAtEcho2 = 0;
    for (let i = echo2Start; i < echo2Start + 100; i++) {
      maxAtEcho2 = Math.max(maxAtEcho2, Math.abs(channel[i]));
    }

    expect(maxAtEcho2).toBeGreaterThan(0);
  });

  test('disabled effect passes signal through unchanged', async () => {
    const ctx = makeContext();
    const config: DelayConfig = { ...defaultConfig, enabled: false };
    const effect = new DelayEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const inCh = input.getChannelData(0);
    const outCh = output.getChannelData(0);

    for (let i = 0; i < inCh.length; i++) {
      expect(outCh[i]).toBeCloseTo(inCh[i], 4);
    }
  });

  test('setParam updates delay time', async () => {
    const ctx = makeContext();
    const effect = new DelayEffect(ctx, defaultConfig);

    effect.setParam('primaryTime', 0.5);
    effect.setParam('primaryFeedback', 0.6);
    effect.setParam('primaryMix', 0.7);
    effect.setParam('secondaryTime', 0.25);
    effect.setParam('secondaryFeedback', 0.4);
    effect.setParam('secondaryMix', 0.3);

    const output = await effect.process(makeBuffer(ctx));
    expect(output).toBeInstanceOf(AudioBuffer);
  });
});
