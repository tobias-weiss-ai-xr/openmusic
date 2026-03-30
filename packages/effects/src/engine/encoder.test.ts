import { test, expect, describe, beforeAll, afterAll } from 'vitest';
import { existsSync, unlinkSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { encodeWav, encodeFlac, encodeMp3 } from './encoder.js';
import { OfflineAudioContext } from 'web-audio-api';
import { decodeWav } from './decoder.js';

const TEST_DIR = join(tmpdir(), 'openmusic-encoder-test');

function makeBuffer(sampleRate = 48000, channels = 2, numSamples = 48000) {
  const ctx = new OfflineAudioContext(channels, numSamples, sampleRate);
  const buf = ctx.createBuffer(channels, numSamples, sampleRate);
  for (let ch = 0; ch < channels; ch++) {
    const data = buf.getChannelData(ch);
    for (let i = 0; i < data.length; i++) {
      data[i] = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 0.5;
    }
  }
  return buf;
}

beforeAll(() => {
  mkdirSync(TEST_DIR, { recursive: true });
});

afterAll(() => {
  rmSync(TEST_DIR, { recursive: true, force: true });
});

describe('encodeWav', () => {
  test('writes a valid WAV file to disk', async () => {
    const filePath = join(TEST_DIR, 'output.wav');
    const buffer = makeBuffer();

    await encodeWav(buffer, filePath);

    expect(existsSync(filePath)).toBe(true);
  });

  test('written file can be decoded back', async () => {
    const filePath = join(TEST_DIR, 'roundtrip.wav');
    const original = makeBuffer();

    await encodeWav(original, filePath);
    const decoded = await decodeWav(filePath);

    expect(decoded.numberOfChannels).toBe(original.numberOfChannels);
    expect(decoded.sampleRate).toBe(original.sampleRate);
    expect(decoded.length).toBe(original.length);
  });

  test('roundtrip preserves audio data', async () => {
    const filePath = join(TEST_DIR, 'data_check.wav');
    const original = makeBuffer();

    await encodeWav(original, filePath);
    const decoded = await decodeWav(filePath);

    const origData = original.getChannelData(0);
    const decData = decoded.getChannelData(0);

    for (let i = 0; i < origData.length; i++) {
      expect(decData[i]).toBeCloseTo(origData[i], 5);
    }
  });

  test('writes mono file correctly', async () => {
    const filePath = join(TEST_DIR, 'mono.wav');
    const buffer = makeBuffer(44100, 1, 44100);

    await encodeWav(buffer, filePath);
    const decoded = await decodeWav(filePath);

    expect(decoded.numberOfChannels).toBe(1);
    expect(decoded.sampleRate).toBe(44100);
  });

  test('creates parent directories if needed', async () => {
    const filePath = join(TEST_DIR, 'nested', 'deep', 'output.wav');
    const buffer = makeBuffer();

    await encodeWav(buffer, filePath);

    expect(existsSync(filePath)).toBe(true);
  });
});

describe('encodeFlac', () => {
  test('throws not implemented error', async () => {
    const filePath = join(TEST_DIR, 'output.flac');
    const buffer = makeBuffer();

    await expect(encodeFlac(buffer, filePath)).rejects.toThrow('FLAC encoding is not yet implemented');
  });
});

describe('encodeMp3', () => {
  test('throws not implemented error', async () => {
    const filePath = join(TEST_DIR, 'output.mp3');
    const buffer = makeBuffer();

    await expect(encodeMp3(buffer, filePath)).rejects.toThrow('MP3 encoding is not yet implemented');
  });
});
