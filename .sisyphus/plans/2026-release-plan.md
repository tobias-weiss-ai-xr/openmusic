# 2026 Release Plan — OpenMusic YouTube

**Created**: 2026-06-13
**Period**: June 13 → December 31, 2026 (~28 weeks)

---

## Content Categories

| # | Category | Format | Playlist | Existing |
|---|----------|--------|----------|----------|
| 1 | **Dub Techno Mixes** | Full-length ~2h | "Dub Techno Mixes" | 3 archived |
| 2 | **Stoic Shorts** | 30s quote videos | "Stoic & DevOps Shorts" | 8 published |
| 3 | **DevOps Shorts** | 20s code tips | "Stoic & DevOps Shorts" | 8 published |
| 4 | **AI Shorts** | 20s AI/ML tips | "AI & Graph Knowledge Shorts" | 8 published |
| 5 | **Graph Shorts** | 20s Cypher/knowledge graph tips | "AI & Graph Knowledge Shorts" | 7 published |

*Note: Consider splitting into separate playlists per category for better channel organization.*

---

## Cadence

| Day | Content | Duration |
|-----|---------|----------|
| **Mon** | DevOps short | 20s |
| **Wed** | AI short | 20s |
| **Fri** | Graph short | 20s |
| **Sat** | Full mix (bi-weekly) | ~2h |
| **Sun** | Stoic short | 30s |

**Total**: 4 shorts/week + 2 mixes/month = ~123 videos by Dec 31.

---

## Production Logistics

### Mix Generation
- **Run**: `openmusic generate --length 2h --bpm 125 --key Dm --output mix_YYYYMM.flac`
- **Timing**: Start Friday evening (~10h CPU on turbo 8-step), upload Saturday
- **Seed**: Use different seeds per mix for variety
- **Storage**: Keep source FLAC (source for shorts), output MP4 for YouTube

### Short Generation
- **Source audio**: Use latest mix.flac segments (different positions each batch)
- **Batch**: Generate monthly (~16 shorts at once, ~30 min rendering)
- **Positions**: Stagger across the full mix duration (avoid reusing same audio)
- **Commands**:
  - Stoic: `openmusic short batch --audio mix.flac --positions "<comma-separated>" --output-dir shorts/`
  - DevOps/AI/Graph: `openmusic short devops-generate --audio mix.flac --position <secs> --category <cat> --upload`

### Upload
- **Auth**: OAuth token (auto-refreshes) via `openmusic auth-youtube`
- **Tool**: `youtube-up video --cookies_file youtube_token.json ...`
- **Privacy**: unlisted → public after review

---

## Monthly Content Targets

| Month | Mixes | DevOps | AI | Graph | Stoic | Total |
|-------|-------|--------|----|-------|-------|-------|
| **Jun** (14-30) | 0 | 2 | 2 | 1 | 2 | 7 |
| **Jul** | 2 | 4 | 4 | 4 | 4 | 18 |
| **Aug** | 2 | 4 | 4 | 4 | 4 | 18 |
| **Sep** | 2 | 5 | 5 | 4 | 5 | 21 |
| **Oct** | 2 | 4 | 4 | 5 | 4 | 19 |
| **Nov** | 2 | 5 | 4 | 4 | 4 | 19 |
| **Dec** | 3 | 4 | 5 | 4 | 5 | 21 |
| **Total** | **13** | **28** | **28** | **26** | **28** | **123** |

---

## Content Expansion Roadmap

### DevOps (expand by +5 tips/month = ~30 new)
- **Jun**: Terraform, Cloud (AWS/GCP basics), Security scanning, Docker networking
- **Jul**: Ansible roles, K8s Helm charts, Prometheus alerting, GitHub Actions advanced
- **Aug**: Terraform modules, IaC best practices, Service mesh, OpenTelemetry
- **Sep**: CI/CD blue/green, Canary deployments, Secret management, Vault
- **Oct**: Linux performance tuning, Systemd deep dive, Nginx advanced, SSL/TLS
- **Nov**: Docker Compose prod, K8s operators, Cloud cost optimization, Chaos engineering
- **Dec**: Year in review, SRE principles, Incident response, Post-mortems

### AI (expand by +4 tips/month = ~24 new)
- **Jun**: LLM evaluation, Prompt chaining, Embedding pipelines, Reranking
- **Jul**: Agent tool use, Multi-agent systems, LangGraph, Guardrails
- **Aug**: Fine-tuning data prep, QLoRA, RLHF basics, Model quantization
- **Sep**: Vision LLMs, Multimodal RAG, Text-to-speech, Speech-to-text
- **Oct**: MCP protocol, Function calling advanced, Caching strategies, Rate limiting
- **Nov**: A/B evaluation, Model routing, Cost optimization, Streaming responses
- **Dec**: Edge deployment, On-device AI, Privacy-preserving ML, Synthetic data

### Graph (expand by +4 tips/month = ~24 new)
- **Jun**: Graph algorithms (BFS, DFS), Path finding, Centrality, Community detection
- **Jul**: Neo4j APOC, Graph data science, Node embeddings, GraphSAGE
- **Aug**: GraphQL basics, Schema design, Resolvers, Federation
- **Sep**: Property graph vs RDF, RDF/OWL, SPARQL basics, Linked data
- **Oct**: Graph visualization, D3 force-directed, Neo4j Bloom, GraphXR
- **Nov**: Temporal graphs, Event-sourced graphs, Graph streaming, Change data capture
- **Dec**: LLM + Graph integration, GraphRAG advanced, Knowledge graph completion, Graph benchmarks

### Stoic (add +5 quotes/month = ~30 new — only needed if current ~449 are exhausted)

---

## Mix Theme Schedule

| Date | Theme | BPM | Key | Notes |
|------|-------|-----|-----|-------|
| Jun 27 | Deep Minimal Dub | 125 | Dm | First release |
| Jul 11 | Dark Ambient Dub | 110 | Am | Lower BPM, atmospheric |
| Jul 25 | Detroit Techno | 128 | F#m | Classic techno vibes |
| Aug 8 | Club Dub | 130 | Cm | Dancefloor-focused |
| Aug 22 | Deep Hypnotic | 120 | Ebm | Hypnotic repetition |
| Sep 5 | Berlin Sound | 125 | Dm | Traditional dub techno |
| Sep 19 | Sci-Fi Ambient | 100 | Bm | Experimental textures |
| Oct 3 | Halloween Dark | 115 | Fm | Dark, industrial |
| Oct 17 | Percussion Focus | 128 | G#m | Rhythm-heavy |
| Nov 7 | Vintage Basic Channel | 125 | Dm | Tribute to the originals |
| Nov 21 | Winter Deep | 110 | Am | Cold, sparse |
| Dec 5 | Holiday Ambient | 100 | C | Warm, peaceful |
| Dec 19 | Year-End Retrospective | 125 | Dm | Best segments compilation |
| Dec 31 | New Year's Eve Special | 130 | Fm | Peak-time celebration |

---

## Queue Structure
When a new mix is generated, the previous mix becomes the shorts source. This gives ~2 weeks of shorts material per mix before the next one arrives.

```
Mix N (generated) → live on YouTube + source audio for shorts
Mix N+1 (generating) → replaces Mix N as shorts source when done
```

---

## Automation Roadmap

- [ ] `openmusic release` command: generate + render + upload in one shot
- [ ] Monthly batch short generation with content rotation
- [ ] Playlist management auto-create/append
- [ ] Scheduling system (cron-based mix generation overnight)
- [ ] Analytics tracking (views/subs per content type)
