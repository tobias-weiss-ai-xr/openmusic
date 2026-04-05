import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { execSync } from 'node:child_process';

/** Encodes an AudioBuffer to WAV format. */
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

/**
 * Encodes an AudioBuffer to FLAC format via ffmpeg.
 * @param buffer - The AudioBuffer to encode
 * @param outputPath - Output file path (.flac)
 */
export async function encodeFlac(
  buffer: AudioBuffer,
  outputPath: string
): Promise<void> {
  const tempWav = outputPath.replace(/\.flac$/i, '_temp.wav');
  await encodeWav(buffer, tempWav);
  
  try {
    execSync(`ffmpeg -i "${tempWav}" -y -codec flac "${outputPath}"`, { stdio: 'pipe' });
  } finally {
    const { unlinkSync } = await import('node:fs');
    try { unlinkSync(tempWav); } catch {}
  }
}

/**
 * Encodes an AudioBuffer to MP3 format via ffmpeg.
 * @param buffer - The AudioBuffer to encode
 * @param outputPath - Output file path (.mp3)
 */
export async function encodeMp3(
  buffer: AudioBuffer,
  outputPath: string
): Promise<void> {
  const tempWav = outputPath.replace(/\.mp3$/i, '_temp.wav');
  await encodeWav(buffer, tempWav);
  
  try {
    execSync(`ffmpeg -i "${tempWav}" -y -codec libmp3lame -q:a 2 "${outputPath}"`, { stdio: 'pipe' });
  } finally {
    const { unlinkSync } = await import('node:fs');
    try { unlinkSync(tempWav); } catch {}
  }
}
