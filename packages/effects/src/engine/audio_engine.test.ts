import { test, expect, describe, beforeAll, afterAll } from 'vitest';
import { writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { AudioEngine, type EngineConfig, type BridgeConfig, type InputStem } from './audio_engine.js';
import { decodeWav } from './decoder.js';
import { AudioBuffer, OfflineAudioContext } from 'web-audio-api';
import { DEFAULT_EFFECTS_CONFIG } from '../config.js';

const TEST_DIR = join(tmpdir(), 'openmusic-engine-test');

function createWavFile(
  filePath: string,
  opts: {
    sampleRate?: number;
    channels?: number;
    numSamples?: number;
    frequency?: number;
  } = {}
): void {
  const {
    sampleRate = 48000,
    channels = 2,
    numSamples = sampleRate,
    frequency = 440,
  } = opts;

  const bytesPerSample = 4;
  const blockAlign = channels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = numSamples * blockAlign;
  const headerSize = 44;
  const fileSize = headerSize + dataSize;

  const buffer = Buffer.alloc(fileSize);

  buffer.write('RIFF', 0);
  buffer.writeUInt32LE(fileSize - 8, 4);
  buffer.write('WAVE', 8);

  buffer.write('fmt ', 12);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(3, 20);
  buffer.writeUInt16LE(channels, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(byteRate, 28);
  buffer.writeUInt16LE(blockAlign, 32);
  buffer.writeUInt16LE(bytesPerSample * 8, 34);

  buffer.write('data', 36);
  buffer.writeUInt32LE(dataSize, 40);

  for (let i = 0; i < numSamples; i++) {
    const sample = Math.sin(2 * Math.PI * frequency * i / sampleRate) * 0.5;
    for (let ch = 0; ch < channels; ch++) {
      const offset = 44 + (i * channels + ch) * bytesPerSample;
      buffer.writeFloatLE(sample, offset);
    }
  }

  writeFileSync(filePath, buffer);
}

function createBridgeConfig(overrides: Partial<BridgeConfig> = {}): BridgeConfig {
  return {
    sampleRate: 48000,
    channels: 2,
    duration: 1,
    bpm: 125,
    key: 'Am',
    inputStems: [
      { path: join(TEST_DIR, 'stem_0.wav'), role: 'bass' },
    ],
    outputPath: join(TEST_DIR, 'output', 'processed.wav'),
    effects: DEFAULT_EFFECTS_CONFIG,
    pattern: { style: 'dub_techno', variation: 0.3 },
    ...overrides,
  };
}

function writeBridgeConfig(configPath: string, config: BridgeConfig): void {
  mkdirSync(dirname(configPath), { recursive: true });
  writeFileSync(configPath, JSON.stringify(config, null, 2));
}

beforeAll(() => {
  mkdirSync(TEST_DIR, { recursive: true });
  createWavFile(join(TEST_DIR, 'stem_0.wav'));
  createWavFile(join(TEST_DIR, 'stem_1.wav'), { frequency: 220 });
});

afterAll(() => {
  rmSync(TEST_DIR, { recursive: true, force: true });
});

describe('AudioEngine', () => {
  describe('constructor', () => {
    test('creates engine with default config', () => {
      const engine = new AudioEngine();
      expect(engine).toBeDefined();
    });

    test('creates engine with custom config', () => {
      const config: EngineConfig = {
        sampleRate: 44100,
        channels: 1,
        effectsPreset: 'minimal_dub',
      };
      const engine = new AudioEngine(config);
      expect(engine).toBeDefined();
    });
  });

  describe('render', () => {
    test('returns AudioBuffer for single input file', async () => {
      const engine = new AudioEngine();

      const result = await engine.render(
        [join(TEST_DIR, 'stem_0.wav')],
        { style: 'dub_techno', variation: 0.3 },
        DEFAULT_EFFECTS_CONFIG
      );

      expect(result).toBeInstanceOf(AudioBuffer);
      expect(result.numberOfChannels).toBe(2);
      expect(result.sampleRate).toBe(48000);
    });

    test('returns AudioBuffer for multiple input files (mixed)', async () => {
      const engine = new AudioEngine();

      const result = await engine.render(
        [join(TEST_DIR, 'stem_0.wav'), join(TEST_DIR, 'stem_1.wav')],
        { style: 'dub_techno', variation: 0.3 },
        DEFAULT_EFFECTS_CONFIG
      );

      expect(result).toBeInstanceOf(AudioBuffer);
      expect(result.numberOfChannels).toBe(2);
    });

    test('mixed output has non-zero samples', async () => {
      const engine = new AudioEngine();

      const result = await engine.render(
        [join(TEST_DIR, 'stem_0.wav')],
        { style: 'dub_techno', variation: 0.3 },
        DEFAULT_EFFECTS_CONFIG
      );

      const data = result.getChannelData(0);
      let foundNonZero = false;
      for (let i = 0; i < Math.min(data.length, 1000); i++) {
        if (Math.abs(data[i]) > 0.001) {
          foundNonZero = true;
          break;
        }
      }
      expect(foundNonZero).toBe(true);
    });

    test('throws for non-existent input file', async () => {
      const engine = new AudioEngine();

      await expect(
        engine.render(
          ['/nonexistent/file.wav'],
          { style: 'dub_techno', variation: 0.3 },
          DEFAULT_EFFECTS_CONFIG
        )
      ).rejects.toThrow();
    });
  });

  describe('export', () => {
    test('exports buffer as WAV file', async () => {
      const engine = new AudioEngine();
      const ctx = new OfflineAudioContext(2, 48000, 48000);
      const buf = ctx.createBuffer(2, 48000, 48000);

      await engine.export(buf, join(TEST_DIR, 'export_test.wav'), 'wav');

      expect(existsSync(join(TEST_DIR, 'export_test.wav'))).toBe(true);
    });

    test('exported WAV can be decoded back', async () => {
      const engine = new AudioEngine();
      const ctx = new OfflineAudioContext(2, 48000, 48000);
      const buf = ctx.createBuffer(2, 48000, 48000);
      const data = buf.getChannelData(0);
      for (let i = 0; i < data.length; i++) {
        data[i] = Math.sin(2 * Math.PI * 440 * i / 48000) * 0.5;
      }

      const exportPath = join(TEST_DIR, 'export_roundtrip.wav');
      await engine.export(buf, exportPath, 'wav');

      const decoded = await decodeWav(exportPath);
      expect(decoded.numberOfChannels).toBe(2);
      expect(decoded.sampleRate).toBe(48000);
      expect(decoded.length).toBe(48000);
    });

    test('throws for unsupported format', async () => {
      const engine = new AudioEngine();
      const ctx = new OfflineAudioContext(2, 48000, 48000);
      const buf = ctx.createBuffer(2, 48000, 48000);

      await expect(
        engine.export(buf, join(TEST_DIR, 'test.flac'), 'flac')
      ).rejects.toThrow();
    });
  });

  describe('fromBridgeConfig', () => {
    test('creates engine from bridge config file', async () => {
      const configPath = join(TEST_DIR, 'config.json');
      writeBridgeConfig(configPath, createBridgeConfig());

      const engine = AudioEngine.fromBridgeConfig(configPath);

      expect(engine).toBeInstanceOf(AudioEngine);
    });

    test('engine created from config has correct sample rate', async () => {
      const configPath = join(TEST_DIR, 'config_44100.json');
      writeBridgeConfig(configPath, createBridgeConfig({ sampleRate: 44100 }));

      const engine = AudioEngine.fromBridgeConfig(configPath);

      expect(engine).toBeInstanceOf(AudioEngine);
    });

    test('throws for non-existent config file', () => {
      expect(() => AudioEngine.fromBridgeConfig('/nonexistent/config.json')).toThrow();
    });

    test('throws for invalid JSON', () => {
      const configPath = join(TEST_DIR, 'bad_config.json');
      writeFileSync(configPath, 'not valid json{{{');

      expect(() => AudioEngine.fromBridgeConfig(configPath)).toThrow();
    });
  });
});
