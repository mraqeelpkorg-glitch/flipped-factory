# PRODUCT COMPILATION — SOURCE OF TRUTH
## Agent #7: Products → "Top 10" Showcase Video
**Document:** `agents/sources_of_truth/product_compilation_SOURCE_OF_TRUTH.md`
**Version:** 1.0
**Last Updated:** 2026-08-19
**Auto-Update:** Daily at 00:00 UTC
**Purpose:** Complete reference for Product Compilation agent.

---

# 1. WHAT IS PRODUCT COMPILATION?

Product Compilation takes a list of products and creates a **"Top N" showcase video** by:
1. Taking product list (name, benefit, price)
2. Generating script with product details
3. Creating TTS voiceover
4. Building video with product highlights
5. Merging audio + video

**Output:** Vertical product showcase video, ready for Instagram Reels.

---

# 2. WORKFLOW

```
PRODUCT LIST
    ↓
┌─────────────────────────────────────────┐
│ 1. INPUT VALIDATION                     │
│    - Products: list with ≥ 2 items?     │
│    - Each has name, benefit, price?     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. RIGHTS GATE                          │
│    - Verify product/brand/price         │
│    - Block if HIGH risk                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. SAFETY GATE                          │
│    - Check content                      │
│    - Block if violations                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. GENERATE SCRIPT                      │
│    - Product showcase script            │
│    - Hook + product highlights          │
│    - Duration: 30-60 seconds            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. TTS + VIDEO                          │
│    - Voiceover generation               │
│    - Video creation with products       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. MERGE + QA                           │
│    - Video + audio                      │
│    - Instagram compliance               │
└─────────────────────────────────────────┘
    ↓
OUTPUT: Product showcase video
```

---

# 3. PRODUCT FORMAT

```python
products = [
    {
        "name": "Vitamin D3 + K2",
        "benefit": "Immune boost & bone health",
        "price": "$15"
    },
    # ... more products
]
```

**Required Fields:** name, benefit, price
**Minimum:** 2 products
**Recommended:** 3-5 products

---

# 4. BEST PRACTICES

## Before Creation
1. **Verify Products** — Real names, prices
2. **Check Rights** — Brand usage allowed
3. **Niche Match** — Products match niche

## During Creation
1. **Clear Benefits** — Why buy this?
2. **Price Transparency** — Show prices
3. **Visual Appeal** — Clean layout

## After Creation
1. **QA Check** — All standards met
2. **Register Content** — For dedup

---

# 5. COMMON ISSUES

| Issue | Cause | Solution |
|-------|-------|----------|
| Too many products | Overwhelming | Limit to 3-5 |
| Unclear benefits | Vague text | Be specific |
| Price missing | Incomplete data | Always include price |

---

# 6. PERFORMANCE METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Creation time | < 60s | ~45s |
| QA pass rate | ≥ 95% | ~90% |

---

# 7. EXAMPLE USAGE

```bash
curl -X POST http://localhost:8003/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "product_compilation",
    "products": [
      {"name": "Vitamin D3", "benefit": "Immunity", "price": "$12"},
      {"name": "Omega-3", "benefit": "Brain health", "price": "$18"}
    ],
    "niche": "health_fitness"
  }'
```

---

**Last verified:** August 19, 2026
