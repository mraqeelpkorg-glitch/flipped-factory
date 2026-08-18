# FLIPPED FACTORY — MASTER PRODUCTION SOURCE OF TRUTH
## Permanent Operating Contract for the 12 AI Video Agents

**Document:** `FLIPPED_FACTORY_MASTER_PRODUCTION.md`  
**Version:** 1.0  
**Purpose:** Permanent source of truth for architecture, agent behavior, quality, rights, viral strategy, Instagram publishing, learning, testing, and production completion.  
**Primary publishing platform:** Instagram Reels  
**Project rule:** Read this document before implementing, modifying, reviewing, or redesigning any agent.

---

# 1. PROJECT MISSION

Flipped Factory is a production-grade AI content factory.

It contains 12 specialized content agents:

1. YouTube Clipper
2. Podcast Clipper
3. Blog to Video
4. Remix Flip
5. Dub Flip
6. Data to Video
7. Product Compilation
8. BTS to Educational
9. Trending Audio
10. Course Teaser
11. Live Highlights
12. Screenshot Tutorial

The objective is NOT to create 12 unrelated demo buttons.

The objective is to create one reliable production platform where specialized agents reuse the same shared infrastructure and produce high-quality Instagram Reels.

The permanent high-level flow is:

```text
SOURCE
↓
VALIDATE
↓
RIGHTS / LICENSE
↓
RESEARCH / EXTRACTION
↓
AI ANALYSIS
↓
CONTENT STRATEGY
↓
HOOK
↓
SCRIPT / EDIT PLAN
↓
VIDEO GENERATION
↓
CAPTIONS
↓
BRANDING
↓
QUALITY ASSURANCE
↓
SAFETY
↓
DUPLICATE CHECK
↓
APPROVAL
↓
PUBLISH QUEUE
↓
INSTAGRAM REELS
↓
POST ID
↓
ANALYTICS
↓
LEARNING
```

---

# 2. SOURCE-OF-TRUTH RULE

This document is the permanent operating contract.

Every Manager, specialist agent, coder, tester, reviewer, and content agent must read it before making meaningful changes.

The project must NOT repeatedly restart from orientation.

The project must NOT repeatedly invent a new strategy every session.

The project must NOT rebuild existing infrastructure merely because a new agent needs it.

If an existing shared engine already performs a function, extend and reuse it.

If this document conflicts with an old agent instruction, this document wins unless the user explicitly changes the source of truth.

---

# 3. EXISTING PROJECT FIRST

Before implementing anything, inspect the real project.

Required inspection:

- README
- requirements files
- dashboard
- database/schema
- shared engines
- shared tools
- existing agent implementations
- rendering pipeline
- transcription pipeline
- caption system
- trend system
- analytics
- Instagram publisher
- authentication/credential handling
- tests
- project knowledge
- previous production lessons

Do not assume a component is missing until the repository has been inspected.

Do not create duplicate implementations.

---

# 4. PRIMARY BUSINESS DIRECTION — INSTAGRAM

Instagram Reels is the primary publishing destination.

Every agent must ultimately be capable of producing content suitable for Instagram.

The system should optimize for:

- retention
- watch time
- completion
- rewatches
- shares
- saves
- comments
- follows
- profile visits
- audience relevance
- consistency
- content quality

Views alone are NOT the only success metric.

The system must learn from actual performance.

---

# 5. DAILY VIRAL STRATEGY — PERMANENT RESPONSIBILITY

## THIS IS A CORE DAILY JOB OF THE SYSTEM

The viral/content strategy must NOT remain frozen.

Every day, the system should evaluate current evidence and update the content direction.

The responsible agent/manager must determine the daily direction.

Do NOT require the user to decide every day:

- which hook style to use
- which topic angle to use
- which format to prioritize
- which content length to use
- which niche angle is strongest
- which trend is relevant
- which visual treatment is performing
- which CTA style to test

The system is expected to make these decisions using current evidence.

## Daily strategy inputs

The daily strategy may consider:

