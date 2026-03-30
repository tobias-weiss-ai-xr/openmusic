# Acceptance Criteria

All acceptance criteria are machine-verifiable. No human listening or subjective judgment required.

Each criterion includes:
- **Command**: Exact command to execute
- **Expected**: What the output should be
- **Validation**: Command and expected result to verify the criterion

---

## CLI Interface

### AC-1: CLI Help Command Displays Usage
- **Command**: `openmusic --help`
- **Expected**: Usage text showing available commands (generate, validate, version) and required flags
- **Validation**: `openmusic --help | grep -q "generate"` AND `openmusic --help | grep -q "validate"` AND `openmusic --help | grep -q "version"`

### AC-2: CLI Version Command Returns Valid SemVer
- **Command**: `openmusic --version`
- **Expected**: Version string in semantic versioning format (e.g., `1.0.0`)
- **Validation**: `openmusic --version | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$'`

### AC-3: CLI Generate Accepts Required Arguments
- **Command**: `openmusic generate --length 1m --output test.flac --style dub_techno`
- **Expected**: Command executes without error, generates `test.flac` file
- **Validation**: `ls -lh test.flac` (file exists and size > 0)

### AC-4: CLI Validates Configuration Files
- **Command**: `openmusic validate --config config.json`
- **Expected**: Returns exit code 0 for valid config, non-zero for invalid
- **Validation**: `openmusic validate --config config.json; echo $?` (should be 0)

---

## Audio Output

### AC-5: Generated Audio Is 48kHz Sample Rate
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Audio file with 48000 Hz sample rate
- **Validation**: `ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 test.flac | grep -E '^48000$'`

### AC-6: Generated Audio Is Stereo
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Audio file with 2 channels
- **Validation**: `ffprobe -v error -select_streams a:0 -show_entries stream=channels -of default=noprint_wrappers=1:nokey=1 test.flac | grep -E '^2$'`

### AC-7: Generated Audio Is FLAC Format
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: FLAC container format
- **Validation**: `ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 test.flac | grep -i flac`

### AC-8: Generated Audio Duration Matches Request
- **Command**: `openmusic generate --length 10m --output test.flac`
- **Expected**: Audio duration within ±1 second of requested 600 seconds
- **Validation**: `DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 test.flac); python3 -c "import sys; print(abs(float(sys.argv[1]) - 600) < 1)" "$DURATION"`

---

## Audio Quality

### AC-9: RMS Level Within Acceptable Range
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: RMS between -18 dB and -14 dB (target -16 dB)
- **Validation**: `ffprobe -v error -hide_banner -stats -i test.flac 2>&1 | grep -oP 'RMS level: \K-?[0-9]+\.[0-9]+' | awk '{print ($1 >= -18 && $1 <= -14) ? "PASS" : "FAIL"}' | grep PASS`

### AC-10: No Clipping (Peak Level Below -0.1 dB)
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Peak level below -0.1 dB (no digital clipping)
- **Validation**: `sox test.flac -n stat 2>&1 | grep "Maximum amplitude:" | awk '{print ($3 < 0.9) ? "PASS" : "FAIL"}' | grep PASS`

### AC-11: Sub-Bass Present (25-55 Hz Range)
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Energy present in 25-55 Hz frequency range
- **Validation**: `sox test.flac -n stat 2>&1` (alternative: `ffmpeg -i test.flac -af "highpass=f=25,lowpass=f=55" -f null -` should produce significant output)

### AC-12: High Frequency Roll-off at 14-16 kHz
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Energy drops significantly above 16 kHz
- **Validation**: `sox test.flac -n spectrogram -o spectrogram.png` (visual inspection) OR `ffmpeg -i test.flac -af "highpass=f=16000" -f null -` (minimal output)

### AC-13: Noise Floor Below -60 dB
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Noise floor at -60 dB or below
- **Validation**: `sox test.flac -n stat 2>&1 | grep "RMS level:" | awk '{print ($3 < 0.001) ? "PASS" : "FAIL"}'` (approximate -60 dB is 0.001 amplitude)

### AC-14: Stereo Width Between 120% and 150%
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Stereo image width within 120-150% (enhanced width)
- **Validation**: `ffmpeg -i test.flac -filter_complex "stereotools=mlev=0.015625" -f null -` OR use `sox` phase meter for width calculation

