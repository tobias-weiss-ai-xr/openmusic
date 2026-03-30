export const version = '0.1.0';

export { DubTechnoEffectsChain } from './chain.js';

export {
  DelayEffect,
  ReverbEffect,
  FilterEffect,
  DistortionEffect,
  VinylEffect,
} from './effects/index.js';

export type {
  EffectsConfig,
  DelayConfig,
  ReverbConfig,
  FilterConfig,
  DistortionConfig,
  VinylConfig,
} from './config.js';

export {
  DEEP_DUB,
  MINIMAL_DUB,
  CLUB_DUB,
  DEFAULT_EFFECTS_CONFIG,
} from './config.js';

export {
  AudioEngine,
  decodeWav,
  getAudioInfo,
  encodeWav,
  encodeFlac,
  encodeMp3,
} from './engine/index.js';

export type {
  EngineConfig,
  BridgeConfig,
  InputStem,
  PatternConfig,
  AudioInfo,
} from './engine/index.js';

function isDirectExecution(): boolean {
  return (
    process.argv[1]?.endsWith('index.js') ||
    process.argv[1]?.endsWith('index')
  );
}

if (isDirectExecution()) {
  const { readFileSync, existsSync } = await import('node:fs');
  const { resolve, dirname, join } = await import('node:path');

  const args = process.argv.slice(2);
  const configIdx = args.indexOf('--config');

  if (configIdx === -1 || configIdx + 1 >= args.length) {
    process.stderr.write('Usage: node dist/index.js --config <path>\n');
    process.exit(1);
  }

  const configPath = resolve(args[configIdx + 1]);

  if (!existsSync(configPath)) {
    process.stderr.write(`Error: config file not found: ${configPath}\n`);
    process.exit(1);
  }

  try {
    const { AudioEngine } = await import('./engine/index.js');
    const { dirname: pathDirname } = await import('node:path');

    const raw = readFileSync(configPath, 'utf-8');
    const config = JSON.parse(raw);
    const configDir = dirname(configPath);

    const engine = new AudioEngine({
      sampleRate: config.sampleRate,
      channels: config.channels,
    });

    const inputFiles = config.inputStems.map(
      (stem: { path: string }) => join(configDir, stem.path)
    );
    const outputPath = join(configDir, config.outputPath);

    const buffer = await engine.render(
      inputFiles,
      config.pattern,
      config.effects
    );
    await engine.export(buffer, outputPath, 'wav');

    process.exit(0);
  } catch (err) {
    process.stderr.write(
      `Error: ${err instanceof Error ? err.message : String(err)}\n`
    );
    process.exit(1);
  }
}
