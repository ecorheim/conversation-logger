# Common Rationalizations and Rebuttals

**Load this reference when:** Tempted to skip TDD, or when reviewing code that lacks tests.

**Role:** High-density correction signal for agents attempting to rationalize TDD shortcuts. Every excuse has been tried. Every excuse fails. This file documents why.

## Protocol: Detection

Every rationalization follows the same structure:
1. Acknowledges TDD rule → 2. Claims this situation is different → 3. Proposes a shortcut

**Self-check — If any is true, you're rationalizing:**
- Making an exception to the rule?
- Claiming this case is different?
- Promising to do something "later"?
- Defending code already written?

**Trigger phrases (STOP immediately):**
- "just this once" / "I'll add tests after"
- "already manually tested" / "it worked when I tried it"
- "keep as reference" / "adapt existing code"
- "too simple to break" / "tests are obvious"
- "this is different because..." / "TDD doesn't work for X"

**Reality:** The situation is never special. The shortcut never works. The Iron Law exists because shortcuts don't work.

## Reference: Core Misconceptions

**"I'll write tests after to verify it works"**
- **Flaw:** Tests-after bias — you test what you built, not what's required
- **Action:** Tests passing immediately proves nothing. Write test first, watch it fail.

**"I already manually tested all edge cases"**
- **Flaw:** Ephemeral verification — no record, can't re-run, forgotten under pressure
- **Action:** Convert manual verification into automated test immediately.

**"Deleting X hours of work is wasteful"**
- **Flaw:** Sunk cost fallacy — time is already gone, keeping unverified code is debt
- **Action:** Delete and rewrite with TDD. High confidence > low confidence + sunk hours.

**"TDD is dogmatic, being pragmatic means adapting"**
- **Flaw:** False dichotomy — TDD IS pragmatic (bugs before commit, not after)
- **Action:** "Pragmatic" shortcuts = debugging in production = slower.

**"Tests after achieve the same goals"**
- **Flaw:** Tests-first = "what should this do?" Tests-after = "what does this do?"
- **Action:** Tests-first forces edge case discovery. Tests-after verify memory (you didn't remember everything).

## Reference: Excuse Categories

### Velocity — Testing is faster than debugging.

| Excuse | Flaw | Action |
|---|---|---|
| "Too simple to test" | Simple code breaks too | Test takes 30 seconds. Just do it. |
| "TDD will slow me down" | Confuses short-term speed with velocity | Bugs from skipping TDD take longer to fix. |
| "Time pressure" | ≈ "TDD will slow me down" | Same flaw. Time pressure makes testing MORE important. |
| "I'll test after" | Tests passing immediately prove nothing | Write test first, watch it fail. |

### Confidence — Automated tests document confidence permanently.

| Excuse | Flaw | Action |
|---|---|---|
| "Already manually tested" | Ad-hoc ≠ systematic | Manual doesn't prove edge cases. You'll re-test every change. |
| "Manual test faster" | ≈ "Already manually tested" | Same flaw. No record, can't re-run. |
| "I know this works" | Confidence without evidence = overconfidence | Knowledge without proof isn't knowledge. |
| "Code is self-explanatory" | ≈ "I know this works" | Code explains how, tests explain what and why. |
| "Tests are obvious" | ≈ "Too simple to test" | If obvious, writing them takes 30 seconds. Do it. |
| "Coverage is good enough" | Coverage measures lines, not correctness | 100% coverage with wrong assertions = 0% safety. |
| "Tests won't catch this bug" | How do you know without trying? | Write the test. You'll be surprised. |

### Order — Tests-first forces design. Tests-after validates implementation.

| Excuse | Flaw | Action |
|---|---|---|
| "Tests after achieve same goals" | Tests-after = "what does this do?" | Tests-first = "what should this do?" Different goals. |
| "Deleting X hours is wasteful" | Sunk cost fallacy | Keeping unverified code is technical debt. Delete means delete. |
| "Keep as reference, write tests first" | You'll adapt it. That's testing after. | Delete means delete. No reference. Start fresh. |

### Complexity — Hard to test = overly coupled. Listen to the test.

| Excuse | Flaw | Action |
|---|---|---|
| "Test hard = design unclear" | Listen to test. Hard to test = hard to use. | Redesign for testability. Test pain = design feedback. |
| "Mock setup too complex" | Complex mocks = coupled design | Listen to test. Simplify dependencies. |
| "Can't test this without..." | Make it testable. | Design for testability. Decouple dependencies. |
| "Need real data to test" | Real data = flaky tests | Use test fixtures. Reproducibility > realism. |
| "Legacy code is untestable" | Make it testable incrementally | Start somewhere. Add seams. Extract testable units. |
| "Tests would duplicate code" | Tests verify behavior, not duplicate implementation | Different purpose. Tests are specifications. |

### Exemption — The situation is never special. The shortcut never works.

| Excuse | Flaw | Action |
|---|---|---|
| "Just a prototype" | Prototypes become production | Do it right first time. Temporary is permanent. |
| "Need to explore first" | ≈ "Just a prototype" | Fine. Throw away exploration. Start with TDD. |
| "Only changing one line" | One-line changes break systems | Test it. Scope ≠ impact. |
| "TDD doesn't work for X" | TDD works everywhere | You haven't learned how yet. Ask for help. |
| "Framework handles this" | Frameworks have bugs | Test your usage. Integration matters. |
| "Integration tests cover this" | Unit tests catch bugs faster, closer to source | Both are needed. Unit tests pinpoint failures. |
| "Tests add maintenance burden" | Bugs add more burden | Tests reduce total maintenance. Bugs compound. |
| "This is different because..." | It's not different | Apply the rule. No exceptions. |

### Environment — External constraints are reasons TO test, not excuses to skip.

| Excuse | Flaw | Action |
|---|---|---|
| "Existing code has no tests" | You're improving it | Add tests for new code. Lead by example. |
| "Team doesn't value tests" | Lead by example | Show value through reliability. Demonstrate impact. |
| "Tests are for QA" | Developers own quality | QA verifies, doesn't create it. Shift left. |

## Protocol: Recovery

When a rationalization is detected:

1. **STOP** — Cease generating code immediately
2. **IDENTIFY** — Classify the rationalization into one of the 6 categories above
3. **READ** — Review the master rebuttal for that category
4. **DELETE** — Remove any untested code written so far
5. **WRITE** — Create the simplest possible failing test to get back on track
