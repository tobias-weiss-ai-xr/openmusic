#!/usr/bin/env python3
"""Generate second mix with music theory integration."""
import sys
import subprocess
from pathlib import Path
import soundfile as sf

sys.path.insert(0, 'packages/core/src')
from openmusic.video.nodes.audio_automation import _apply_stage_modifications

mix_path = Path.home() / '.cache' / 'openmusic' / 'video' / 'audio' / 'audio_with_automation.flac'
if not mix_path.exists():
    print(f'Mix not found at {mix_path}')
    sys.exit(1)

print(f'Loading mix from {mix_path}...')
audio, sr = sf.read(str(mix_path))
print(f'Audio shape: {audio.shape}, SR: {sr}')

total_duration = len(audio) / sr
print(f'Total duration: {total_duration:.2f}s = {total_duration/60:.2f}min = {total_duration/3600:.2f}h')

stage_duration = total_duration / 10
print(f'Stage duration: {stage_duration:.2f}s ({stage_duration/60:.1f} min each)')

stages = [
    ('ambient-intro', 0, stage_duration),
    ('early-build', stage_duration, 2*stage_duration),
    ('mid-build', 2*stage_duration, 3*stage_duration),
    ('pre-peak-one', 3*stage_duration, 4*stage_duration),
    ('peak-one', 4*stage_duration, 5*stage_duration),
    ('peak-two', 5*stage_duration, 6*stage_duration),
    ('post-peak', 6*stage_duration, 7*stage_duration),
    ('decay-one', 7*stage_duration, 8*stage_duration),
    ('decay-two', 8*stage_duration, 9*stage_duration),
    ('dissolution', 9*stage_duration, 10*stage_duration),
]

processed_audio = audio.copy()
for idx, (stage, start, end) in enumerate(stages, 1):
    start_sample = int(start * sr)
    end_sample = min(int(end * sr), len(audio))
    if start_sample >= end_sample:
        continue
    print(f'Stage {idx}/10 Processing {stage} ({start:.0f}-{end:.0f}s)...')
    segment = audio[start_sample:end_sample]
    processed_segment = _apply_stage_modifications(segment, sr, stage, 'Dm', 125)
    processed_audio[start_sample:end_sample] = processed_segment
    print(f'  Done with {stage}')

output_path = Path('/tmp/2h_mix_with_music_theory.flac')
sf.write(str(output_path), processed_audio, sr)
print(f'\nDONE. Saved new mix to {output_path}')

result = subprocess.run(['ls', '-lh', str(output_path)], capture_output=True, text=True)
print(result.stdout)