- recent Instagram performance
- historical project analytics
- hook performance
- completion rate
- watch time
- saves
- shares
- comments
- follows
- current relevant trends
- current audience behavior
- niche performance
- content saturation
- recent successful formats
- recent failed formats
- seasonal/contextual opportunities
- official platform changes
- available source material

## Daily strategy output

Store a daily strategy record containing:

```text
strategy_date
target_niches
priority_topics
priority_formats
priority_hook_patterns
recommended_clip_lengths
caption_style
visual_style
CTA_style
trend_opportunities
things_to_avoid
reasoning/evidence
confidence
sources
created_at
```

## Important

The system may change direction daily.

But it must NOT randomly change direction without evidence.

A strategy change should have a reason such as:

- a format is outperforming
- a hook family has better retention
- a niche is declining
- a trend has emerged
- audience behavior changed
- a previous experiment failed

## No single-post overreaction

One viral post must not permanently redefine the system.

Use accumulated evidence.

---

# 6. VIRAL HOOK ENGINE — DAILY AND CONTINUOUSLY IMPROVED

Viral hooks are a first-class system capability.

The system must continuously test and improve hooks.

## Hook objective

Create a strong first 1–3 seconds that creates a legitimate reason to continue watching.

## Preferred hook families

The system may test:

### Curiosity

- "Most people don't know this..."
- "Here's what nobody tells you..."
- "The surprising part is..."

### Mistake

- "You're probably doing this wrong..."
- "This is the mistake almost everyone makes..."

### Contradiction

- "Everyone says X. Here's why that's incomplete..."

### Strong insight

- "The biggest lesson from this is..."

### Story

- "This started with one simple mistake..."

### Before/after

- "Before you do X, see what happens..."

### Question

- "Would you do this if you knew the result?"

### Specific value

- "Three things you should know before..."

These are patterns, not fixed scripts.

## Hook truthfulness

A hook must accurately represent the content.

Never fabricate:

- facts
- statistics
- quotes
- credentials
- testimonials
- outcomes
- controversy
- expert claims

Do not use deceptive clickbait.

## Hook scoring

Candidate hooks should be scored using evidence such as:

```text
clarity
curiosity
content_match
emotional_pull
specificity
retention_potential
novelty
audience_fit
```

The exact weights may evolve based on real performance.

## Hook learning loop

Every published clip should contribute:

```text
hook_type
hook_text
topic
niche
length
publish_time
watch_time
completion
shares
saves
comments
follows
```

The system should identify:

- winning hook patterns
- weak hook patterns
- niche-specific winners
- length-specific winners
- audience-specific winners

## Daily hook update

At least once per day, the system should evaluate recent results and update:

```text
winning_hooks
losing_hooks
experiments
recommended_hooks
```

The user should NOT need to manually teach the system the same hook rules repeatedly.

---

# 7. TREND ENGINE

Trend research is dynamic.

A trend is only considered current if it has recent evidence.

Store:

```text
trend
source
observed_at
region
niche
confidence
expires_at
```

Never label stale data as current.

Trends are signals, not facts.

A trend should only be used when it fits:

- niche
- audience
- brand
- content
- available assets

Do not force an unrelated trend into content merely because it is popular.

---

# 8. NICHE STRATEGY

Supported niches are extensible.

Current project examples may include:

- Health
- Finance
- Technology
- E-Commerce
- Education
- Motivation
- Food
- Travel
- Beauty
- Productivity

Niche selection can consider:

- audience fit
- current demand
- historical performance
- monetization potential
- competition
- source availability
- trend freshness
- brand fit

High-stakes niches require additional factual and safety verification.

---

# 9. SHARED AGENT CONTRACT

Every agent must provide:

## Input

Structured and validated input.

## Processing

Observable stages.

## Output

Structured output.

## Job identity

Every run has:

```text
job_id
agent_type
created_at
started_at
finished_at
status
retry_count
error_code
error_message
```

## Persistent states

Use states such as:

```text
DRAFT
VALIDATING
ANALYZING
GENERATING
RENDERING
QA_PENDING
QA_FAILED
READY_FOR_REVIEW
APPROVED
SCHEDULED
PUBLISHING
PUBLISHED
FAILED
BLOCKED
HUMAN_REVIEW_REQUIRED
DUPLICATE
```

