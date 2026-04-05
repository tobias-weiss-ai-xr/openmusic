# @openmusic/effects

Dub techno audio effects chain using web-audio-api.

## Installation

```bash
npm install @openmusic/effects
```

## Usage

```typescript
import { AudioEngine, DEFAULT_EFFECTS_CONFIG } from '@openmusic/effects';

const engine = new AudioEngine();
const buffer = await engine.render(['input.wav'], { style: 'dub_techno', variation: 0.3 }, DEFAULT_EFFECTS_CONFIG);
await engine.export(buffer, 'output.wav', 'wav');
```

## Presets

- `DEEP_DUB` - Deep, atmospheric dub techno with long delays and reverb
- `MINIMAL_DUB` - Subtle effects for minimal productions
- `CLUB_DUB` - Punchy sound optimized for club systems

## API

### AudioEngine

- `new AudioEngine(config?)` - Create engine with optional config
- `render(inputFiles, patternConfig, effectsConfig)` - Render audio through effects
- `export(buffer, outputPath, format)` - Export to WAV/FLAC/MP3
- `fromBridgeConfig(configPath)` - Load engine from JSON config

### Effects

- `DubTechnoEffectsChain` - Full effects chain
- `DelayEffect`, `ReverbEffect`, `FilterEffect`, `DistortionEffect`, `VinylEffect`