---

## Pipeline

### AC-15: ACE-Step Generates Valid WAV Stem
- **Command**: (internal pipeline step) ACE-Step generates stem file
- **Expected**: WAV file at 48kHz, stereo, 32-bit float, valid header
- **Validation**: `ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -of default=noprint_wrappers=1 stem_0.wav | grep -E "pcm_f32le|48000|2"`

### AC-16: Bridge JSON Config Is Valid JSON
- **Command**: (internal pipeline step) Write bridge config JSON
- **Expected**: Valid JSON structure matching schema
- **Validation**: `cat bridge.json | python3 -m json.tool > /dev/null; echo $?` (exit code 0 = valid)

### AC-17: Bridge Config Includes All Required Fields
- **Command**: (internal pipeline step) Write bridge config JSON
- **Expected**: Config contains sampleRate, channels, duration, bpm, key, inputStems, outputPath, effects
- **Validation**: `cat bridge.json | python3 -c "import json, sys; c=json.load(sys.stdin); print(all(k in c for k in ['sampleRate','channels','duration','bpm','key','inputStems','outputPath','effects']))"`

### AC-18: Effects Engine Processes Without Errors
- **Command**: `node packages/effects/dist/index.js --config bridge.json`
- **Expected**: Exit code 0, output WAV file created
- **Validation**: `node packages/effects/dist/index.js --config bridge.json; echo $?` AND `ls -lh output/processed.wav`

### AC-19: Effects Engine Validates Input Stems
- **Command**: `node packages/effects/dist/index.js --config bridge.json` with invalid stem path
- **Expected**: Non-zero exit code, error message logged
- **Validation**: `node packages/effects/dist/index.js --config invalid_config.json 2>&1 | grep -i error; echo $?` (non-zero)

---

## Integration

### AC-20: Full 2-Hour Mix Generation Succeeds
- **Command**: `openmusic generate --length 2h --output mix.flac --style dub_techno`
- **Expected**: Generates valid 2-hour FLAC file without errors
- **Validation**: `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 mix.flac | grep -E '^(7199|7200|7201)$'` (within ±1 second of 2 hours)

### AC-21: Mix Has Correct Structure (Intro → Development → Climax → Outro)
- **Command**: `openmusic generate --length 1h --output test.flac`
- **Expected**: Mix contains multiple segments with crossfade overlaps
- **Validation**: `ffprobe -i test.flac -show_entries packet=pts_time,flags -of csv | grep -c "K"` (count keyframes, should be ~20 segments for 1 hour)

### AC-22: Config File Parsing Works
- **Command**: `openmusic generate --config user_config.json`
- **Expected**: Reads config file and applies settings
- **Validation**: `cat user_config.json | python3 -m json.tool > /dev/null; openmusic generate --config user_config.json --output test.flac; ls -lh test.flac`

### AC-23: Tempo Is Within Acceptable Range
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: BPM between 120 and 130 (default 125)
- **Validation**: Extract BPM from metadata OR analyze beat detection: `aubio test.flac` or `librosa.beat.beat_track` (Python)

### AC-24: Key Is Minor (D, E, A, C, F, or B minor)
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Musical key is minor tonality
- **Validation**: `keyfinder test.flac` OR `python3 -c "import librosa; y,sr=librosa.load('test.flac'); chroma=librosa.feature.chroma_stft(y=y,sr=sr); print('minor' if chroma.mean(axis=1)[0] < chroma.mean(axis=1)[4] else 'major')"`

---

## Testing

### AC-25: All Unit Tests Pass
- **Command**: `pytest tests/ -v`
- **Expected**: All tests pass, no failures or errors
- **Validation**: `pytest tests/ -v | tail -5 | grep -E 'passed|failed|error'` (should show X passed, 0 failed, 0 errors)

### AC-26: All Integration Tests Pass
- **Command**: `pytest tests/integration/ -v`
- **Expected**: All integration tests pass
- **Validation**: `pytest tests/integration/ -v | tail -5 | grep -E 'passed|failed|error'` (should show X passed, 0 failed, 0 errors)

### AC-27: Code Coverage Meets Threshold
- **Command**: `pytest --cov=. --cov-report=term-missing tests/`
- **Expected**: Coverage ≥ 70% for core modules
- **Validation**: `pytest --cov=. --cov-report=term-missing tests/ | grep TOTAL | awk '{print ($4 >= 70) ? "PASS" : "FAIL"}' | grep PASS`

