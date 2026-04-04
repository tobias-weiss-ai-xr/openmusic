import { readFileSync } from 'node:fs';
import { OfflineAudioContext } from 'web-audio-api';

/** Metadata about a decoded audio file. */
export interface AudioInfo {
  sampleRate: number;
  channels: number;
  duration: number;
  bitsPerSample: number;
}

/** Decode a WAV file into an AudioBuffer. */
export async function decodeWav(filePath: string): Promise<any> {
  const fileBuffer = readFileSync(filePath);
  const arrayBuffer = fileBuffer.buffer.slice(
    fileBuffer.byteOffset,
    fileBuffer.byteOffset + fileBuffer.byteLength
  );

  const info = getAudioInfo(filePath);

  const ctx = new OfflineAudioContext(
    info.channels,
    Math.ceil(info.duration * info.sampleRate),
    info.sampleRate
  );

  return ctx.decodeAudioData(arrayBuffer);
}

export function getAudioInfo(filePath: string): AudioInfo {
  const buffer = readFileSync(filePath);

  const riff = buffer.toString('ascii', 0, 4);
  if (riff !== 'RIFF') {
    throw new Error(`Invalid WAV file: expected RIFF header, got "${riff}"`);
  }

  const channels = buffer.readUInt16LE(22);
  const sampleRate = buffer.readUInt32LE(24);
  const bitsPerSample = buffer.readUInt16LE(34);
  const blockAlign = buffer.readUInt16LE(32);

  let dataSize = 0;
  let offset = 12;
  while (offset < buffer.length - 8) {
    const chunkId = buffer.toString('ascii', offset, offset + 4);
    const chunkSize = buffer.readUInt32LE(offset + 4);

    if (chunkId === 'data') {
      dataSize = chunkSize;
      break;
    }
    offset += 8 + chunkSize;
  }

  if (dataSize === 0) {
    throw new Error('Invalid WAV file: no data chunk found');
  }

  const numSamples = dataSize / blockAlign;
  const duration = numSamples / sampleRate;

  return { sampleRate, channels, duration, bitsPerSample };
}
