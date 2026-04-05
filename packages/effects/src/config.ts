/** Delay effect configuration with primary and secondary taps. */
export interface DelayConfig {
  primaryTime: number;
  primaryFeedback: number;
  primaryMix: number;
  secondaryTime: number;
  secondaryFeedback: number;
  secondaryMix: number;
  enabled: boolean;
}

/** Reverb effect configuration. */
export interface ReverbConfig {
  decay: number;
  preDelay: number;
  mix: number;
  inputFilterFreq: number;
  inputFilterQ: number;
  enabled: boolean;
}

/** Filter effect configuration with LFO modulation. */
export interface FilterConfig {
  type: BiquadFilterType;
  frequency: number;
  Q: number;
  lfoRate: number;
  lfoDepth: number;
  enabled: boolean;
}

/** Distortion effect configuration. */
export interface DistortionConfig {
  amount: number;
  mix: number;
  enabled: boolean;
}

/** Vinyl noise effect configuration. */
export interface VinylConfig {
  level: number;
  hissLevel: number;
  enabled: boolean;
}

/** Tape saturation effect configuration. */
export interface TapeSaturationConfig {
  drive: number;
  wetDryMix: number;
  biasTone: {
    frequency: number;
    amplitude: number;
  } | null;
  enabled: boolean;
}

export interface EffectsConfig {
  delay: DelayConfig;
  reverb: ReverbConfig;
  filter: FilterConfig;
  distortion: DistortionConfig;
  vinyl: VinylConfig;
  tapeSaturation: TapeSaturationConfig;
}

/** Deep, atmospheric dub techno preset with long delays and reverb. */
export const DEEP_DUB: EffectsConfig = {
  delay: {
    primaryTime: 0.375, // dotted 1/8 at 125 BPM
    primaryFeedback: 0.5,
    primaryMix: 0.6,
    secondaryTime: 0.28125, // 3/16 at 125 BPM
    secondaryFeedback: 0.4,
    secondaryMix: 0.5,
    enabled: true,
  },
  reverb: {
    decay: 4.0,
    preDelay: 30,
    mix: 0.5,
    inputFilterFreq: 800,
    inputFilterQ: 1.5,
    enabled: true,
  },
  filter: {
    type: 'bandpass',
    frequency: 600,
    Q: 3.0,
    lfoRate: 0.1,
    lfoDepth: 150,
    enabled: true,
  },
  distortion: {
    amount: 0.2,
    mix: 0.3,
    enabled: true,
  },
  vinyl: {
    level: 0.25,
    hissLevel: 0.15,
    enabled: true,
  },
  tapeSaturation: {
    drive: 30,
    wetDryMix: 40,
    biasTone: { frequency: 50, amplitude: 0.01 },
    enabled: true,
  },
};

/** Minimal dub techno preset with subtle effects. */
export const MINIMAL_DUB: EffectsConfig = {
  delay: {
    primaryTime: 0.375,
    primaryFeedback: 0.3,
    primaryMix: 0.35,
    secondaryTime: 0.28125,
    secondaryFeedback: 0.2,
    secondaryMix: 0.25,
    enabled: true,
  },
  reverb: {
    decay: 2.0,
    preDelay: 20,
    mix: 0.25,
    inputFilterFreq: 1000,
    inputFilterQ: 1.0,
    enabled: true,
  },
  filter: {
    type: 'bandpass',
    frequency: 900,
    Q: 2.0,
    lfoRate: 0.2,
    lfoDepth: 80,
    enabled: true,
  },
  distortion: {
    amount: 0.1,
    mix: 0.15,
    enabled: true,
  },
  vinyl: {
    level: 0.1,
    hissLevel: 0.05,
    enabled: true,
  },
  tapeSaturation: {
    drive: 15,
    wetDryMix: 20,
    biasTone: null,
    enabled: true,
  },
};

/** Club-optimized dub techno preset with punchier sound. */
export const CLUB_DUB: EffectsConfig = {
  delay: {
    primaryTime: 0.3,
    primaryFeedback: 0.35,
    primaryMix: 0.4,
    secondaryTime: 0.225,
    secondaryFeedback: 0.25,
    secondaryMix: 0.3,
    enabled: true,
  },
  reverb: {
    decay: 2.5,
    preDelay: 15,
    mix: 0.3,
    inputFilterFreq: 1200,
    inputFilterQ: 1.2,
    enabled: true,
  },
  filter: {
    type: 'bandpass',
    frequency: 1000,
    Q: 2.5,
    lfoRate: 0.3,
    lfoDepth: 120,
    enabled: true,
  },
  distortion: {
    amount: 0.25,
    mix: 0.35,
    enabled: true,
  },
  vinyl: {
    level: 0.12,
    hissLevel: 0.08,
    enabled: true,
  },
  tapeSaturation: {
    drive: 40,
    wetDryMix: 50,
    biasTone: { frequency: 60, amplitude: 0.015 },
    enabled: true,
  },
};

export const DEFAULT_EFFECTS_CONFIG: EffectsConfig = MINIMAL_DUB;