### AC-28: TypeScript Compiles Without Errors
- **Command**: `npm run build` (in packages/effects and @openmusic/cli)
- **Expected**: No TypeScript compilation errors
- **Validation**: `npm run build 2>&1 | grep -i error; echo $?` (should be 0, no errors)

### AC-29: Linting Passes (Python and TypeScript)
- **Command**: `ruff check .` AND `npm run lint`
- **Expected**: No linting errors
- **Validation**: `ruff check .; echo $?` (exit 0) AND `npm run lint; echo $?` (exit 0)

### AC-30: Type Checking Passes
- **Command**: `tsc --noEmit` (for TypeScript packages)
- **Expected**: No type errors
- **Validation**: `tsc --noEmit; echo $?` (exit 0)

---

## Performance

### AC-31: Segment Generation Time Acceptable
- **Command**: `time openmusic generate --length 3m --output test.flac`
- **Expected**: 3-minute segment generates in reasonable time (< 10 minutes on RTX 2060)
- **Validation**: `time openmusic generate --length 3m --output test.flac` (check real time < 600s)

### AC-32: Effects Processing Time Acceptable
- **Command**: `time node packages/effects/dist/index.js --config bridge.json` (3-minute segment)
- **Expected**: Effects processing completes in < 30 seconds for 3-minute segment
- **Validation**: `time node packages/effects/dist/index.js --config bridge.json` (check real time < 30s)

### AC-33: Memory Usage Within Limits
- **Command**: `openmusic generate --length 2h --output mix.flac` (monitor with `/usr/bin/time -v`)
- **Expected**: Peak memory < 12GB (fits within typical development machine)
- **Validation**: `/usr/bin/time -v openmusic generate --length 2h --output mix.flac 2>&1 | grep "Maximum resident set size" | awk '{print ($6 < 12582912) ? "PASS" : "FAIL"}' | grep PASS`

---

## Crossfade and Transitions

### AC-34: Segments Have Proper Crossfade Overlap
- **Command**: (internal pipeline check) Analyze segment boundaries
- **Expected**: Crossfade overlap of ~2 seconds (4 beats at 125 BPM)
- **Validation**: `ffmpeg -i mix.flac -af "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=log.txt" -f null -` AND analyze RMS at boundaries

### AC-35: No Clicks or Pops at Transitions
- **Command**: `openmusic generate --length 10m --output test.flac`
- **Expected**: No transient artifacts at segment boundaries
- **Validation**: `sox test.flac -n stat 2>&1 | grep "Minimum amplitude:" | awk '{print ($3 > -1) ? "PASS" : "FAIL"}'` (no -infinite dB drops)

---

## File Cleanup

### AC-36: Temp Files Cleaned Up After Success
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: No temp directories remaining after successful generation
- **Validation**: `ls /tmp/openmusic-* 2>&1 | grep -q "No such file"` OR count should be 0

### AC-37: Temp Files Preserved on Error
- **Command**: `openmusic generate --length 1m --output /invalid/path/test.flac` (force error)
- **Expected**: Temp directory preserved for debugging
- **Validation**: `ls /tmp/openmusic-* | grep -q "openmusic-"` (temp dir exists)

---

## Format Conversion

### AC-38: WAV to FLAC Conversion Preserves Quality
- **Command**: (internal pipeline step) Convert WAV to FLAC
- **Expected**: FLAC file has same duration, sample rate, channels as source WAV
- **Validation**: `ffprobe -i input.wav -show_entries format=duration,stream=sample_rate,channels -of csv > wav_info.txt && ffprobe -i output.flac -show_entries format=duration,stream=sample_rate,channels -of csv > flac_info.txt && diff wav_info.txt flac_info.txt`

### AC-39: FLAC Is Losslessly Compressed
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: FLAC file is smaller than equivalent WAV
- **Validation**: `ffmpeg -i test.flac test.wav; ls -l test.flac | awk '{print $5}'` < `ls -l test.wav | awk '{print $5}'`

---

## Config Validation

