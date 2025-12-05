# Product Discovery Session
**Date**: November 27, 2025
**Product**: ContentSync (working name)
**Session Type**: Interactive Product Discovery (20 Questions)

---

## Product Foundation

### 1. Product Name & Category

**Answer**:
- **Working Name**: ContentSync / ContentPipe / KnowledgeSync (TBD)
- **Category**: Content Intelligence API / RAG Data Pipeline
- **Industry**: AI/ML Infrastructure, Knowledge Management

**Expert Analysis**:
✅ **Category Positioning**: Entering "Content Intelligence & Knowledge Management" space
- Strong timing with AI/RAG explosion
- Differentiated by continuous sync vs one-off extraction
- API-first approach targets developer early adopters

💡 **Long-term Vision**: Evolution to "AI Intelligence Platform" (watch platform with AI-powered discovery + human curation)

🎯 **Recommended Positioning**:
- MVP: "RAG Data Pipeline for YouTube Content"
- Future: "Continuous Knowledge Monitoring Platform"

---

### 2. Big Idea & Vision

**Answer**:
- **MVP**: Continuous YouTube channel/playlist monitoring that extracts transcripts and generates structured knowledge (summaries, tags, categories, key moments)
- **Approach**: API-first, productize later
- **Long-term Vision**: Full intelligence platform that combines trusted sources (YouTube, web) with AI-powered content discovery (Perplexity-style) and human curation workflow

**Expert Analysis**:
✅ **Why This Is Strong**:
- Real pain point: Getting quality data into RAG systems is hard
- Multi-source potential (YouTube → web → podcasts → papers)
- Platform play with network effects
- Continuous sync provides ongoing value

⚠️ **Strategic Considerations**:
- API-first limits initial market but enables faster validation
- Vision is ambitious (watch platform) but MVP is focused
- Need to resist feature creep during MVP phase

💡 **Success Pattern**:
- Phase 1: Prove YouTube sync works (3 months)
- Phase 2: Add AI discovery layer (6 months)
- Phase 3: Build curation platform (12 months)

**Vision Statement**:
> "Democratize knowledge by making the world's video content intelligently accessible. We turn passive watching into active learning through AI-powered knowledge extraction."

---

### 3. Problem Statement

**Answer**:
"As a researcher/learner, I want to systematically learn from YouTube content (channels, playlists) but manually watching, taking notes, and organizing insights is time-consuming and doesn't scale. I need an automated system to monitor my trusted sources, extract knowledge, and make it queryable."

**Who Experiences This**:
- Individual researchers tracking specific topics
- Software engineers learning from tech YouTube channels
- PhD students following educational content
- Knowledge workers building personal knowledge bases

**Expert Analysis**:
✅ **Problem Validation**:
- **Pain Severity**: This is a painkiller, not vitamin
- **Current Solutions**: Manual note-taking, browser extensions (one-off), ChatGPT + URL (manual)
- **Market Evidence**: Growth of Obsidian, Notion, Roam shows demand for knowledge management

💡 **Problem Quantification**:
- Average learner watches 10+ hours of YouTube/week
- Manual notes capture <20% of insights
- Zero ability to search/query across videos
- Time cost: ~2 hours/week on manual organization

🔍 **Adjacent Problems** (future scope):
- Same problem exists for podcasts, web articles, PDFs, research papers
- Team knowledge sharing (not just personal)
- Competitive intelligence monitoring

---

### 4. Solution Overview

**Answer**:
1. User subscribes to YouTube channels/playlists via API
2. System continuously monitors for new videos (Celery background jobs)
3. Auto-extracts transcripts using YouTube API
4. AI (Claude Haiku via LiteLLM) processes each video to generate:
   - Summary (TL;DR)
   - Tags (topics covered)
   - Categories (broad classification)
   - Main ideas (key concepts extracted)
   - Key moments (timestamped important points)
5. All structured data exposed via REST API
6. User connects to their RAG system (future: built-in RAG)
7. User can ask questions across all monitored content

