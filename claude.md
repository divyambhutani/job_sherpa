# JobSherpa — Claude Code Context

## Project Overview
An ADK-based agentic AI application that takes a candidate's resume (PDF)
and a job description (text or URL), then returns a visually rich PDF report
containing match analysis, interview prep, and salary intelligence.

**App Name:** JobSherpa — your guide through the job hunt climb.

**One line use case:** "AI-powered resume-to-job matchmaker with real-time
interview and salary intel."

## Tech Stack
- Agent framework: Google ADK (google-adk)
- LLM: Gemini 2.5 Pro (gemini-2.5-pro) via Vertex AI
- URL finding: Serper API (serper.dev)
- Deep scraping: Scrapling (StealthyFetcher for anti-bot sites)
- PDF parsing: PyMuPDF (pymupdf)
- PDF generation: WeasyPrint (HTML+CSS → PDF)
- Charts: matplotlib (radar, donut, bar, speedometer)

## Architecture — Single Agent + Multiple Tools
One root ADK agent (Gemini) that orchestrates all tools.
NOT multi-agent — tools are Python functions, not sub-agents.

### Tools (in execution order)
1. parse_resume(tool_context) → dict
   - Reads PDF uploaded via ADK artifact system (ToolContext)
   - Extracts full text + all URLs/links found in resume
   - Library: PyMuPDF

2. validate_links(links_json) → str
   - HTTP status check on all links extracted from resume
   - LeetCode specific: checks problem count and difficulty distribution
   - Returns structured JSON with links + action_items
   - NOTE: Implemented in tools/link_validator.py but not currently
     wired into the agent tools list. Link validation output defaults
     to empty in the report for now.

3. fetch_jd(url) → str
   - Scrapes job description from a URL if provided
   - Library: Scrapling Fetcher

4. serper_search(query) → dict
   - Finds relevant URLs for interview data + salary data
   - Returns structured JSON with dates for freshness filtering
   - API: serper.dev

5. scrape_content(url) → str
   - Deep scrapes a URL and returns full page content
   - Uses StealthyFetcher for Glassdoor/AmbitionBox (anti-bot)
   - Uses DynamicFetcher for Levels.fyi (JS-rendered)
   - Uses regular Fetcher for Reddit/Medium and all other sites
   - Library: Scrapling

6. generate_pdf(report, tool_context) → dict
   - Generates the final visual PDF report
   - Saves as ADK artifact (renders as download button in UI)
   - Charts via matplotlib, layout via WeasyPrint

## Project Structure
```
job_sherpa/
├── job_sherpa_agent/             # ADK module root (name must match for adk web)
│   ├── __init__.py
│   ├── agent.py                  # ADK agent definition, tool wiring, system prompt
│   ├── assets/
│   │   ├── branding.md           # Branding instructions (fonts, colors, style)
│   │   └── README.md             # Instructions for updating brand assets
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── resume_parser.py      # PDF → text + link extraction (via ADK artifact)
│   │   ├── link_validator.py     # HTTP checks on all resume links (not wired yet)
│   │   ├── jd_fetcher.py         # URL → JD text
│   │   ├── serper_search.py      # query → URLs list
│   │   └── scraper.py            # URL → full content
│   ├── report/
│   │   ├── __init__.py
│   │   ├── chart_generator.py    # All matplotlib charts
│   │   ├── pdf_generator.py      # WeasyPrint HTML→PDF
│   │   └── templates/
│   │       └── report.html       # Jinja2 HTML template
│   ├── .env                      # Never commit this
│   └── requirements.txt
├── requirements.txt              # Root-level copy (used for pip install)
└── claude.md                     # This file
```

## Environment Variables
All secrets live in `job_sherpa_agent/.env` — never hardcode, never commit .env.

```
GOOGLE_API_KEY=
GOOGLE_CLOUD_PROJECT=
SERPER_API_KEY=
GOOGLE_GENAI_USE_VERTEXAI=TRUE
```