### AC-40: Invalid BPM Is Rejected
- **Command**: `openmusic generate --length 1m --bpm 200 --output test.flac`
- **Expected**: Command fails with error message about BPM out of range
- **Validation**: `openmusic generate --length 1m --bpm 200 --output test.flac 2>&1 | grep -i "bpm.*range\|out of range"; echo $?` (non-zero exit code)

### AC-41: Invalid Duration Is Rejected
- **Command**: `openmusic generate --length 30s --output test.flac` (too short)
- **Expected**: Command fails with error message about minimum duration
- **Validation**: `openmusic generate --length 30s --output test.flac 2>&1 | grep -i "duration.*minimum\|too short"; echo $?` (non-zero)

### AC-42: Invalid Key Is Rejected
- **Command**: `openmusic generate --length 1m --key Xmajor --output test.flac` (invalid key)
- **Expected**: Command fails with error message about invalid key
- **Validation**: `openmusic generate --length 1m --key Xmajor --output test.flac 2>&1 | grep -i "key.*invalid\|not supported"; echo $?` (non-zero)

---

## Effects Verification

### AC-43: Reverb Tail Is Present
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Reverb decay audible (verified via frequency decay analysis)
- **Validation**: `ffmpeg -i test.flac -af "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=reverb.log" -f null -` AND analyze decay tail (RMS should decay gradually over ~3 seconds)

### AC-44: Delay Echoes Are Present
- **Command**: `openmusic generate --length 30s --output test.flac`
- **Expected**: Delay echoes at ~3/16 and 1/8 note intervals
- **Validation**: Visual inspection with spectrogram OR use autocorrelation to detect echo patterns

### AC-45: Filter Modulation Is Present
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Bandpass filter modulation (LFO) creates movement
- **Validation**: `sox test.flac -n spectrogram -o filter_spectrogram.png` (visual check for frequency band movement) OR analyze frequency spectrum over time

### AC-46: Saturation Is Subtle (No Heavy Distortion)
- **Command**: `openmusic generate --length 1m --output test.flac`
- **Expected**: Harmonic content is intact, no excessive distortion
- **Validation**: `sox test.flac -n stat 2>&1 | grep "Crest factor"` (should be > 10 dB, indicating preserved dynamics) OR THD analysis

---

## Bridge Communication

### AC-47: Bridge Process Exits Cleanly
- **Command**: `node packages/effects/dist/index.js --config bridge.json`
- **Expected**: Node.js process exits with code 0
- **Validation**: `node packages/effects/dist/index.js --config bridge.json; echo $?` (exit code 0)

### AC-48: Bridge Writes Success Status on Success
- **Command**: `node packages/effects/dist/index.js --config bridge.json`
- **Expected**: Success file written with status field
- **Validation**: `cat /tmp/openmusic-*/status.json | python3 -c "import json, sys; print(json.load(sys.stdin)['success'])"` (should be `true`)

### AC-49: Bridge Writes Error File on Failure
- **Command**: `node packages/effects/dist/index.js --config invalid_bridge.json`
- **Expected**: Error file written with error details and stage
- **Validation**: `cat /tmp/openmusic-*/status.json | python3 -c "import json, sys; d=json.load(sys.stdin); print(d['success'], d.get('error', ''))"` (should be `false` with error message)

---

## Pattern Generation

### AC-50: Pattern Definitions Are Valid
- **Command**: (internal) Load pattern definitions from @openmusic/patterns
- **Expected**: Patterns compile and run without errors
- **Validation**: `node -e "require('@openmusic/patterns'); console.log('OK')"` (should print 'OK')

---

## Summary

**Total Acceptance Criteria: 50**

**Categories:**
- CLI Interface: 4 criteria
- Audio Output: 4 criteria
- Audio Quality: 6 criteria
- Pipeline: 5 criteria
- Integration: 5 criteria
- Testing: 6 criteria
- Performance: 3 criteria
- Crossfade and Transitions: 2 criteria
- File Cleanup: 2 criteria
- Format Conversion: 2 criteria
- Config Validation: 3 criteria
- Effects Verification: 4 criteria
- Bridge Communication: 3 criteria
- Pattern Generation: 1 criterion

**Critical Path (Must Pass for Release):**
- AC-20: Full 2-Hour Mix Generation
- AC-25: All Unit Tests Pass
- AC-26: All Integration Tests Pass
- AC-5, AC-6, AC-7: Audio Format Specifications
- AC-9, AC-10: Audio Quality Specifications
