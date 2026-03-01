# FutureProof User Research: Who to Build For and How to Reach Them

## Context

Research to identify the most promising user segments for FutureProof as a product, based on: market landscape, user pain points, audience size, distribution channels, and monetization models.

---

## The Market Gap FutureProof Fills

The career tool market ($30B) is saturated with **resume template fillers** ($8-49/mo) that produce generic, homogenized output. No competitor does:
- Automated multi-source data gathering (LinkedIn + GitHub + portfolio + assessments)
- RAG-powered career analysis over actual professional data
- Strategic career intelligence (not just document formatting)
- Conversational interface with episodic memory across sessions
- Financial analysis (salary PPP, market rates) combined with career data

The "career intelligence" space — strategic analysis, not document generation — is essentially empty.

---

## Target User Segments (Ranked by Fit)

### Tier 1: Best Fit (high pain, strong product-market match)

#### 1. Scientists/PhDs Transitioning to Industry
- **Size**: Thousands annually (US alone produces ~55K PhDs/year, majority leave academia)
- **Pain**: Widest gap between actual capability and ability to communicate it. Academic CVs are illegible to industry. One PhD reported 1,000+ applications, ~2% response rate.
- **Why FutureProof fits**: Multi-source data (GitHub repos + publications + portfolio) → unified career profile → industry-translated CV. The "skills translation" analysis (Bayesian inference pipeline → ML engineering) is exactly what the orchestrator's analysis workflows do.
- **Where they are**: r/LeavingAcademia, r/datascience, r/PhD, Cheeky Scientist community, Nature Careers, SciPy/PyCon conferences
- **Willingness to pay**: High. Cheeky Scientist charges $2K+ for career transition coaching. These users are accustomed to paying for career help.

#### 2. Open Source Contributors
- **Size**: 1.5-3M developers with substantial public GitHub profiles globally. 60% unpaid, 44% burned out.
- **Pain**: Career invisibility — years of visible OSS work often ignored by hiring managers. Success (more users) = punishment (more demands, no pay). Can't translate contributions into career leverage.
- **Why FutureProof fits**: GitHub/GitLab live integration is a core feature. FutureProof can quantify and narrativize their contributions. "Your 847 commits to kubernetes show distributed systems expertise worth $X in market Y."
- **Where they are**: Hacker News, r/opensource, r/programming, OpenSauced community, Sustain OSS, FOSDEM, All Things Open
- **Willingness to pay**: Moderate. Many are frugal/OSS-minded. But the pain is acute enough that $15-25/mo is viable, especially if positioned as "finally get paid what your code is worth."

### Tier 2: Large Audience, Strong Pain

#### 3. Non-US Developers
- **Size**: India alone has 20M+ GitHub developers (+30% growth). Eastern Europe, Latin America, Southeast Asia are massive.
- **Pain**: Market value opacity. A developer in Argentina making $30-45K has identical skills to someone earning $120K+ in SF. No tools help them understand or negotiate their true value. 56% of Indian devs and 41% of Chinese devs find the job market challenging.
- **Why FutureProof fits**: Already has salary PPP comparison and market rate analysis. The financial analysis tools are a direct answer to "what am I actually worth?"
- **Where they are**: r/developersIndia, r/cscareerquestionsEU, We Work Remotely, RemoteOK, Toptal/Turing/Arc.dev communities
- **Willingness to pay**: Price-sensitive. PPP-adjusted pricing essential. $5-10/mo in emerging markets, $15-25/mo in Western markets.

#### 4. Mid-Career Developers (The "Complacent 75%")
- **Size**: Massive. 75% of developers are either "complacent" or "not happy" at work (Stack Overflow 2025, 49K respondents). Only 24% are happy.
- **Pain**: Employed but stuck. Can't articulate impact for promotions. Worried about mobility in a tight market (job listings down 35% from 2020). Know they should prepare but don't know how.
- **Why FutureProof fits**: The always-on career analysis — not just when job hunting. "What does your GitHub activity + LinkedIn + portfolio say about where your career is heading?" Episodic memory tracks decisions over time.
- **Where they are**: r/ExperiencedDevs (321K members), Blind, Levels.fyi, Hacker News
- **Willingness to pay**: Moderate-high. Employed developers have disposable income. $20/mo is trivial compared to the cost of a bad career move.

### Tier 3: Addressable but Harder

