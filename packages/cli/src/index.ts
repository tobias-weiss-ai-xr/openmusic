/**
 * @openmusic/cli
 * Command-line interface for OpenMusic
 */

import { AudioEngine, DEFAULT_EFFECTS_CONFIG, DEEP_DUB, MINIMAL_DUB, CLUB_DUB } from '@openmusic/effects';
import { DubTechnoPatterns } from '@openmusic/patterns';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';

export const version = '0.1.0';

interface CliOptions {
  length: string;
  style: 'dub_techno' | 'minimal' | 'club';
  output: string;
  bpm: number;
  key: string;
  help?: boolean;
}

function parseArgs(args: string[]): CliOptions {
  const options: CliOptions = {
    length: '5m',
    style: 'dub_techno',
    output: 'output.wav',
    bpm: 125,
    key: 'Am',
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--length':
      case '-l':
        options.length = args[++i];
        break;
      case '--style':
      case '-s':
        options.style = args[++i] as CliOptions['style'];
        break;
      case '--output':
      case '-o':
        options.output = args[++i];
        break;
      case '--bpm':
      case '-b':
        options.bpm = parseInt(args[++i], 10);
        break;
      case '--key':
      case '-k':
        options.key = args[++i];
        break;
      case '--help':
      case '-h':
        options.help = true;
        break;
    }
  }

  return options;
}

function printHelp() {
  console.log(`
OpenMusic CLI - AI-assisted dub techno generation

Usage: openmusic [options]

Options:
  --length, -l <duration>  Output length (e.g., "5m", "2h") [default: "5m"]
  --style, -s <style>     Music style: dub_techno, minimal, club [default: dub_techno]
  --output, -o <path>     Output file path [default: output.wav]
  --bpm, -b <number>     Tempo [default: 125]
  --key, -k <key>         Musical key (e.g., "Am", "C") [default: Am]
  --help, -h              Show this help message

Examples:
  openmusic --length 10m --style dub_techno --output mix.wav
  openmusic -l 2h -s club -o club mix.wav -b 130 -k Cm
`);
}

function parseLength(length: string): number {
  const match = length.match(/^(\d+)(m|h)$/);
  if (!match) throw new Error(`Invalid length format: ${length}`);
  const value = parseInt(match[1], 10);
  const unit = match[2];
  return unit === 'h' ? value * 60 * 60 : value * 60;
}

function getEffectsConfig(style: CliOptions['style']) {
  switch (style) {
    case 'dub_techno': return DEEP_DUB;
    case 'minimal': return MINIMAL_DUB;
    case 'club': return CLUB_DUB;
    default: return DEFAULT_EFFECTS_CONFIG;
  }
}

/**
 * Executes the CLI application.
 * Reads input files from args or generates a pattern and renders audio.
 */
export async function run(args: string[] = process.argv.slice(2)): Promise<void> {
  const options = parseArgs(args);

  if (options.help) {
    printHelp();
    return;
  }

  const seconds = parseLength(options.length);
  const sampleRate = 48000;
  const channels = 2;
  const numSamples = seconds * sampleRate;

  // Determine input files
  const inputFiles = args.filter(arg => arg.endsWith('.wav') && existsSync(arg));

  if (inputFiles.length === 0) {
    console.log('No input files provided. Generating pattern...');
    // For now, generate silence as placeholder
    // In full implementation, would use patterns to generate audio
  }

  const engine = new AudioEngine({ sampleRate, channels });
  const effectsConfig = getEffectsConfig(options.style);

  try {
    if (inputFiles.length > 0) {
      console.log(`Processing ${inputFiles.length} input file(s)...`);
      const buffer = await engine.render(inputFiles, { style: options.style, variation: 0.3 }, effectsConfig);
      
      const ext = options.output.split('.').pop() || 'wav';
      await engine.export(buffer, options.output, ext as 'wav');
      
      console.log(`Written to ${options.output}`);
    } else {
      // Create empty buffer for pattern generation
      console.log('Generating pattern for key:', options.key, 'BPM:', options.bpm);
      const pattern = DubTechnoPatterns.fullPattern(options.key, options.bpm);
      console.log('Pattern generated (audio generation not yet implemented):', JSON.stringify(pattern, null, 2));
    }
  } catch (err) {
    console.error('Error:', err instanceof Error ? err.message : String(err));
    process.exit(1);
  }
}

// Allow running as CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  run().catch(console.error);
}
