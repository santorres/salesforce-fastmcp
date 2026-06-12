# Local LLM Reliability: Fixing Hallucination

## The Problem We Found

When testing Qwen 2.5-3B with the query:
```
"Show me revenue by country last quarter ranked by amount"
```

**MLX Output (hallucinated):**
- Spain: $200,000
- Italy: $100,000

**Real Salesforce Data (Claude got this):**
- Italy: €685,425 ✅
- Spain: €326,652 ✅

The numbers were completely fabricated. This is **unacceptable for financial data**.

---

## Why It Happened

1. **Too-small model** — Qwen 2.5-3B (3 billion parameters) struggles with:
   - Instruction following
   - Maintaining data integrity
   - Distinguishing real from invented data

2. **Silent MCP failure** — Tool calls failed but MLX continued synthesizing anyway

3. **No validation** — System didn't detect hallucination or refuse to answer

---

## Solution: Three-Layer Defense

### Layer 1: Error Detection (in chat.py)

```python
# Check if any tool returned an error
if errors:
    return "⚠️ Tool execution failed. Cannot provide accurate data."
    # Don't attempt synthesis if tools failed
```

**Effect:** Stops hallucination at the source — if tools fail, admit it rather than invent.

### Layer 2: System Prompt (in ollama_llm.py)

```
CRITICAL RULES:
1. NEVER invent or estimate numbers
2. Always use tool results EXACTLY
3. If no real data, say so
4. Always cite exact values
```

**Effect:** Instructs the model to use only real data and refuse synthesis without it.

### Layer 3: Synthesis Validation (in chat.py)

```python
synthesis_prompt = (
    f"Based on these REAL tool results from Salesforce:\n\n"
    f"{tool_results}\n\n"
    f"Answer using ONLY the data above. "
    f"Do NOT invent or estimate numbers."
)
```

**Effect:** Explicitly tells synthesis step to use tool results, not hallucinate.

---

## Model Selection for Reliability

### ❌ Too Small (Unreliable)
- Qwen 2.5-3B (hallucination risk: **CRITICAL**)
- Llama 3.2-1B
- Gemma-3-1B
- DeepSeek 1.5B

### ⚠️ Borderline (Better, but still risky)
- Qwen 2.5-7B (if available)
- Mistral-7B (better instruction following)

### ✅ Recommended (More Reliable)
- **Mistral-8x7B** (mixture of experts, better reasoning)
- **Llama 3.1-8B** or **3.2-11B** (strong instruction following)
- **Qwen-14B** (better than 7B, still fast)
- **OpenHermes-2.5** (trained for tool use)

### 🚀 Most Reliable (Production-Ready)
- **Llama 3.1-70B** (excellent, but slower/larger)
- Larger variants of Mistral, Qwen, or Llama

---

## Testing & Validation

### Step 1: Direct Tool Test

```bash
python debug_tool_execution.py
```

This shows:
- ✅ Can connect to MCP?
- ✅ What data is returned?
- ✅ Is it real Salesforce data?

If this fails, MCP server is the issue (not the LLM).

### Step 2: Model Tool Calling Test

```bash
python demo_mlx_tools.py
```

This shows:
- ✅ Does the model detect tools?
- ✅ Are parameters correct?
- ✅ Multiple tools in one query?

### Step 3: End-to-End Test

```bash
python mcp_client/chat.py

You: show me revenue by country last quarter ranked by amount

# Check:
# 1. Did it call get_revenue?
# 2. Did it use real Salesforce data?
# 3. Are the numbers correct? (cross-reference with Claude)
```

---

## How to Upgrade the Model

If Qwen 2.5-3B is hallucinating, try Mistral-7B:

### In MLX Omni Server terminal:
```bash
# Check available models
curl http://localhost:8000/v1/models | jq '.data[].id'

# If Mistral-7B is available, it's already downloaded
# If not, MLX will auto-download on first use
```

