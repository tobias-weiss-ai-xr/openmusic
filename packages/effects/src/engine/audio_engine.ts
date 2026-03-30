import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { OfflineAudioContext } from 'web-audio-api';
import { DubTechnoEffectsChain } from '../chain.js';
import { DEFAULT_EFFECTS_CONFIG, type EffectsConfig } from '../config.js';
import { decodeWav } from './decoder.js';
import { encodeWav, encodeFlac, encodeMp3 } from './encoder.js';

export interface EngineConfig {
  sampleRate: number;
  channels: number;
  effectsPreset: string;
}

export interface InputStem {
  path: string;
  role: string;
}

export interface PatternConfig {
  style: string;
  variation: number;
}

export interface BridgeConfig {
  sampleRate: number;
  channels: number;
  duration: number;
  bpm: number;
  key: string;
  inputStems: InputStem[];
  outputPath: string;
  effects: EffectsConfig;
  pattern: PatternConfig;
}

const DEFAULT_ENGINE_CONFIG: EngineConfig = {
  sampleRate: 48000,
  channels: 2,
  effectsPreset: 'deep_dub',
};

export class AudioEngine {
  private config: EngineConfig;

  constructor(config?: Partial<EngineConfig>) {
    this.config = { ...DEFAULT_ENGINE_CONFIG, ...config };
  }

  async render(
    inputFiles: string[],
    _patternConfig: PatternConfig,
    effectsConfig: EffectsConfig
  ): Promise<AudioBuffer> {
    const decodedBuffers = await Promise.all(
      inputFiles.map((file) => decodeWav(file))
    );

    const mixed = await this.mixBuffers(decodedBuffers);

    const chain = new DubTechnoEffectsChain(effectsConfig);
    return chain.process(mixed);
  }

  private async mixBuffers(buffers: AudioBuffer[]): Promise<AudioBuffer> {
    if (buffers.length === 0) {
      throw new Error('No input buffers to mix');
    }

    const first = buffers[0];
    let maxLength = 0;

    for (const buf of buffers) {
      const len = buf.length;
      if (len > maxLength) maxLength = len;
    }

    const ctx = new OfflineAudioContext(
      this.config.channels,
      maxLength,
      this.config.sampleRate
    );
    const output = ctx.createBuffer(this.config.channels, maxLength, this.config.sampleRate);

    const numFiles = buffers.length;
    const gainPerFile = 1 / numFiles;

    for (const buf of buffers) {
      const inputChannels = buf.numberOfChannels;
      const outputChannels = output.numberOfChannels;

      for (let ch = 0; ch < outputChannels; ch++) {
        const outData = output.getChannelData(ch);
        const inCh = ch < inputChannels ? ch : 0;
        const inData = buf.getChannelData(inCh);

        for (let i = 0; i < inData.length; i++) {
          outData[i] += inData[i] * gainPerFile;
        }
      }
    }

    return output;
  }

  async export(
    buffer: AudioBuffer,
    outputPath: string,
    format: 'wav' | 'flac' | 'mp3'
  ): Promise<void> {
    switch (format) {
      case 'wav':
        await encodeWav(buffer, outputPath);
        break;
      case 'flac':
        await encodeFlac(buffer, outputPath);
        break;
      case 'mp3':
        await encodeMp3(buffer, outputPath);
        break;
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  static fromBridgeConfig(configPath: string): AudioEngine {
    const raw = readFileSync(configPath, 'utf-8');
    const config: BridgeConfig = JSON.parse(raw);

    return new AudioEngine({
      sampleRate: config.sampleRate,
      channels: config.channels,
    });
  }
}