## Failure handling

Never silently fail.

Every failure must identify:

- stage
- error
- retryable/permanent
- next action

---

# 10. COPYRIGHT / RIGHTS MANAGEMENT

Copyright handling is a mandatory shared system responsibility.

## Valid source classes

Content can proceed when it is:

1. User-owned.
2. Properly licensed.
3. Explicitly authorized.
4. Public domain.
5. Used under a legitimate applicable legal exception.

## Important distinction

The following are separate:

```text
COPYRIGHT PERMISSION
PLATFORM POLICY
REUSED CONTENT POLICY
MONETIZATION ELIGIBILITY
```

Permission does not guarantee monetization.

A legal exception is not an automatic guarantee.

The system must never make a definitive legal conclusion where the facts are uncertain.

## Rights record

Store:

```text
rights_status
source_url
source_owner
license_type
permission_reference
commercial_use_allowed
attribution_required
rights_checked_at
```

If rights are unknown:

```text
RIGHTS_STATUS = UNKNOWN
PUBLISH = BLOCKED
```

## Never

- bypass DRM
- bypass access restrictions
- scrape private content
- fabricate permission
- fabricate licensing
- remove ownership marks to disguise source
- impersonate rights holders
- claim "fair use" as an automatic defense

---

# 11. ORIGINALITY / VALUE-ADDITION RULE

The platform should produce genuinely valuable content.

For third-party source material, favor:

- commentary
- education
- criticism
- analysis
- explanation
- new narrative
- meaningful editing
- substantive visual transformation
- original context

The following alone are NOT sufficient originality:

- cropping
- mirroring
- speed changes
- filters
- borders
- captions alone
- minor cuts

The system should avoid mass-producing near-identical content.

---

# 12. CONTENT SAFETY

Safety is a production gate.

Potentially risky content includes:

- hate
- harassment
- threats
- sexual content
- minor safety concerns
- graphic violence
- dangerous instructions
- scams/fraud
- illegal activity
- serious medical misinformation
- dangerous financial claims
- impersonation
- privacy violations

When confidence is low:

```text
HUMAN_REVIEW_REQUIRED
```

Do not auto-publish uncertain high-risk content.

---

# 13. HIGH-STAKES CONTENT

Health, finance, legal, safety, medication, and similar topics require stronger verification.

The system should:

- prefer authoritative sources
- preserve source references
- avoid unsupported claims
- distinguish facts from opinion
- avoid exaggerated outcomes
- escalate uncertainty

Never invent:

- medical claims
- dosage advice
- financial returns
- legal guarantees
- professional credentials

---

# 14. PRIVACY AND SECRET PROTECTION

Before publishing, detect/redact where appropriate:

- passwords
- API keys
- tokens
- cookies
- private email addresses
- private phone numbers
- private addresses
- private IDs
- financial information
- confidential business information

Never log secrets.

Never store platform passwords in ordinary database fields.

---

# 15. VIDEO STANDARD

Default Instagram output:

```text
9:16
1080x1920
MP4
H.264 or supported modern codec
AAC audio
23–60 FPS
```

Every render must be checked for:

- file integrity
- resolution
- aspect ratio
- codec
- audio
- duration
- captions
- safe zone
- black bars
- corrupted frames
- readability
- duplicate content

Failed media cannot enter publishing.

---

# 16. CAPTION ENGINE

Captions must reflect actual content.

Support:

- dynamic word highlighting
- sentence highlighting
- speaker-aware captions
- configurable font
- size
- position
- animation
- background/outline
- safe zones

Never change quotes merely to increase virality.

---

# 17. BRANDING

Branding must be configurable:

- brand name
- Instagram username
- logo
- watermark
- font
- caption style
- intro
- outro
- CTA

Do not hard-code branding into individual agents.

---

# 18. DUPLICATE PROTECTION

Track:

```text
source_id
source_hash
transcript_hash
audio_hash
video_hash
clip_start
clip_end
agent_type
```

The same source segment must not accidentally publish multiple times.

Intentional remixes must be explicitly identified as remixes.

---