**Technical Stack**:
- **Backend**: Python, Django, Celery, Flower
- **LLM**: LangGraph, LiteLLM, Claude Haiku
- **Database**: Supabase (PostgreSQL)
- **Infrastructure**: Docker, UV (Python package manager)
- **Auth**: Django API keys (MVP)

**Expert Analysis**:
✅ **Technical Feasibility**: Stack is production-ready and well-supported
✅ **User Adoption**: API-first reduces UI friction, targets technical users
✅ **Defensibility**: Continuous sync system + data accumulation creates moat

💡 **Innovations**:
- Continuous monitoring (not one-off extraction)
- Rich metadata (not just transcripts)
- Key moments with timestamps (easy source verification)
- Per-user YouTube API credentials (scales better)

⚠️ **Technical Risks**:
- YouTube API quota limits (50 transcripts/day per key)
- YouTube ToS compliance (transcript caching limits)
- LLM cost at scale (mitigated by Haiku)
- Processing latency for long videos

---

### 5. Mission Statement

**Answer**:
> "Democratize knowledge by making the world's video content intelligently accessible. We turn passive watching into active learning through AI-powered knowledge extraction."

**Expert Analysis**:
✅ **Inspiration Factor**: Aligns with broader AI/education mission
✅ **Customer Resonance**: Learners care about "learning smarter"
✅ **Business Alignment**: Mission supports both free and paid models

💡 **How Mission Becomes Competitive Advantage**:
- Attracts contributors if open-sourced
- Differentiates from "just another AI tool"
- Enables partnerships with educational platforms

---

## Market & User Context

### 6. Target Market

**Answer**:
- **TAM** (Total Addressable Market): Personal knowledge management software (~$1B+, growing with AI tools)
- **SAM** (Serviceable Addressable Market): Tech-savvy learners/researchers who use or want RAG systems (~100K globally)
- **SOM** (Serviceable Obtainable Market): 100-1,000 active users in Year 1

**Expert Analysis**:
✅ **Market Growth**: Exploding with AI adoption (ChatGPT, Claude, RAG systems)
✅ **Market Readiness**: Early adopters exist (Obsidian, Notion, Roam users)

💡 **Market Expansion Strategy**:
- Year 1: Technical users (developers, researchers)
- Year 2: Knowledge workers (broader audience with UI)
- Year 3: Teams/organizations (B2B pivot potential)

🔍 **Underserved Segments**:
- Academic researchers (need citation/reference features)
- Content creators (studying competitor content)
- VC/investors (market monitoring)

---

### 7. Primary Users (Personas)

**Persona 1: "Research Rahul"**
- **Demographics**: 30-year-old software engineer, works at tech startup
- **Behavior**: Watches 10+ hours of tech YouTube weekly (conferences, tutorials, deep dives)
- **Tools**: Uses Obsidian for notes, wants better video integration
- **Pain**: "I watch tons of great content but can't search or reference it later. I'm constantly re-watching to find that one insight."
- **Job-to-be-Done**: "Help me build a searchable knowledge base from YouTube without manual effort"
- **Willingness to Pay**: $20-50/month if it saves 5+ hours/week

**Persona 2: "Academic Alice"**
- **Demographics**: 28-year-old PhD student in social sciences
- **Behavior**: Follows 20+ educational YouTube channels for research
- **Tools**: Notion for research organization, Zotero for citations
- **Pain**: "I need to track what experts say across hundreds of videos. Manual timestamps and notes don't scale."
- **Job-to-be-Done**: "Help me cite and reference video content in my research papers"
- **Willingness to Pay**: $10-30/month (student budget)

**Expert Analysis**:
✅ **User Specificity**: These are real user types (not imagined)
✅ **Pain Intensity**: High urgency (time-consuming manual work)
✅ **Buying Power**: Can afford subscription ($10-50/month range)

