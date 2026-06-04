# DevOps/AI Shorts Design

## Goal

Create automated short videos (15-30s) featuring practical DevOps and AI tips from tobias-weiss.org cheatsheets and articles, using dub techno audio backgrounds.

## Format

- **Duration**: 15-30s per short
- **Layout**: Split-screen vertical (9:16)
  - Top/right: Code snippet with syntax highlighting
  - Bottom/left: Explanatory text with fade-in animation
- **Audio**: Dub techno background (ACE-Step or Tone.js effects)
- **Visual style**: Dark theme matching the stoic shorts aesthetic

## Content Sources

### Cheatsheets (23 total):
- Docker commands and best practices
- CI/CD pipeline patterns
- Kubernetes manifests and deployments
- Ansible playbooks
- Git workflows
- Linux system administration
- Monitoring and observability
- Security practices
- Performance profiling

### AI Articles (9 total):
- XGBoost tuning strategies
- LangChain vs routing patterns
- Gemma 4 optimizations
- RAG architectures
- LLM prompting techniques
- ML deployment patterns
- Data engineering best practices

## Visual Layout

```
┌─────────────────────┐
│  [95%] # CODE      │  ← Split top: Code snippet (dark bg)
│  docker run -d \    │     70% height, syntax highligted
│    -p 80:80 \       │
│    -v /data:/data   │
│    nginx            │
│                     │
│─────────────────────│
│  [5%] # TIP        │  ← Split bottom: Tip text (animated)
│  Run detached     │     30% height, fades in after 2s
│  containers in    │
│  background       │
└─────────────────────┘
```

## Pipeline Architecture

Reuse existing infrastructure from stoic shorts:

```
[Content DB: DevOpsAIDatabase]
    ↓
[HTML Template: devops_template.html]  ← Split-screen layout
    ↓
[Playwright Renderer: record split-screen]
    ↓
[ffmpeg: merge audio + convert to shorts]
    ↓
[Output: short_devops_N.mp4]
```

### Key Components

1. **devops_content.py** - Database of tips with code snippets
2. **devops_templates.py** - Split-screen HTML generator with syntax highlighting
3. **pipeline.py** - Existing ShortsPipeline (reused for audio/rendering/compositing)
4. **CLI** - `openmusic short devops` commands

## Content Database Structure

```python
DevOpsTip = namedtuple("DevOpsTip", [
    "title",           # Short title: "Docker Detached Mode"
    "code",            # Code snippet: docker run -d -p 80:80 nginx
    "language",        # Syntax highlighting: "docker", "python", "yaml", etc.
    "description",     # Explanatory text: "Run containers in background mode"
    "category",        # Category: "docker", "k8s", "ci", "ai", etc.
    "source",          # Source URL
])

TIPS: list[DevOpsTip] = [...]
```

## HTML Template

Split-screen layout using CSS Grid:

```css
.devops-container {
  display: grid;
  grid-template-rows: 70% 30%;
  height: 1920px;
  background: #020204;
}

.code-pane {
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 48px;
  padding: 60px;
  overflow: hidden;
}

.tip-pane {
  padding: 40px;
  animation: tipFade 2s ease-in-out;
}
```

## CLI Commands

```bash
# Generate single DevOps tip short
openmusic short devops \
  --audio dub_mix.flac \
  --position 300 \
  --category docker \
  --output /tmp/docker_tip.mp4

# Generate batch from categories
openmusic short devops-batch \
  --audio dub_mix.flac \
  --categories docker,k8s,ci \
  --positions "300,600,900,1200" \
  --output-dir ./devops_shorts/
```

## Implementation Plan

### Phase 1: Content Database
1. Fetch and parse cheatsheets from tobias-weiss.org
2. Extract code snippets and descriptions
3. Create TIPS database with proper categorization
4. Add unit tests for content lookups

### Phase 2: Split-Screen Templates
1. Create devops_template.html with syntax highlighting
2. Integrate prism.js or highlight.js for code coloring
3. Design tip-pane fade-in animation
4. Test layout across different code snippet lengths

### Phase 3: Integration with Existing Pipeline
1. Create DevOpsConfig for ShortsPipeline
2. Add devops-specific rendering parameters
3. Test with sample tips

### Phase 4: CLI Commands
1. Create short.py devops commands
2. Add filtering by category/language
3. Add batch generation support
4. End-to-end testing

## Technical Considerations

- **Syntax Highlighting**: Use Prism.js (lightweight, many languages supported)
- **Code Truncation**: Long snippets should be truncated with ellipsis
- **Text Fading**: Tip text fades in at 2s, stays visible to end
- **Fonts**: Monospace for code (Fira Code), clean sans-serif for tips
- **Colors**: Match stoic shorts color scheme (c8b898 text, 7a6a4a accents)

## Success Criteria

- Generate 30+ unique DevOps/AI shorts
- Each short is 15-30s duration
- Split-screen layout renders correctly on all phones
- Code snippets are syntax-highlighted and readable
- Batch generation produces consistent quality
- Automated pipeline produces 1 short/minute throughput

## Future Enhancements

- Add animated code typing effect
- Include ASCII art diagrams where applicable
- Support multiple tip texts with carousel
- Add channel branding overlay
- Generate content from other sources (GitHub, Stack Overflow)