# 19. INSTAGRAM PUBLISHING

Instagram is the primary publishing destination.

Prefer official supported Meta/Instagram APIs wherever available.

Publisher should support:

- account connection
- authentication state
- token state
- token expiry
- media creation
- media processing
- publish
- post/media ID
- publish timestamp
- error handling
- retry handling

Never bypass:

- password security
- passkeys
- 2FA
- CAPTCHA
- anti-bot systems
- platform security

Browser/CDP automation may support legitimate workflows but must never be used to bypass security controls.

---

# 20. APPROVAL

Default:

```text
AUTO_PUBLISH = OFF
```

Normal workflow:

```text
GENERATED
↓
QA PASSED
↓
RIGHTS PASSED
↓
SAFETY PASSED
↓
READY FOR REVIEW
↓
APPROVED
↓
QUEUED
↓
PUBLISHED
```

Auto-publishing may later be enabled, but mandatory safety, rights, QA and duplicate gates remain.

---

# 21. SCHEDULING

Support:

- publish now
- scheduled publishing

Timezone must be configurable.

Default timezone:

```text
Asia/Karachi
```

Do not hard-code the timezone throughout the application.

---

# 22. ANALYTICS

Every published item should store:

```text
agent
niche
topic
hook_type
hook
duration
template
caption_style
publish_time
views
watch_time
completion
replays
shares
saves
comments
follows
profile_visits
```

Use analytics to improve:

- hooks
- topics
- formats
- lengths
- captions
- publishing times
- visual styles
- niche selection

Do not overfit to one viral post.

---

# 23. DAILY STRATEGY DECISION ENGINE

The system must decide the daily content direction.

It may choose:

- what niche to emphasize
- what topics to emphasize
- what hook families to test
- what video lengths to prioritize
- what visual templates to prioritize
- what caption style to test
- what CTA style to test
- what trend opportunities to use
- what formats to reduce
- what content to avoid

The direction must be based on current evidence.

The user should not need to provide daily strategic instructions.

---

# 24. DAILY STRATEGY FILE

Persist a daily strategy artifact such as:

```text
daily_strategy/YYYY-MM-DD.json
```

Recommended fields:

```text
date
target_niches
priority_topics
priority_formats
priority_hooks
recommended_lengths
caption_style
visual_style
cta_style
trend_opportunities
avoid_list
evidence
confidence
sources
created_at
```

This prevents the system from repeatedly "starting over" every session.

---

# 25. DAILY HOOK LEARNING

Persist:

```text
hook_learning/
  winners
  losers
  experiments
  recommendations
```

Daily job:

1. read recent performance
2. compare hook families
3. identify winners
4. identify losers
5. create new experiments
6. update recommendations
7. record evidence

The system should evolve without requiring repeated manual training.

---

# 26. TWELVE AGENTS

## 26.1 YouTube Clipper

YouTube → Instagram Reels.

Pipeline:

```text
URL
→ validate
→ rights
→ download
→ transcribe
→ segment
→ score
→ select
→ render
→ captions
→ QA
→ approval
→ Instagram
```

Use shared downloader/transcriber.

Detect:

- strong statements
- useful lessons
- emotional moments
- surprising insights
- complete stories
- strong Q&A

Reject contextless fragments.

---

## 26.2 Podcast Clipper

Podcast → short clips.

Pipeline:

```text
PODCAST
→ transcript
→ speaker detection
→ topic segmentation
→ moment detection
→ scoring
→ context check
→ render
→ captions
→ QA
→ Instagram
```

Prioritize:

- stories
- opinions
- lessons
- memorable statements
- emotional moments
- humor
- surprising insights
- actionable advice

Support:

- speaker focus
- split screen
- dynamic speaker layouts

---

## 26.3 Blog to Video

Blog → video reel.

Extract:

- title
- headings
- key points
- facts
- images
- source links

Structure:

```text
HOOK
→ PROBLEM
→ KEY POINTS
→ TAKEAWAY
→ CTA
```

Store source URL.

Verify factual alignment.

---

## 26.4 Remix Flip

Authorized existing content → value-added new Reel.

Analyze:

- original hook
- beats
- pacing
- key message