## Output — PDF Report Structure
Dark theme (#0f0f1a background), visual-first design.
Text used only where visuals cannot convey the information.

### Page 1 — Cover
- Dark full-page background
- Candidate name, role, company in large typography
- Circular speedometer dial showing overall match score (0-100)
- Color: red <50, yellow 50-75, green >75

### Page 2 — Match Analysis
- Radar/spider chart: 5 axes (core skills, experience, domain,
  tools/stack, soft skills) — two overlapping shapes: yours vs required
- Shining points card (strengths, achievements, ownership signals)
  shown BEFORE skill gaps — confidence-first design
- Skill pills: green=matched, red=missing, gold=bonus
- ATS score horizontal bar

### Page 3 — Interview Roadmap
- Horizontal visual timeline of all interview rounds
- Each node: round name, duration, difficulty color
- Per-round detail cards: what they evaluate, how to prepare, red flags

### Page 4 — Expected Questions
- Card grid layout grouped by type:
  Technical (blue), Behavioural (purple), Curveball (gold)
- Icon per card type

### Page 5 — Salary Intelligence
- Side-by-side salary range bars: India (INR) and Global (USD)
- Donut chart: CTC breakdown (fixed/variable/ESOP)
- Negotiation tips
- Only rendered if salary band data is available (not all N/A)

### Page 6 — Sources & Confidence
- Dot-based confidence ratings per section
- Source chips/badges listing all URLs used

## Color Palette
- Background:     #0f0f1a
- Cards:          #1a1a2e
- Accent Blue:    #4285F4
- Accent Green:   #34A853
- Accent Red:     #EA4335
- Accent Gold:    #FBBC05
- Text Primary:   #ffffff
- Text Secondary: #a0a0c0

## JSON Schema (intermediate — agent produces this, then PDF is generated)
```json
{
  "candidate_name": "",
  "target_company": "",
  "target_role": "",
  "detected_role_type": "",
  "generated_at": "",
  "match_analysis": {
    "overall_score": 0,
    "dimensions": {
      "core_technical_skills":  { "score": 0, "reasoning": "" },
      "years_of_experience":    { "score": 0, "reasoning": "" },
      "domain_knowledge":       { "score": 0, "reasoning": "" },
      "tools_and_stack":        { "score": 0, "reasoning": "" },
      "soft_skills_leadership": { "score": 0, "reasoning": "" }
    },
    "skills": {
      "must_have":    { "matched": [], "missing": [] },
      "nice_to_have": { "matched": [], "missing": [] },
      "bonus_skills": []
    },
    "ats_analysis": {
      "ats_score": 0,
      "matched_keywords": [],
      "missing_keywords": [],
      "format_warnings": []
    },
    "experience_fit": {
      "verdict": "underqualified | good_fit | overqualified",
      "reasoning": ""
    },
    "shining_points": {
      "ownership_signals": [],
      "quantified_achievements": [],
      "competitions_hackathons": [],
      "open_source": [],
      "side_projects": [],
      "jd_resonance": [],
      "hidden_gems": []
    },
    "jd_flags": {
      "is_kitchen_sink_jd": false,
      "contradictions_found": [],
      "vague_requirements": []
    }
  },
  "link_validation": {
    "links": [],
    "action_items": []
  },
  "interview_process": {
    "rounds": [
      {
        "round_number": 0,
        "name": "",
        "format": "",
        "duration": "",
        "difficulty": "easy | medium | hard | very_hard",
        "what_they_evaluate": "",
        "how_to_prepare": "",
        "red_flags_to_avoid": "",
        "questions": {
          "technical": [],
          "behavioural": [],
          "curveball": []
        }
      }
    ],
    "total_rounds": 0,
    "typical_timeline": "",
    "confidence": "LOW | FAIR | HIGH",
    "source_urls": [],
    "data_freshness": ""
  },
  "salary_intelligence": {
    "india": {
      "source": "",
      "data_freshness": "",
      "confidence": "",
      "band": { "min": "", "median": "", "max": "" },
      "ctc_breakdown": { "fixed": "", "variable": "", "esops_rsus": "" },
      "joining_bonus": "",
      "negotiability": "",
      "candidate_estimate": ""
    },
    "global": {
      "source": "",
      "data_freshness": "",
      "confidence": "",
      "band": { "min": "", "median": "", "max": "" }
    },
    "negotiation_tips": []
  }
}
```

## JD Skill Classification Intelligence

JDs use inconsistent language to express skill priority.
The agent must detect intent, not just keywords.

### Must-Have Signal Words (hard requirements — penalise if missing)
- "required", "must have", "must-have", "you must"
- "essential", "mandatory", "minimum requirement"
- "X+ years of experience in", "proficiency in"
- "strong experience with", "expertise in"

### Nice-to-Have Signal Words (soft requirements — lenient scoring)
- "preferred", "nice to have", "good to have"
- "bonus", "plus", "advantage", "desirable"
- "ideally", "familiarity with", "exposure to"
- "experience with X is a plus"

### Growth / Learning Signal Words (zero penalty — flag as opportunity)
- "excited to learn", "eager to learn", "willingness to learn"
- "interest in", "curiosity about", "open to"
- "we will teach", "training provided"
- "you don't need to know X but..."

### Scoring Rules
- Missing a Must-Have skill     → significant penalty on match score
- Missing a Nice-to-Have skill  → minor penalty, flagged as "bridgeable gap"
- Missing a Growth signal skill → zero penalty, shown as "🌱 Learning Opportunity"
- Candidate has unrequested Nice-to-Have → flag as talking point in interview

## JD Edge Cases & Leniency Rules

### 1. Umbrella / Vague Phrases — ignore for scoring
Examples: "Strong CS fundamentals", "Experience with cloud platforms"
Rule: Too vague to score meaningfully. Don't penalise unless resume
shows zero technical depth whatsoever.

### 2. Years of Experience — apply ±1 year leniency buffer
- "3-5 years" → candidate has 2.5 years = "slightly below", not disqualified
- "5+ years"  → candidate has 4 years   = "slightly below", not disqualified
Rule: Quality of experience > raw years. Never hard-fail on years alone.

### 3. Synonymous / Equivalent Skills — full or partial credit
```
JD says        → Candidate has      → Credit
────────────────────────────────────────────
"ML"           → "Machine Learning" → 100%
"k8s"          → "Kubernetes"       → 100%
"Postgres"     → "PostgreSQL"       → 100%
"GCP"          → "Google Cloud"     → 100%
"CI/CD"        → "Jenkins+GitHub"   → 100%
"REST APIs"    → "RESTful services" → 100%
"Airflow"      → "Prefect"          →  60%
"AWS Lambda"   → "Serverless"       →  70%
"Agile"        → "Scrum"            → 100%
```

### 4. Version Specificity — 80% credit for same tool, different version
- "Python 3.8+" → candidate knows Python (unspecified) = 80% credit
- "React 18"    → candidate knows React (older)        = 80% credit
Rule: Version upgrades are learnable. Underlying skill is what matters.

### 5. Degree with Escape Clauses — never penalise if experience compensates
- "Bachelor's degree in CS or equivalent experience"
- "MS preferred but not required"
Rule: "Or equivalent experience" = degree not mandatory.
Flag as a note, never as a gap.

### 6. Role Title Inflation / Deflation — evaluate responsibilities, not title
- "Senior Engineer" at 10-person startup ≠ "Senior Engineer" at Google
- "Lead" with no management mentioned = likely individual contributor
Rule: Cross-reference title with company size and responsibilities listed.

### 7. Kitchen Sink JDs — detect and flag
If JD asks for 5+ completely different domains (backend + data + ML +
DevOps + frontend), flag: "This JD has a very wide scope. Focus on
skills listed first or mentioned most frequently."

### 8. Contradictory Requirements — flag and apply leniency
- "Entry level — 5 years experience required"
- "Junior role — must have led a team"
Flag: "Contradicting requirements detected — company may have
flexibility in their actual hiring bar."

### 9. Internal / Niche Tool Requirements — zero penalty
- Company-internal tools = zero penalty, learnable on the job
- Niche tools (Bloomberg, SAP) = soft requirement only

### 10. Soft Skills as Requirements — ignore for scoring
- "Excellent communication", "Team player", "Self-starter"
Rule: Universal filler. Route to behavioural interview prep only.

### 11. Location / Timezone Requirements — do not factor into score
Flag separately as a logistics note.

### 12. Security / Compliance Requirements — flag as hard blocker if relevant
- "Must have active security clearance"
- "Must be eligible to work in the US"
Rule: Non-negotiable unlike skill gaps. Flag prominently.

### 13. College / University Tier Requirements — flag clearly, never penalise score
Some companies (especially FAANG, top Indian product companies) explicitly
or implicitly prefer candidates from Tier 1 institutions.

Tier 1 India (most selective):
- IITs (all campuses), IISc, IIITs (Hyderabad, Bangalore, Allahabad)
- NITs (top campuses: Trichy, Warangal, Surathkal, Calicut)
- BITS Pilani (all campuses)
- Top private: IIIT-H, DA-IICT, VIT (selective programs)

Detection — flag if JD contains:
- "Tier 1 college", "Premier institution", "Top university"
- "IIT/NIT preferred", "From a reputed institution"
- Implicitly: very high bar roles at selective companies

Rules:
- NEVER reduce match score for college tier — skills matter more
- If candidate is from Tier 1 → highlight as shining point
- If candidate is NOT from Tier 1 but JD signals preference:
  → Flag as: "⚠️ This company shows preference for Tier 1 institutions.
    Your skills and projects will need to compensate — emphasise
    achievements, GitHub, and any competitive programming results."
- If candidate has strong compensating signals (FAANG internship,
  open source, hackathon wins) → flag those as overrides

## Shining Points Detection

Show BEFORE skill gaps in the PDF — confidence-first design philosophy.

### 1. Ownership & Leadership Signals
- "Built X from scratch", "Architected", "Designed and implemented"
- "Led the development of", "Single-handedly"
- "Founded", "Co-founded", "Introduced X to the team"
- "Migrated legacy system", "Reduced X by Y%", "Increased X by Y%"

### 2. Quantified Achievements — spotlight any number attached to impact
- "Reduced latency by 40%", "Served 10M+ users"
- "Saved $200K in costs", "Shipped product in 3 months"
Rule: Any metric = highlight loudly. These are what interviewers remember.

### 3. Competitions & Hackathons
- Won / finalist at any hackathon
- Smart India Hackathon, HackMIT, Google Summer of Code
- Kaggle top X%, ACM ICPC, LeetCode contest rating
Signal: Drive and performance under pressure. Especially valuable
for early-career candidates.

### 4. Open Source Contributions
- Contributed to / maintained open source projects
- GitHub stars, forks on personal packages
- Core contributor to known libraries
Signal: Public peer-reviewed code. Often stronger than job experience.

### 5. Side Projects & Indie Products
- Built and launched app with real users
- ProductHunt featured, App Store / Play Store published
- Any mention of revenue or active users
Signal: Initiative, product sense, end-to-end ownership.

### 6. Early Career Accelerators
- Internship at top-tier company
- Research publication or paper
- Teaching assistant, mentor, conference speaker
- Technical blog, patent, scholarship, rank topper

### 7. Cross-functional Exposure
- Worked with PMs, designers, C-suite
- Presented to stakeholders
- Onboarded and mentored junior engineers
Signal: Maturity beyond pure technical skill.

### 8. JD-Specific Resonance — match shining points to JD priorities
```
JD: "Small team — everyone owns their stack"
Resume: "Solo developer — built full product"
→ "🌟 Strong fit: Solo ownership matches their small team culture"

JD: "Performance at scale"
Resume: "Pipeline handling 500M records/day"
→ "🌟 Strong fit: Scale experience exceeds role requirements"
```

### 9. Hidden Gem Detection — catch candidates who undersell
```
Says "Helped with data pipeline" BUT "Team of 1 on data team"
→ They owned it entirely
→ Flag: "Reframe this as ownership, not assistance"

Says "Worked on ML models" BUT stack shows PyTorch + MLflow
→ Flag: "Stack suggests deeper ML expertise than description conveys"
```

### 10. Culture Fit Signals
```
Startup JD    + side projects, solo builds        = 🌟 strong fit
FAANG JD      + competitive programming, papers   = 🌟 strong fit
Product co JD + metrics-driven, A/B testing       = 🌟 strong fit
Research JD   + papers, novel implementations     = 🌟 strong fit
```

## Candidate Profile Link Validation

Extract and validate all external links found in the resume.
Note: `validate_links` tool is implemented but not currently wired into the
agent. Link validation section in the PDF report will be empty until wired.

### Links to Extract & Validate
- GitHub profile:       github.com/username
- GitHub repositories:  github.com/username/repo
- LinkedIn profile:     linkedin.com/in/username
- LeetCode profile:     leetcode.com/username
- Codeforces profile:   codeforces.com/profile/username
- CodeChef profile:     codechef.com/users/username
- HackerRank profile:   hackerrank.com/username
- Kaggle profile:       kaggle.com/username
- Portfolio website:    any personal domain
- Project live links:   deployed apps, demos
- Devpost:              devpost.com/username
- Any other URL found in the resume

### Validation Rules

#### All Platforms — HTTP status check
- 200 OK    → ✅ Live and accessible
- 403/404   → ❌ Dead or private — flag as urgent fix
- Timeout   → ⚠️ Possibly down or rate-limited

#### GitHub & LinkedIn & All Other Platforms
- Is the profile/repo publicly accessible?
  → Private or restricted = ❌ recruiter cannot verify, flag it

#### LeetCode Specific
- Total problems solved < 100       → ⚠️ flag as low activity
- Zero medium or hard problems      → ⚠️ flag
  Action: "Remove LeetCode from resume or improve before applying"

### Scoring Impact
- Dead link on resume     → -5 impression score, URGENT flag
- Private repo mentioned  → -3, flag as fix
- LeetCode too easy/low  → -2, flag as note or suggest removing
- All links healthy       → +5 bonus impression score

## Data Sources (searched at runtime)

### Primary Sources (scraped directly via Serper + Scrapling)
- Interview experiences: Glassdoor, Reddit, Medium, Leetcode Discuss
- Salary India:          AmbitionBox, Glassdoor India, Indeed India,
                         Naukri.com, LinkedIn Salary, Leetcode Compensation
- Salary Global:         Levels.fyi, Glassdoor
- Company intel:         Company careers page, Crunchbase, LinkedIn

## Scraping Strategy
```
Phase 1 — Serper finds URLs (structured JSON with dates)
Phase 2 — Filter: drop anything older than 3 years from current date
Phase 3 — Scrapling scrapes top 8-10 URLs
           StealthyFetcher → Glassdoor, AmbitionBox (Cloudflare protected)
           Regular Fetcher → Reddit, Medium
           DynamicFetcher  → Levels.fyi if regular fails (JS-rendered)
Phase 4 — Gemini synthesizes all content → structured JSON
Phase 5 — generate_pdf converts JSON → visual PDF report
```

## Scraping Notes
- Glassdoor and AmbitionBox use Cloudflare — always use StealthyFetcher
- Reddit and Medium are open — use regular Fetcher (faster)
- Levels.fyi is JS-rendered — use DynamicFetcher if regular fails
- Leetcode Discuss is unreliable — treat as best-effort only
- Always filter scraped content older than 3 years before passing to Gemini

## Development Workflow
1. Run locally: `adk web` from the `job_sherpa/` root directory
2. Local URL: http://localhost:8000
3. Upload PDF resume via the ADK web UI chat
4. The agent reads the PDF via the ADK artifact system (ToolContext)

## Coding Conventions
- Python 3.10+
- Type hints on all functions
- Each tool in its own file under tools/
- Async functions where possible (ADK supports async tools)
- Never hardcode API keys — always use environment variables
- System prompt and task instructions live inline in agent.py
- Tool functions must return strings or dicts (ADK requirement)
- Handle scraping failures gracefully — log and continue, don't crash

## Key Decisions Made
- Single agent (not multi-agent) — tools don't need independent reasoning
- resume_parser uses ADK ToolContext artifact system — not raw bytes
- pdf_generator is a Tool not an Agent — deterministic, no LLM needed
- link_validator is a Tool not an Agent — deterministic HTTP checks
- validate_links implemented but not wired — agent populates link_validation
  as empty for now; can be wired when ready
- Scrapling chosen over Firecrawl — free, self-hosted, adaptive parsing
- Serper chosen for URL discovery — returns dates, enables freshness filtering
- WeasyPrint for PDF — HTML+CSS gives full design control
- Dark theme PDF — premium look, visually differentiated
- Shining points shown BEFORE skill gaps — confidence-first design
- No FastAPI / no Dockerfile — project runs via adk web only
- No google_search built-in — Serper + Scrapling covers all research needs
- System prompt inline in agent.py — no separate prompts.py needed