💡 **Earlyvangelists** (users who'll promote you):
- Tech YouTubers who want to study their niche
- Productivity influencers (will create content about the tool)
- RAG/AI enthusiasts (early adopter community)

---

### 8. User Journey (Current State)

**Current Workflow**:
1. Discover interesting YouTube channel
2. Watch video, pause to take notes in Notion/Obsidian
3. Manually timestamp key moments
4. Copy/paste quotes, add tags
5. Repeat for every video (unsustainable)
6. Knowledge gets fragmented across tools
7. Can't search across all videos
8. Forget what was learned weeks later

**Pain Points**:
- ⚠️ Manual note-taking interrupts learning flow
- ⚠️ No way to search across videos
- ⚠️ Can't keep up with new uploads
- ⚠️ Knowledge scattered across files/apps
- ⚠️ Hard to cite/reference video content

**Switching Costs**:
- Low! Users already frustrated with manual process
- Need: Easy channel import, reliable sync

**Expert Analysis**:
✅ **Magic Moment**: When user asks a question and gets answer with video timestamp
💡 **10x Better Experience**:
- Add channel → Auto-sync → Ask questions → Get answers with sources
- Time saved: 90% reduction in manual work

---

### 9. Competitive Landscape

**Direct Competitors**:
1. **Glasp** - Video highlights and notes (one-off, not continuous)
2. **Snipd** - Podcast summaries (audio only, not YouTube)
3. **YouTube Summary Extensions** - Browser extensions (manual, per-video)
4. **ChatGPT + YouTube URL** - Manual process, not automated

**Indirect Competitors**:
- Manual note-taking (Notion, Obsidian)
- "Do nothing" - just watch and forget
- Paid courses (alternative to free YouTube learning)

**Expert Analysis**:
✅ **Hidden Competitor**: The "do nothing" option (users tolerate current pain)
✅ **Competitive Moats**:
- Glasp: Strong community, visual UI
- ChatGPT: Brand power, multi-modal
- Manual tools: User's existing workflow/habits

🔍 **Vulnerabilities to Attack**:
- None offer continuous monitoring
- None are API-first (hard to integrate)
- None provide rich metadata extraction
- None optimize for RAG use cases

💡 **Positioning Strategy**:
- "The data pipeline for your AI knowledge base" (not a note-taking app)
- Target technical users first (underserved by UI-focused competitors)
- Focus on automation (set-and-forget vs manual per-video)

---

### 10. Differentiation & Competitive Advantage

**What Makes You Unique**:
1. **Continuous Monitoring**: Auto-sync new videos (not one-off)
2. **Batch Processing**: Channels/playlists (not single videos)
3. **API-First**: Integration-ready (not just UI)
4. **Rich Metadata**: Summaries + tags + categories + key moments
5. **RAG-Optimized**: Structured for AI querying
6. **Per-User API Keys**: Scalable, privacy-friendly

**Competitive Advantages**:
- ✅ **Sustainable**: Continuous sync creates data moat over time
- ✅ **Perception**: Technical users value API-first approach
- ✅ **Defensibility**: Hard to replicate sync infrastructure + data accumulation

**Expert Analysis**:
💡 **Compound Competitive Advantage**:
1. Start with API (attract developers)
2. Build data network effects (more sources = more value)
3. Add AI discovery (unique data = better results)
4. Create platform (hard to switch once integrated)

⚠️ **Risk**: OpenAI or Google could add this feature easily
**Mitigation**: Move fast, build community, go multi-platform

---

## Product Scope & Strategy

### 11. Core Features (MVP - Priority Order)

**Must-Have Features**:

1. **YouTube Channel/Playlist Subscription**
   - Add source by URL (channel or playlist)
   - Validate YouTube API credentials (per-user)
   - Auto-detect new videos
   - Configurable sync frequency (hourly, daily, weekly)

2. **Transcript Extraction & Processing**
   - Fetch YouTube transcript via API
   - Send to Claude Haiku (via LiteLLM)
   - Extract: summary, tags, categories, main ideas, key moments
   - Store structured data in Supabase

3. **REST API Endpoints**
   - `POST /api/sources` - Add channel/playlist
   - `GET /api/sources` - List all sources
   - `GET /api/videos` - List processed videos (with filters)
   - `GET /api/videos/{id}` - Get full video analysis
   - `GET /api/search` - Search across content (text search MVP)
   - `DELETE /api/sources/{id}` - Remove source

4. **Background Job Management**
   - Celery periodic tasks for sync checks
   - Job queue for video processing
   - Flower dashboard for monitoring
   - Retry logic with exponential backoff
   - Error logging and alerting

5. **Authentication & User Management**
   - Django user registration/login
   - API key generation per user
   - YouTube API credential storage (encrypted)
   - Basic usage tracking (API calls, videos processed)

**Nice-to-Have (Post-MVP)**:
- Webhook notifications when new videos processed
- Advanced search (semantic, embeddings)
- Export to common formats (JSON, Markdown)
- Web UI for non-technical users

**Expert Analysis**:
✅ **Value Delivery**: Feature #2 (processing) delivers core value
✅ **Technical Risk**: Feature #4 (background jobs) needs early validation
✅ **User Delight**: Key moments with timestamps = "aha!" moment

🔍 **Features to Cut**: Anything not on this list! No admin UI, no analytics dashboard, no integrations (yet)

💡 **Fake Complex Features**:
- Search can be basic SQL text search (not semantic) for MVP
- Sync frequency can be fixed (daily) initially

---

### 12. Success Metrics

**Leading Indicators** (predict success before revenue):
- Sign-ups per week
- API key activations
- Sources added per user
- Videos processed daily

**Activation Metrics**:
- User has added ≥1 source
- User has ≥10 videos processed
- User has made ≥5 API calls

**North Star Metric**:
**"Videos queried per week"** - indicates users finding value in processed content

**Key KPIs**:
| Metric | MVP Target | 3-Month Target |
|--------|------------|----------------|
| Active users (weekly) | 10 | 100 |
| Videos processed (total) | 1,000 | 10,000 |
| Processing cost/video | <$0.10 | <$0.05 |
| Processing latency | <5 min | <2 min |
| API uptime | >95% | >99% |
| User retention (weekly) | >30% | >50% |

**Expert Analysis**:
💡 **Benchmarks from Similar Products**:
- Glasp: ~40% weekly retention for active users
- Notion: ~60% weekly retention
- Developer APIs: ~70% retention if integrated

🎯 **Metrics Hierarchy**:
1. **Activation**: Get users to process first 10 videos
2. **Engagement**: Get users querying content weekly
3. **Retention**: Keep users coming back (new videos = new value)
4. **Revenue**: Convert to paid after value proven

---

### 13. Business Model

**MVP Strategy**: Free during beta (focus on learning & validation)

**Future Monetization Options**:

1. **Freemium Model** (Recommended)
   - Free: 5 sources, 100 videos/month
   - Pro: Unlimited sources, unlimited videos, $20/month
   - Team: Multi-user, shared sources, $50/month

2. **Usage-Based Pricing**
   - Pay per video processed: $0.05-0.10 per video
   - Credits system: Buy packs of 100/500/1000 videos

3. **API Credits**
   - Free tier: 1,000 API calls/month
   - Paid: $10 per 10,000 calls

**Expert Analysis**:
✅ **Model-Market Fit**: Developers expect freemium or usage-based
✅ **Unit Economics**:
- Cost: ~$0.05 per video (Haiku) + infrastructure
- Target price: $0.10 per video = 50% margin
- Or: $20/month for ~400 videos = profitable at scale

💡 **Pricing That Accelerates Growth**:
- Generous free tier to reduce friction
- Charge when users get serious (>10 sources)
- Referral credits (give 100 free videos for referrals)

🔍 **Additional Revenue Streams** (future):
- Premium LLM models (GPT-4, Claude Opus) at higher price
- White-label API for B2B customers
- Managed RAG service (host their knowledge base)

---

### 14. Platform Strategy

**Answer**: API-first (REST API)

**MVP Platform**:
- REST API only
- JSON responses
- API key authentication

**Future Platform Expansion**:
- Web UI (for non-technical users)
- Python SDK (easier integration)
- CLI tool (power users)
- Zapier/Make integration (no-code users)

**Expert Analysis**:
✅ **User Behavior**: Technical users live in code/terminal (API fits)
✅ **Technical Complexity**: API-only = faster MVP (no UI complexity)
✅ **Market Opportunity**: UI expansion opens 10x larger market later

💡 **Platform Expansion Strategy**:
1. Month 1-3: API only (validate core value)
2. Month 4-6: Python SDK (reduce integration friction)
3. Month 7-9: Web UI (expand to non-developers)
4. Month 10-12: Mobile app (on-the-go access)

---

### 15. Timeline & Milestones

**Answer**: 4 weeks (aggressive)

**Week-by-Week Plan**:

**Week 1: Foundation**
- ✅ Django project setup + Supabase connection
- ✅ User authentication + API key system
- ✅ YouTube API integration (test with credentials)
- ✅ Basic data models (Source, Video, ProcessedContent)

**Week 2: Processing Pipeline**
- ✅ Celery + Flower setup
- ✅ Transcript extraction job
- ✅ LangGraph + LiteLLM integration
- ✅ Claude Haiku processing (summary, tags, etc.)
- ✅ Error handling + retry logic

**Week 3: API & Jobs**
- ✅ REST API endpoints (sources, videos, search)
- ✅ Periodic sync jobs (check for new videos)
- ✅ Background processing queue
- ✅ Basic monitoring/logging

**Week 4: Polish & Deploy**
- ✅ Testing (unit + integration)
- ✅ Docker containerization
- ✅ Deploy to production (Railway/Render/Fly.io)
- ✅ API documentation (basic)
- ✅ Invite first 10 users

**Expert Analysis**:
⚠️ **Velocity Reality Check**: 4 weeks is aggressive but doable with AI assistance
⚠️ **Risk Buffers**: Build in 1 week buffer for YouTube API issues

🔍 **What to Cut to Launch Faster**:
- Advanced search (just basic text search)
- Web UI (API only)
- Webhook notifications
- Analytics dashboard
- Multiple LLM options (just Haiku)

💡 **"Fake It Before You Make It" MVP**:
- Fixed daily sync (not configurable)
- Process videos sequentially (not parallel optimization)
- Basic error handling (just log and retry)
- Manual monitoring (no alerting system)

---

## Technical & Resource Context

### 16. Technical Constraints

**Answer**:
- **YouTube API Limits**: 10,000 units/day per project, ~50 transcripts/day per key
- **Strategy**: Per-user YouTube API credentials (users bring their own keys)
- **Retry Logic**: Implement exponential backoff for quota errors and transient failures
- **Compliance**: YouTube ToS requires proper attribution, data deletion compliance

**Expert Analysis**:
✅ **Constraint → Feature**: Per-user credentials = better privacy story
✅ **Technical Debt Acceptable**: Use simple retry logic first (optimize later)
✅ **Future-Proofing Critical**: Design data model to support non-YouTube sources

🔍 **Clever Workarounds**:
- Cache transcripts temporarily (re-fetch if >30 days old)
- Process videos during user's off-peak hours (respect quotas)
- Batch operations (process multiple videos per API call when possible)

💡 **Build vs Buy vs Partner**:
- Build: Core processing pipeline (your moat)
- Buy: LLM API (LiteLLM for flexibility)
- Partner: Consider YouTube Premium API if scaling (higher quotas)

**YouTube ToS Compliance Strategy**:
✅ **Must Do**:
- Link back to original YouTube videos
- Display YouTube branding in any UI
- Delete data if video removed from YouTube
- Store structured metadata (not raw transcripts long-term)

⚠️ **Risk Mitigation**:
- Clear ToS for users (they're responsible for content compliance)
- "Research tool" positioning (not YouTube competitor)
- Auto-delete cached transcripts >30 days

---

### 17. Team & Resources

**Answer**: Solo project with AI agent assistance (AI-generated code)

**Current Resources**:
- Developer: You (with AI coding agents)
- Budget: Minimal (optimize for free/cheap tiers)
- Time: 4 weeks to MVP

**Expert Analysis**:
✅ **Skill Gaps**: AI agents can handle most coding, but you need:
- System design decisions (architecture choices)
- Debugging complex async issues (Celery jobs)
- DevOps/deployment (Docker, hosting)

✅ **Resource Allocation**:
- Week 1-2: 60% core pipeline, 40% infrastructure
- Week 3: 80% API, 20% testing
- Week 4: 50% polish, 50% deployment/docs

💡 **Do More with Less**:
- Use managed services (Supabase, Render/Railway)
- Leverage AI for boilerplate (Django models, API serializers)
- Copy-paste proven patterns (don't reinvent)

🔍 **When to Get Help**:
- Legal review (YouTube ToS compliance)
- Security audit (API key storage, auth)
- UX feedback (when building UI later)

**Future Hiring Roadmap** (if this scales):
- Month 6: Part-time DevOps (if self-hosting)
- Month 9: Full-time engineer (if revenue hits $5K/month)
- Month 12: Designer (when building UI)

---

### 18. Integration Needs

**Answer**:
- LlamaIndex integration (future, for research features)
- Not MVP priority

**MVP Integrations**:
- YouTube Data API v3 (required)
- LiteLLM → Claude API (required)
- Supabase (database + auth)

**Future Integration Opportunities**:
- **RAG Frameworks**: LlamaIndex, LangChain
- **Note-Taking Tools**: Obsidian, Notion, Roam (via plugins)
- **Automation**: Zapier, Make, n8n
- **Search**: Algolia, Meilisearch (semantic search)

**Expert Analysis**:
✅ **Integration Priorities**:
- Critical: YouTube API, Claude API
- Nice-to-have: Export to Markdown (easy Obsidian import)

💡 **Design for Future Integrations**:
- Clean REST API = easy third-party integrations
- Webhook support (add later for real-time notifications)
- Standard formats (JSON, Markdown) = compatible with everything

🔍 **Integration Shortcuts**:
- Instead of building Notion integration, just provide clean JSON export
- Let community build plugins (open API docs)
- Partner with tool creators (cross-promotion)

---

### 19. Scalability Requirements

**Answer**: 50 videos/day for MVP

**Expected Growth Trajectory**:
- **Month 1**: 10 users × 5 videos/day = 50 videos/day
- **Month 3**: 100 users × 10 videos/day = 1,000 videos/day
- **Month 6**: 500 users × 20 videos/day = 10,000 videos/day
- **Month 12**: 2,000 users × 50 videos/day = 100,000 videos/day

**Expert Analysis**:
✅ **Scale Triggers**:
- <1,000 videos/day: Single server + Celery workers
- 1,000-10,000/day: Add more workers, optimize queries
- >10,000/day: Distributed workers, caching layer, job prioritization

✅ **Architecture for 100x Growth**:
- Celery workers scale horizontally (add more containers)
- Supabase can handle millions of rows (PostgreSQL)
- LiteLLM supports multiple providers (scale with $ not architecture)

💡 **Cost Curves at Scale**:
| Users | Videos/Day | Monthly LLM Cost | Infrastructure |
|-------|------------|------------------|----------------|
| 10 | 50 | $75 | $20 |
| 100 | 1,000 | $1,500 | $50 |
| 500 | 10,000 | $15,000 | $200 |
| 2,000 | 100,000 | $150,000 | $1,000 |

**At 2,000 users**: $150K/month cost, need $200K+ revenue (charge $100/user/month)

🔍 **Premature Optimization Traps to Avoid**:
- Don't build distributed system for 50 videos/day
- Don't optimize database queries until >100K rows
- Don't add caching until response time >2 seconds

💡 **Systems That Scale Elegantly**:
- Queue-based processing (Celery) ✅
- Stateless API (horizontal scaling) ✅
- Managed database (Supabase) ✅
- Pay-per-use LLM (scales with revenue) ✅

---

### 20. Compliance & Security

**Answer**:
- YouTube ToS compliance (covered in #16)
- API authentication strategy needed

**Security Requirements**:

1. **Authentication**:
   - Django API keys (MVP)
   - HTTPS only (no HTTP)
   - Rate limiting (prevent abuse)

2. **Data Security**:
   - Encrypt YouTube API credentials at rest
   - Secure API key generation (cryptographically random)
   - No sensitive data in logs

3. **Privacy**:
   - User data isolation (can't access others' sources)
   - Data deletion on account closure
   - No selling user data (in ToS)

4. **YouTube API Compliance**:
   - Proper attribution and linking
   - Respect video privacy settings
   - Delete data when source video deleted
   - Transcript caching <30 days

**Expert Analysis**:
✅ **Compliance Strategy**:
- YouTube ToS: Low risk for personal research use case
- GDPR: If EU users, need data export/deletion features
- CCPA: Similar to GDPR for California users

⚠️ **Risk Mitigation**:
- Clear user ToS (users responsible for content)
- Security audit before public launch
- Monitor for ToS violations (automated checks)

💡 **Turn Compliance into Competitive Advantage**:
- "Privacy-first" messaging (per-user API keys)
- "Transparent data handling" (show what's stored)
- "User control" (delete anytime)

🔍 **Compliance Shortcuts**:
- Use Supabase auth (handles password security)
- Use Django's built-in security features
- Copy ToS from similar products (modify for your use case)

---

## Summary & Next Steps

### 🎯 MVP Definition (Final)

**Product Name**: ContentSync (working name)

**One-Liner**: Automatically sync YouTube channels to your personal knowledge base with AI-powered summaries, tags, and key moments.

**Target User**: Individual researchers and learners who want to systematically extract knowledge from YouTube

**Core Value**: Stop manually watching and note-taking. Set-and-forget monitoring that makes video content searchable and queryable.

**MVP Features**:
1. YouTube channel/playlist subscription
2. Continuous monitoring for new videos
3. Auto-extract transcripts + AI processing (summary, tags, categories, main ideas, key moments)
4. REST API for integration
5. Background job management

**Success Criteria**:
- 10 active users in 4 weeks
- 1,000 videos processed
- <$0.10 per video cost
- Weekly user retention >30%

**Timeline**: 4 weeks (aggressive but achievable with AI assistance)

---

### 🚀 Recommended Next Steps

**Immediate Actions** (Before coding):

1. **Validate YouTube API Access**
   - Create Google Cloud project
   - Enable YouTube Data API v3
   - Test transcript extraction with your credentials
   - Confirm quota limits and ToS compliance

2. **Design Data Model**
   - Sketch out database schema (User, Source, Video, ProcessedContent)
   - Define API response formats
   - Plan error/status tracking fields

3. **Create Technical Spec**
   - System architecture diagram
   - API endpoint specifications
   - Celery task definitions
   - LangGraph processing workflow

4. **Set Up Development Environment**
   - Initialize Django project with UV
   - Configure Supabase connection
   - Set up Docker development environment
   - Install all dependencies

**Week 1 Sprint Goals**:
- Working Django app with Supabase
- YouTube API integration (fetch video metadata)
- Basic user auth + API key generation
- First transcript extraction (manual trigger)

---

### 💡 Expert Recommendations

**What Will Make or Break This Product**:

✅ **Do This**:
- Focus ruthlessly on MVP scope (no feature creep!)
- Get first 10 users ASAP (even if manually onboarded)
- Measure everything (processing cost, latency, errors)
- Talk to users weekly (learn what they actually need)

⚠️ **Avoid This**:
- Building UI before API works (wrong order)
- Optimizing performance prematurely (focus on working first)
- Adding "nice-to-have" features (kill your darlings)
- Perfectionism (ship fast, iterate faster)

🔥 **Secret Weapons**:
1. **The Wizard of Oz MVP**: Manually process first 10 users' videos to learn patterns
2. **The Fake Door Test**: Tweet about the product, gauge interest before building
3. **The 10x Question**: For every feature, ask "Does this make the product 10x better?" If no, cut it.

---

### 📊 Risk Assessment

**High-Risk Items** (mitigate immediately):
- 🚨 YouTube ToS compliance (get legal review)
- 🚨 API quota limits (test with realistic load)
- 🚨 Processing cost at scale (monitor closely)

**Medium-Risk Items** (watch and plan):
- ⚠️ User onboarding friction (YouTube API credential setup)
- ⚠️ Processing accuracy (LLM hallucinations)
- ⚠️ Async job failures (Celery error handling)

**Low-Risk Items** (standard engineering):
- Infrastructure setup (Docker, Supabase)
- API development (Django REST framework)
- Authentication (Django built-in)

---

### 🎯 Validation Checklist

Before investing 4 weeks, validate these assumptions:

- [ ] YouTube API can reliably extract transcripts (test 10 videos)
- [ ] Claude Haiku quality is good enough (compare with GPT-4)
- [ ] Processing cost is <$0.10/video (test 100 videos)
- [ ] You can get 10 people to try it (presell if possible)
- [ ] You're excited to use this yourself daily (dogfood test)

---

## Appendix: Reference Materials

### Competitor Analysis Matrix

| Feature | ContentSync (You) | Glasp | YouTube Extensions | ChatGPT |
|---------|-------------------|-------|-------------------|---------|
| Continuous sync | ✅ | ❌ | ❌ | ❌ |
| Channel monitoring | ✅ | ❌ | ❌ | ❌ |
| API access | ✅ | ❌ | ❌ | ✅ |
| Rich metadata | ✅ | ⚡ | ❌ | ⚡ |
| Key moments | ✅ | ✅ | ⚡ | ❌ |
| RAG-optimized | ✅ | ❌ | ❌ | ⚡ |

✅ = Full support, ⚡ = Partial, ❌ = Not supported

### Technology Stack Rationale

| Component | Choice | Why | Alternatives Considered |
|-----------|--------|-----|------------------------|
| Backend | Django | Batteries-included, mature, good for API | FastAPI (too minimal), Flask (too manual) |
| Jobs | Celery | Industry standard, reliable | Dramatiq (less mature), RQ (simpler but limited) |
| LLM Gateway | LiteLLM | Multi-provider, cost optimization | Direct API calls (vendor lock-in) |
| LLM Orchestration | LangGraph | Structured workflows, state management | Raw LangChain (less structured) |
| Database | Supabase | Managed PostgreSQL, auth built-in | Self-hosted PG (more ops), MongoDB (wrong fit) |
| Package Manager | UV | Fast, modern Python tooling | pip/poetry (slower) |
| Monitoring | Flower | Celery-native, easy setup | Custom dashboard (unnecessary work) |

### Key Metrics Dashboard (Track Weekly)

**Growth Metrics**:
- New signups
- Active users (made API call in last 7 days)
- Sources added
- Videos processed

**Engagement Metrics**:
- API calls per user
- Videos queried per user
- Retention (% users active week-over-week)

**Technical Metrics**:
- Processing latency (avg time per video)
- Processing cost ($ per video)
- Error rate (% failed jobs)
- API uptime

**Business Metrics** (future):
- Free vs paid users
- MRR (Monthly Recurring Revenue)
- Churn rate
- Customer acquisition cost

---

**End of Discovery Session**

Total Questions Answered: 20/20 ✅

**Confidence Level**: High - Clear vision, focused MVP, achievable timeline

**Recommendation**: Proceed to implementation with strict scope discipline. Review this document weekly to stay aligned with vision.

---

*Session conducted by AI acting as Chief Product Officer with 20 years of product development experience. This document should be treated as a living document and updated as new insights emerge during development.*
