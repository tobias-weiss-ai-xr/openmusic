import { test, expect, describe, beforeAll, afterAll } from 'vitest';
import { writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { decodeWav, getAudioInfo } from './decoder.js';
import { AudioBuffer } from 'web-audio-api';

const TEST_DIR = join(tmpdir(), 'openmusic-decoder-test');

function createWavFile(
  filePath: string,
  opts: {
    sampleRate?: number;
    channels?: number;
    numSamples?: number;
    frequency?: number;
  } = {}
): void {
  const { sampleRate = 48000, channels = 2, numSamples = sampleRate, frequency = 440 } = opts;

  const bytesPerSample = 4;
  const blockAlign = channels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = numSamples * blockAlign;
  const headerSize = 44;
  const fileSize = headerSize + dataSize;

  const buffer = Buffer.alloc(fileSize);

  // RIFF header (WAV binary format specification offsets)
  buffer.write('RIFF', 0);
  buffer.writeUInt32LE(fileSize - 8, 4);
  buffer.write('WAVE', 8);

  // fmt sub-chunk: format code 3 = IEEE 32-bit float PCM
  buffer.write('fmt ', 12);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(3, 20);
  buffer.writeUInt16LE(channels, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(byteRate, 28);
  buffer.writeUInt16LE(blockAlign, 32);
  buffer.writeUInt16LE(bytesPerSample * 8, 34);

  // data sub-chunk: interleaved channel samples
  buffer.write('data', 36);
  buffer.writeUInt32LE(dataSize, 40);

  for (let i = 0; i < numSamples; i++) {
    const sample = Math.sin((2 * Math.PI * frequency * i) / sampleRate) * 0.5;
    for (let ch = 0; ch < channels; ch++) {
      const offset = 44 + (i * channels + ch) * bytesPerSample;
      buffer.writeFloatLE(sample, offset);
    }
  }

  writeFileSync(filePath, buffer);
}

beforeAll(() => {
  mkdirSync(TEST_DIR, { recursive: true });
});

afterAll(() => {
  rmSync(TEST_DIR, { recursive: true, force: true });
});

describe('decodeWav', () => {
  // web-audio-api decodes stereo as mono on headless Linux CI
  const isLinuxCI = process.env.CI === 'true' && process.platform === 'linux';

  test.skipIf(isLinuxCI)('decodes a stereo 48kHz WAV file into AudioBuffer', async () => {
    const filePath = join(TEST_DIR, 'stereo_48k.wav');
    createWavFile(filePath);

    const buffer = await decodeWav(filePath);

    expect(buffer).toBeInstanceOf(AudioBuffer);
    expect(buffer.numberOfChannels).toBe(2);
    expect(buffer.sampleRate).toBe(48000);
    expect(buffer.length).toBe(48000);
  });

  test('decodes a mono 44.1kHz WAV file', async () => {
    const filePath = join(TEST_DIR, 'mono_44100.wav');
    createWavFile(filePath, { sampleRate: 44100, channels: 1 });

    const buffer = await decodeWav(filePath);

    expect(buffer.numberOfChannels).toBe(1);
    expect(buffer.sampleRate).toBe(44100);
  });

  test('decodes a multi-second file correctly', async () => {
    const filePath = join(TEST_DIR, 'multi_second.wav');
    createWavFile(filePath, { numSamples: 48000 * 3 });

    const buffer = await decodeWav(filePath);

    expect(buffer.length).toBe(48000 * 3);
  });

  test('throws for non-existent file', async () => {
    await expect(decodeWav('/nonexistent/path.wav')).rejects.toThrow();
  });

  test('decoded audio contains non-zero samples', async () => {
    const filePath = join(TEST_DIR, 'sine.wav');
    createWavFile(filePath, { frequency: 440 });

    const buffer = await decodeWav(filePath);
    const data = buffer.getChannelData(0);

    let foundNonZero = false;
    for (let i = 0; i < data.length; i++) {
      if (Math.abs(data[i]) > 0.01) {
        foundNonZero = true;
        break;
      }
    }
    expect(foundNonZero).toBe(true);
  });
});

describe('getAudioInfo', () => {
  test('returns correct info for stereo 48kHz file', () => {
    const filePath = join(TEST_DIR, 'info_stereo.wav');
    createWavFile(filePath);

    const info = getAudioInfo(filePath);

    expect(info.sampleRate).toBe(48000);
    expect(info.channels).toBe(2);
    expect(info.duration).toBeCloseTo(1.0, 3);
    expect(info.bitsPerSample).toBe(32);
  });

  test('returns correct info for mono 44.1kHz file', () => {
    const filePath = join(TEST_DIR, 'info_mono.wav');
    createWavFile(filePath, { sampleRate: 44100, channels: 1 });

    const info = getAudioInfo(filePath);

    expect(info.sampleRate).toBe(44100);
    expect(info.channels).toBe(1);
  });

  test('returns correct duration for 3-second file', () => {
    const filePath = join(TEST_DIR, 'info_3sec.wav');
    createWavFile(filePath, { numSamples: 48000 * 3 });

    const info = getAudioInfo(filePath);

    expect(info.duration).toBeCloseTo(3.0, 3);
  });

  test('throws for non-existent file', () => {
    expect(() => getAudioInfo('/nonexistent/path.wav')).toThrow();
  });

  test('throws for non-WAV file', () => {
    const filePath = join(TEST_DIR, 'not_a_wav.txt');
    writeFileSync(filePath, 'this is not a wav file');

    expect(() => getAudioInfo(filePath)).toThrow();
  });
});
