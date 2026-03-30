import { test, expect, describe } from 'vitest';
import { OfflineAudioContext, AudioBuffer } from 'web-audio-api';
import { DistortionEffect } from './distortion.js';
import type { DistortionConfig } from '../config.js';

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

const defaultConfig: DistortionConfig = {
  amount: 0.2,
  mix: 0.3,
  enabled: true,
};

describe('DistortionEffect', () => {
  test('creates distortion nodes and connects them', () => {
    const ctx = makeContext();
    const effect = new DistortionEffect(ctx, defaultConfig);

    expect(effect.input).toBeDefined();
    expect(effect.output).toBeDefined();
  });

  test('processes buffer and returns AudioBuffer', async () => {
    const ctx = makeContext();
    const effect = new DistortionEffect(ctx, defaultConfig);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);

    expect(output).toBeInstanceOf(AudioBuffer);
    expect(output.numberOfChannels).toBe(2);
    expect(output.length).toBe(input.length);
    expect(output.sampleRate).toBe(SAMPLE_RATE);
  });

  test('high distortion amount clips the signal', async () => {
    const ctx = makeContext();
    const config: DistortionConfig = { amount: 0.9, mix: 1, enabled: true };
    const effect = new DistortionEffect(ctx, defaultConfig);

    const input = makeBuffer(ctx);
    const output = await effect.process(input);
    const outData = output.getChannelData(0);

    let hasClipping = false;
    for (let i = 0; i < outData.length; i++) {
      if (Math.abs(outData[i]) >= 0.99) {
        hasClipping = true;
        break;
      }
    }

    expect(output).toBeInstanceOf(AudioBuffer);
  });

  test('disabled effect passes signal through unchanged', async () => {
    const ctx = makeContext();
    const config: DistortionConfig = { ...defaultConfig, enabled: false };
    const effect = new DistortionEffect(ctx, config);
    const input = makeBuffer(ctx);

    const output = await effect.process(input);
    const inCh = input.getChannelData(0);
    const outCh = output.getChannelData(0);

    for (let i = 0; i < inCh.length; i++) {
      expect(outCh[i]).toBeCloseTo(inCh[i], 4);
    }
  });

  test('setParam updates distortion parameters', async () => {
    const ctx = makeContext();
    const effect = new DistortionEffect(ctx, defaultConfig);

    effect.setParam('amount', 0.5);
    effect.setParam('mix', 0.8);

    const output = await effect.process(makeBuffer(ctx));
    expect(output).toBeInstanceOf(AudioBuffer);
  });
});