#### 5. Freelancers/Contractors
- **Pain**: Constant self-marketing burden, feast-or-famine cycle, platform economics degradation (Upwork connect costs real money now)
- **Why FutureProof fits**: CV generation for every new pitch, market rate analysis, portfolio synthesis
- **Challenge**: Fragmented, price-sensitive, many competing tools

#### 6. Career Changers Into Tech
- **Pain**: Credential anxiety, experience paradox, portfolio catch-22
- **Why FutureProof fits**: Can help build narrative from non-traditional backgrounds
- **Challenge**: Low GitHub/portfolio data to work with initially. The product needs data to be useful.

#### 7. New Grads / Entry-Level
- **Pain**: Resume black hole (100-200+ apps before an offer), new grad hiring down 25%
- **Challenge**: Least data to work with, most price-sensitive, highest churn

---

## Competitive Landscape

| Category | Top Players | Price Range | FutureProof Advantage |
|----------|------------|-------------|----------------------|
| AI Resume Builders | Rezi, Teal, Kickresume | $8-49/mo | They fill templates; FP does intelligence |
| Career Platforms | Careerflow, Jobright | Free-$29/mo | They track jobs; FP analyzes careers |
| Salary Data | Levels.fyi, Payscale | Free/enterprise | FP combines salary with personal career data |
| Portfolio Generators | github-readme-stats (78K stars), Reactive Resume (27K stars) | Free/OSS | FP goes beyond display to analysis |
| Career Coaching | Cheeky Scientist, CoachHub | $2K+/enterprise | FP automates what coaches do manually |

**Key insight**: Nobody connects GitHub data + LinkedIn data + portfolio + assessments + market data into a single career intelligence system. Every competitor does one piece.

---

## Go-to-Market Strategy

### Distribution (ranked by effectiveness for dev CLI tools)

1. **GitHub** — open-source the CLI, earn stars, build contributor community. GPT-Engineer: 50K stars → 300K advocates at commercial launch.
2. **Hacker News** — "Show HN" post. HN generates 3-4x more installs than Product Hunt for dev tools.
3. **Twitter/X** — build-in-public threads, demo videos. "I ran `futureproof chat` and asked what my GitHub says about my career" is a viral-ready demo.
4. **Reddit** — r/ExperiencedDevs, r/datascience, r/LeavingAcademia, r/developersIndia. Authentic engagement, not promotion.
5. **Conference talks** — PyCon, SciPy, All Things Open. Scientists love CLI tools; the demo writes itself.
6. **Dev.to / Hashnode** — tutorial content showing real use cases.

### Monetization Model

See product-direction.md for the full model.

**Summary**: FutureProof is free, local-first. The only paid service is an optional LLM proxy (the Zed/Warp pattern). New users get free starter tokens so they can start immediately without configuring an API key. After free tokens: pay-as-you-go at API cost + ~10% markup, or switch to BYOK (bring your own API keys) or Ollama (local, free). All features are free — only LLM compute is monetized.

### What to Avoid
- Don't position as "AI resume builder" — saturated, commoditized, associated with dark-pattern billing
- Don't use unpredictable credit-based pricing (Cursor's mistake caused mass backlash)
- Don't anchor to $0 permanently — makes later enterprise pricing "complex, costly, and disruptive"
- Don't go B2B first — developer tools are a retail market first

---

## Key Data Points

| Metric | Value | Source |
|--------|-------|--------|
| GitHub total users | 180M+ | Octoverse 2025 |
| Developers unhappy at work | 75% | Stack Overflow 2025 |
| Job listings down from 2020 | 35% | Indeed/MEV |
| AI resume demand growth YoY | 10,900% | Industry reports |
| OSS maintainers unpaid | 60% | ByteIota |
| Median time to first offer | 68.5 days | State of Job Search 2025 |
| Career tool premium conversion | 5-8% | Industry benchmarks |
| Career tool price point | $9-29/mo | Market analysis |
| HR Tech market (2025) | $43.66B | Fortune Business Insights |
| Career development market | $30B | Industry reports |

---

## Recommended First Moves

1. **Pick one Tier 1 segment** (Scientists/PhDs or OSS contributors) as launch audience
2. **Add 1-2 gatherers** for that segment (Google Scholar/ORCID for scientists, or contribution analytics for OSS)
3. **Open-source the CLI** on GitHub with a compelling README demo
4. **Write a "Show HN" post** with a real career analysis example
5. **Build multi-provider LLM support** (OpenAI, Anthropic, Google, Ollama) so users aren't locked to Azure OpenAI