Create meaningful new:

- hook
- context
- commentary
- structure
- visual treatment
- CTA

Crop/speed/filter-only edits are insufficient.

Store source/remix hashes.

---

## 26.5 Dub Flip

Authorized Reel → multilingual Reel.

Initial languages:

- English
- Spanish
- Hindi
- Arabic
- Portuguese

Preserve:

- meaning
- tone
- names
- numbers
- technical terms

Validate:

- translation
- pronunciation
- audio sync
- captions
- localized metadata

---

## 26.6 Data to Video

Research/data → infographic Reel.

Inputs:

- research topic
- CSV
- JSON
- spreadsheet
- authorized sources

Validate:

- values
- units
- dates
- percentages
- calculations

Never invent statistics.

Support:

- charts
- rankings
- comparisons
- timelines
- percentage cards

Store source information.

---

## 26.7 Product Compilation

Products → Top 5/10 showcase.

Verify:

- product
- brand
- price
- features
- pros
- cons
- rating where verified
- source
- date

Rank using transparent factors:

- value
- features
- quality
- use case
- price
- audience fit

Never invent product specifications.

Support appropriate affiliate disclosure.

---

## 26.8 BTS to Educational

Behind-the-scenes → tutorial.

Structure:

```text
HOOK
→ WHAT
→ HOW
→ WHY
→ LESSON
→ CTA
```

Use:

- labels
- arrows
- zooms
- numbered steps
- captions
- callouts

High-risk processes require human review.

---

## 26.9 Trending Audio

Current trend + relevant niche → Reel.

Track:

- source
- observed_at
- region
- niche
- confidence
- TTL

Never call stale data current.

Use platform-supported or appropriately licensed audio.

Never unlawfully redistribute copyrighted audio.

---

## 26.10 Course Teaser

Authorized course → educational teaser.

Structure:

```text
HOOK
→ PROBLEM
→ ONE REAL LESSON
→ RESULT
→ COURSE CTA
```

Do not expose unauthorized premium/private material.

Do not make unsupported income/result promises.

---

## 26.11 Live Highlights

Authorized livestream → best moments.

Detect:

- reactions
- questions
- answers
- funny moments
- announcements
- lessons
- unexpected events

Remove/review:

- dead air
- technical failures
- private conversations
- confidential information

Use timestamped candidate clips.

---

## 26.12 Screenshot Tutorial

Screenshots → step-by-step tutorial.

Structure:

```text
HOOK
→ STEP 1
→ STEP 2
→ STEP 3
→ RESULT
→ CTA
```

Add:

- zoom
- cursor
- highlights
- arrows
- step numbers
- captions

Detect/redact:

- passwords
- API keys
- tokens
- private data

For changing software interfaces record:

```text
source_url
checked_at
version
```

Do not claim current instructions without verification when the UI may have changed.

---

# 27. DASHBOARD CONTRACT

Every agent's dashboard view must expose:

- Run
- inputs
- progress
- current stage
- logs
- preview
- score
- QA
- rights
- safety
- approval
- schedule
- publishing status
- published ID
- errors/retries

A Run button is not proof of completion.

---

# 28. TESTING CONTRACT

Each agent requires tests for:

1. valid input
2. invalid input
3. source failure
4. rights failure
5. AI failure
6. render failure
7. QA failure
8. duplicate detection
9. safety escalation
10. approval
11. queue
12. publish failure/retry
13. successful completion

Use mocks/test sources for automated tests.

Never publish to the real Instagram account during automated tests unless explicitly authorized.

---

# 29. NO-REGRESSION RULE

Before changing shared infrastructure:

1. identify every agent using it
2. run relevant tests
3. make the smallest safe change
4. run regression tests
5. verify affected dashboard flows

Do not break one agent while fixing another.

---

# 30. CURRENT KNOWLEDGE RULE

For external platform/API/policy behavior:

Priority:

1. official platform documentation
2. official policy/help center
3. official API reference
4. official developer examples
5. project telemetry/tests
6. reputable technical documentation
7. community sources as supplemental evidence

When platform rules change:

