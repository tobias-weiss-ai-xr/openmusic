# @openmusic/cli

Command-line interface for OpenMusic - AI-assisted dub techno generation.

## Installation

```bash
npm install @openmusic/cli
```

## Usage

```bash
openmusic generate --length 2h --style dub_techno --output mix.flac
```

## Commands

- `generate` - Generate a dub techno mix
- `export` - Export audio in various formats

## Options

- `--length` - Duration (e.g., "2h", "30m")
- `--style` - Music style (dub_techno, minimal, club)
- `--output` - Output file path
- `--bpm` - Tempo (default: 125)
- `--key` - Musical key (e.g., "Am")

## Programmatic Usage

```typescript
import { run } from '@openmusic/cli';

run();
```