# 10 Prompts: MLX vs Claude Comparison

Use these 10 prompts to compare how MLX Omni Server (local) performs vs Claude (cloud) for Salesforce channel analytics.

**Setup:**
- Terminal 1: `mlx_omni_server` (MLX running locally)
- Terminal 2: `MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py` (MCP on corporate laptop)
- Terminal 3: `python mcp_client/chat.py` (Test MLX)
- Browser: [Claude.ai with MCP integration](https://claude.ai) (Test Claude)

---

## 1. Simple Data Query

**Prompt:**
```
What was our closed-won revenue this quarter?
```

**What to compare:**
- Does MLX correctly identify and call `get_revenue()` with `period="THIS_QUARTER"`?
- Does it include attainment % if available?
- Is the response concise and business-focused?

**Expected behavior:**
- MLX: Calls tool, returns formatted number
- Claude: Same, but may add more context/explanation

---

## 2. Multi-dimensional Breakdown

**Prompt:**
```
Show me revenue by country this quarter with the countries ranked by amount.
```

**What to compare:**
- Does MLX call `get_revenue(period="THIS_QUARTER", breakdown="country")`?
- Does it handle the ranking/sorting request?
- Is the output formatted as a table or list?

**Expected behavior:**
- MLX: Calls tool, may or may not sort (depends on model capability)
- Claude: Calls tool, definitely sorts and formats nicely

---

## 3. Tool Calling Decision

**Prompt:**
```
Who are our top 5 partners and how much pipeline do they have?
```

**What to compare:**
- Does MLX recognize this needs TWO tools: `get_top_partners()` and `get_partner_pipeline()`?
- Can it make sequential tool calls?
- Does it merge the results meaningfully?

**Expected behavior:**
- MLX: May only call one tool (limitation of smaller models)
- Claude: Calls both, synthesizes combined view

---

## 4. Trend Analysis

**Prompt:**
```
What is our growth rate from last quarter to this quarter?
```

**What to compare:**
- Does MLX call `get_growth()` with the right periods?
- Does it understand "growth rate" = percentage change?
- Does it explain the growth direction?

**Expected behavior:**
- MLX: Calls tool, returns raw % number
- Claude: Calls tool, interprets (up/down, healthy/concerning)

---

## 5. Risk Identification

**Prompt:**
```
Which deals are at risk of not closing?
```

**What to compare:**
- Does MLX recognize this maps to `get_high_risk_deals()`?
- Does it filter for realistic risk levels?
- Does it prioritize the highest-risk deals?

**Expected behavior:**
- MLX: Calls tool, lists deals with probabilities
- Claude: Calls tool, adds interpretation (e.g., "3 deals under 30% probability")

---

## 6. Partner Deep-Dive

**Prompt:**
```
Give me a full scorecard for Accenture this fiscal year.
```

**What to compare:**
- Does MLX call `get_partner_scorecard()` with the exact partner name?
- Does it understand "this fiscal year" vs "this quarter"?
- Does it present the scorecard in a readable format?

**Expected behavior:**
- MLX: Calls tool, returns structured data
- Claude: Calls tool, formats as actual scorecard (nicer presentation)

---

## 7. Conditional Logic

**Prompt:**
```
Which partners have over $5M pipeline but under 40% average deal probability?
```

**What to compare:**
- Does MLX recognize this needs filtering logic?
- Does it call the right tools to get the data?
- Can it apply the filters (pipeline > 5M AND probability < 40%)?

**Expected behavior:**
- MLX: May struggle with compound conditions
- Claude: Handles complex filters naturally

---

## 8. Forecast/Planning

**Prompt:**
```
Based on our pipeline velocity, when should we expect to hit $10M in closed deals?
```

**What to compare:**
- Does MLX attempt to call `get_pipeline()` + `get_stage_progression_velocity()`?
- Does it do calculation/extrapolation?
- Or does it just return the raw data?

**Expected behavior:**
- MLX: Returns data, minimal analysis
- Claude: Analyzes velocity, projects timeline, adds confidence

---

## 9. Anomaly Detection

**Prompt:**
```
What's unusual about our sales this quarter compared to last quarter?
```

**What to compare:**
- Does MLX fetch both quarters' data automatically?
- Does it identify outliers/unusual patterns?
- Or does it just compare numbers?

**Expected behavior:**
- MLX: Retrieves data, basic comparison
- Claude: Identifies specific anomalies, explains potential causes

---

## 10. Natural Language Intent (Ambiguous)

**Prompt:**
```
Tell me about Spain.
```

**What to compare:**
- Does MLX ask for clarification or assume a tool?
- Does it call `get_pipeline()` with `country="Spain"`?
- Does it handle ambiguity gracefully?

**Expected behavior:**
- MLX: May call wrong tool or ask for clarification
- Claude: Asks clarifying question (revenue, pipeline, partners?) or makes intelligent guess

---

## Scoring Rubric

For each prompt, rate on a 1-5 scale:

### Correctness (1-5)
- 5: Calls correct tool(s) with right parameters
- 4: Calls tool but missing optional params
- 3: Calls tool but wrong parameters
- 2: Calls wrong tool
- 1: No tool call

### Completeness (1-5)
- 5: Full answer to the question
- 4: Answer with minor missing context
- 3: Partial answer, some missing pieces
- 2: Very incomplete, needs follow-up
- 1: Doesn't answer at all

### Clarity (1-5)
- 5: Crystal clear, well-formatted, business-ready
- 4: Clear, minor formatting issues
- 3: Understandable, but could be clearer
- 2: Confusing, hard to extract insight
- 1: Incomprehensible

### Speed (1-5)
- 5: Sub-2 second response
- 4: 2-5 seconds
- 3: 5-10 seconds
- 2: 10-30 seconds
- 1: 30+ seconds

---

## Example Scoring

**Prompt 1: "What was our closed-won revenue this quarter?"**

| Criteria | MLX | Claude | Winner |
|----------|-----|--------|--------|
| Correctness | 5 | 5 | Tie ✓ |
| Completeness | 4 | 5 | Claude |
| Clarity | 4 | 5 | Claude |
| Speed | 5 | 3 | MLX ✓ |
| **Total** | **18/20** | **18/20** | **Tie** |

---

## Interpretation Guide

**Total Scores (add up all 4 rubric categories for each prompt):**

- **18-20 (90-100%)**: Excellent response, minimal difference
- **15-17 (75-85%)**: Good response, minor gaps
- **12-14 (60-74%)**: Acceptable, some limitations
- **<12 (<60%)**: Poor response, significant issues

**MLX Wins When:**
- Speed matters (local = instant)
- Simple, deterministic queries
- Tool calling is straightforward
- No complex synthesis needed

**Claude Wins When:**
- Complex multi-step reasoning
- Natural language ambiguity
- Formatted output/presentation
- Deeper analysis/interpretation

---

## How to Run Comparison

### Step 1: Test MLX
```bash
python mcp_client/chat.py
# Paste prompt 1
# Note response quality, time taken
```

### Step 2: Test Claude
- Go to [claude.ai/code](https://claude.ai/code)
- Use MCP integration with same Salesforce server
- Paste same prompt
- Compare response

### Step 3: Document Results

Create a simple table:

```markdown
| Prompt | MLX Score | Claude Score | Winner | Notes |
|--------|-----------|--------------|--------|-------|
| 1. Simple Data Query | 18/20 | 19/20 | Claude | MLX slightly slower synthesis |
| 2. Multi-dimensional | 17/20 | 20/20 | Claude | Claude sorted results |
| ... | ... | ... | ... | ... |
| **Total Average** | **X/20** | **Y/20** | **???** | **Summary** |
```

---

## Key Insights

After running all 10 prompts, you should be able to answer:

1. **When to use MLX:** _____ (e.g., "fast queries, simple reports")
2. **When to use Claude:** _____ (e.g., "complex analysis, presentations")
3. **MLX Strengths:** _____ (e.g., "speed, local privacy, no cloud")
4. **Claude Strengths:** _____ (e.g., "intelligence, multi-step reasoning")
5. **For channel directors, which is better?** _____ (e.g., "Claude for now, MLX for automation")

---

## Next Steps

After comparison:
1. Share results with IT/security team
2. Use for demo to other channel directors
3. Plan production migration path (e.g., "Start with Claude, optimize with MLX")
4. Document which use cases fit which model