```text
VERIFY CURRENT OFFICIAL DOCS
→ UPDATE KNOWLEDGE
→ UPDATE TESTS
→ UPDATE IMPLEMENTATION
→ RECORD DATE/SOURCE
```

Do not permanently encode old workarounds.

---

# 31. DAILY SELF-IMPROVEMENT

The agents are expected to improve their direction from evidence.

Every day, the system should be able to answer:

- What worked yesterday?
- What did not work?
- Which hooks won?
- Which hooks lost?
- Which niches performed?
- Which topics performed?
- Which lengths performed?
- Which visual templates performed?
- Which CTAs performed?
- Which publishing times performed?
- Which trends are relevant now?
- What should we test next?

The answer must become structured project knowledge.

Do not rely on conversation memory.

---

# 32. PRODUCTION MEMORY

Durable lessons must be stored in the project's knowledge system.

A lesson should include:

```text
lesson_id
date
problem
evidence
decision
result
confidence
affected_components
```

Do not store secrets or personal authentication data.

---

# 33. AGENT SPECIALIZATION RULE

Agents are specialized workers.

They may decide HOW to execute their assigned content type.

They must NOT violate the global contract.

Example:

Podcast Clipper decides:
- which podcast moments are strongest
- which clip length is best
- which layout is best

But it does not decide:
- whether to bypass copyright
- whether to bypass Instagram security
- whether QA can be skipped
- whether secrets can be published

Global safety/rights/platform rules always win.

---

# 34. MANAGER RESPONSIBILITY

When the user says:

"Complete Podcast Clipper"

Manager must:

1. read this document
2. inspect existing implementation
3. inspect shared infrastructure
4. identify gaps
5. delegate appropriate specialists
6. implement missing functionality
7. test
8. review
9. perform end-to-end verification
10. update durable project knowledge
11. continue until Definition of Done is met

Do not stop after diagnosis.

Do not return a "next session" checklist if internal work remains.

If an internal fix is possible, FIX → TEST → VERIFY → CONTINUE.

Only report a blocker when it is genuinely external or impossible to resolve legitimately.

---

# 35. DEFINITION OF DONE

An agent is DONE only when:

- implementation exists
- shared infrastructure is reused
- dashboard is integrated
- persistent state exists
- errors are handled
- retries are safe
- rights gate exists
- safety gate exists
- duplicate protection exists
- QA exists
- tests pass
- local/test end-to-end flow succeeds
- documentation is updated
- analytics are connected
- Instagram publishing path is connected or clearly verified
- no known internal gap remains

---

# 36. STOP CONDITION

Once an agent is genuinely complete:

STOP changing it.

Only reopen it for:

- real bug
- security issue
- platform-policy change
- requested feature
- evidence-based performance improvement

Do not redesign completed agents merely to create more work.

---

# 37. PROJECT COMPLETION

The entire project is complete only when all 12 agents satisfy the Definition of Done and share the production infrastructure.

Final architecture:

```text
                    FLIPPED FACTORY
                           │
                    ORCHESTRATOR
                           │
       ┌──────────┬────────┼────────┬──────────┐
       ▼          ▼        ▼        ▼          ▼
    YouTube    Podcast    Blog    Remix       Dub
       │          │        │        │          │
       └──────────┴────────┼────────┴──────────┘
                           │
                     SHARED ENGINES
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     Research             AI                Video
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                    Caption Engine
                           ▼
                        QA Gate
                           ▼
                    Rights + Safety
                           ▼
                    Approval Queue
                           ▼
                 Instagram Publisher
                           ▼
                       Analytics
                           ▼
                 Daily Learning Loop
```

---

# 38. FINAL PRINCIPLE

Flipped Factory is not a collection of 12 demos.

It is a production content system.

The agents are specialized workers.

The shared engines are the foundation.

The dashboard is the control plane.

Instagram is the primary publishing destination.

The daily strategy is automatically evidence-driven.

Viral hooks are continuously tested and updated.

Copyright and rights are mandatory gates.

Safety is mandatory.

Quality comes before volume.

The system should become more capable over time without requiring the user to repeat the same instructions every session.

**This document is the permanent source of truth.**