### In MCP Client:
```bash
export OLLAMA_MODEL=mistralai/Mistral-7B-Instruct-v0.3
python mcp_client/chat.py
```

Or edit `mcp_client/config.py`:
```python
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
```

Then test again:
```bash
python mcp_client/chat.py
You: show me revenue by country last quarter ranked by amount
```

---

## Recommended Model Tiers

### Tier 1: Quick Demos (Fast, Lower Reliability)
- **Qwen 2.5-3B** — hallucination risk, fast ⚠️
- **Mistral-7B** — better, good balance ✅

### Tier 2: Production (Reliable, Moderate Speed)
- **Llama 3.1-8B** — strong, recommended 🎯
- **Mistral-8x7B** — expert mixture, better reasoning ✅
- **OpenHermes-2.5** — trained for tools 🎯

### Tier 3: Gold Standard (Slow, Most Reliable)
- **Llama 3.1-70B** — excellent, but slower
- **Command-R+** — specialized for enterprise 🎯

---

## For Your Use Case

**Channel Director Analytics = Financial Data = High Accuracy Requirement**

### Minimum Acceptable:
- **Mistral-7B** or **Llama 3.1-8B**
- With the 3-layer validation above
- Tested against real Salesforce queries

### Recommended:
- **Llama 3.1-8B or 11B** on M1/M2/M3 Mac
- Better instruction following
- More reliable with complex queries
- Still runs locally (no compliance issues)

### If You Can't Get Reliability:
Consider hybrid approach:
- **MLX for:** Demos, exploration, non-critical queries
- **Claude (on corporate laptop via API):** Critical revenue/pipeline data

---

## Verification Checklist

Before deploying a model for real use:

- [ ] Run `debug_tool_execution.py` — MCP connection works
- [ ] Run `demo_mlx_tools.py` — Tool calling works
- [ ] Run all 10 prompts from PROMPT_COMPARISON.md
- [ ] Compare results against actual Salesforce data
- [ ] Check for hallucinations (made-up numbers)
- [ ] Verify rankings are correct (highest → lowest)
- [ ] Confirm deal counts match reality
- [ ] Test error handling (invalid period, missing country, etc.)

**Pass criteria:** ≥90% accuracy on all queries, zero hallucinations on numbers.

---

## Long-term Strategy

| Phase | LLM | Use | Timeline |
|-------|-----|-----|----------|
| **Now** | MLX 7B+ | Local testing, demos | Immediate |
| **Q2 2026** | MLX 8B+ | Automation, scheduled reports | After validation |
| **Q3 2026** | Claude (internal) | Critical decisions, channel director dashboards | When approved |
| **Q4 2026** | Bedrock/Glean | Production deployment | After security review |

---

## Support & Debugging

### "Model is hallucinating numbers"
1. Try a larger model (7B → 8B → 13B)
2. Check `debug_tool_execution.py` — is MCP returning correct data?
3. Enable VERBOSE mode: `export VERBOSE=true`
4. Check logs for what data was passed to synthesis

### "Tool not being called"
1. Check `demo_mlx_tools.py` — tool detection working?
2. Check model size — 3B models miss 20% of tool opportunities
3. Try different model (Mistral vs Qwen)

### "Numbers look right but ranking is wrong"
1. Model isn't reading data correctly
2. Try larger model or different model family
3. Check synthesis prompt is clear (updated code includes this)

### "Everything works but slow"
1. Larger models are slower (trade-off)
2. Check: is inference slow or MCP call slow?
3. `debug_tool_execution.py` helps measure MCP latency

---

## Next Steps

1. **Test Mistral-7B** with the validation code
2. **Run the 10-prompt comparison** with your chosen model
3. **Document accuracy baseline** for your territory
4. **Plan model upgrade path** (8B → 13B if needed)
5. **Share results with IT** for compliance approval

**Goal:** Local LLM that's as accurate as Claude for Salesforce queries, with zero hallucinations on financial data.
