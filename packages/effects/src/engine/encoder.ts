import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

/** Encode an AudioBuffer to WAV format. */
export async function encodeWav(
  buffer: AudioBuffer,
  outputPath: string
): Promise<void> {
  const { numberOfChannels, sampleRate, length } = buffer;
  const bytesPerSample = 4;
  const blockAlign = numberOfChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = length * blockAlign;
  const headerSize = 44;
  const fileSize = headerSize + dataSize;

  const wav = Buffer.alloc(fileSize);

  wav.write('RIFF', 0);
  wav.writeUInt32LE(fileSize - 8, 4);
  wav.write('WAVE', 8);

  wav.write('fmt ', 12);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(3, 20); // IEEE 32-bit float PCM
  wav.writeUInt16LE(numberOfChannels, 22);
  wav.writeUInt32LE(sampleRate, 24);
  wav.writeUInt32LE(byteRate, 28);
  wav.writeUInt16LE(blockAlign, 32);
  wav.writeUInt16LE(bytesPerSample * 8, 34);

  wav.write('data', 36);
  wav.writeUInt32LE(dataSize, 40);

  const interleaved = new Float32Array(length * numberOfChannels);
  for (let ch = 0; ch < numberOfChannels; ch++) {
    const channelData = buffer.getChannelData(ch);
    for (let i = 0; i < length; i++) {
      interleaved[i * numberOfChannels + ch] = channelData[i];
    }
  }

  for (let i = 0; i < interleaved.length; i++) {
    wav.writeFloatLE(interleaved[i], 44 + i * bytesPerSample);
  }

  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, wav);
}

export async function encodeFlac(
  _buffer: AudioBuffer,
  _outputPath: string
): Promise<void> {
  throw new Error('FLAC encoding is not yet implemented. Use ffmpeg for FLAC conversion.');
}

export async function encodeMp3(
  _buffer: AudioBuffer,
  _outputPath: string
): Promise<void> {
  throw new Error('MP3 encoding is not yet implemented. Use ffmpeg for MP3 conversion.');
}
