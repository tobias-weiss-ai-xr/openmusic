import { test, expect, describe } from 'vitest';
import { OfflineAudioContext, AudioBuffer } from 'web-audio-api';
import { DubTechnoEffectsChain } from './chain.js';
import { DEFAULT_EFFECTS_CONFIG, DEEP_DUB, MINIMAL_DUB, CLUB_DUB } from './config.js';

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

describe('DubTechnoEffectsChain', () => {
  test('creates chain with default config', () => {
    const chain = new DubTechnoEffectsChain(DEFAULT_EFFECTS_CONFIG);
    expect(chain).toBeDefined();
  });

  test('process returns AudioBuffer with correct properties', async () => {
    const ctx = makeContext();
    const chain = new DubTechnoEffectsChain(DEFAULT_EFFECTS_CONFIG);
    const input = makeBuffer(ctx);

    const output = await chain.process(input);

    expect(output).toBeInstanceOf(AudioBuffer);
    expect(output.numberOfChannels).toBe(input.numberOfChannels);
    expect(output.length).toBe(input.length);
    expect(output.sampleRate).toBe(input.sampleRate);
  });

  test('setParam updates effect parameters at runtime', async () => {
    const ctx = makeContext();
    const chain = new DubTechnoEffectsChain(DEFAULT_EFFECTS_CONFIG);
    const input = makeBuffer(ctx);

    chain.setParam('filter', 'frequency', 1200);
    chain.setParam('delay', 'primaryTime', 0.5);
    chain.setParam('reverb', 'decay', 5.0);
    chain.setParam('distortion', 'amount', 0.3);
    chain.setParam('vinyl', 'level', 0.2);

    const output = await chain.process(input);
    expect(output).toBeInstanceOf(AudioBuffer);
  });

  test('works with all preset configs', async () => {
    const ctx = makeContext();
    const input = makeBuffer(ctx);

    for (const preset of [MINIMAL_DUB, CLUB_DUB]) {
      const chain = new DubTechnoEffectsChain(preset);
      const output = await chain.process(input);
      expect(output).toBeInstanceOf(AudioBuffer);
      expect(output.numberOfChannels).toBe(2);
    }
  }, 15000);

  test('all effects disabled passes signal through', async () => {
    const ctx = makeContext();
    const config = {
      delay: { ...DEFAULT_EFFECTS_CONFIG.delay, enabled: false },
      reverb: { ...DEFAULT_EFFECTS_CONFIG.reverb, enabled: false },
      filter: { ...DEFAULT_EFFECTS_CONFIG.filter, enabled: false },
      distortion: { ...DEFAULT_EFFECTS_CONFIG.distortion, enabled: false },
      vinyl: { ...DEFAULT_EFFECTS_CONFIG.vinyl, enabled: false },
    };
    const chain = new DubTechnoEffectsChain(config);
    const input = makeBuffer(ctx);

    const output = await chain.process(input);
    const inCh = input.getChannelData(0);
    const outCh = output.getChannelData(0);

    for (let i = 0; i < inCh.length; i++) {
      expect(outCh[i]).toBeCloseTo(inCh[i], 4);
    }
  });
});
