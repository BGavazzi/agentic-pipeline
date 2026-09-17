# W10 — Receipt fuzz benchmark boundary

`receipt_fuzz_benchmark.py` is a deterministic, bounded property-style
regression check for the admission evaluator. With the default seed it creates
128 JSON-shaped malformed replacements across 13 authoritative nested paths.
The first 13 cases guarantee path coverage; the remaining cases choose paths
from the same fixed set using the seeded generator.

The hard limits are 512 cases and payload depth 6. The default run uses 128
cases and depth 3. Each case starts from a complete synthetic high-risk
fixture, replaces one evaluator-consumed field, and classifies the result as:

- `rejected`: the evaluator raises a validation/type error;
- `blocked`: the evaluator returns `admitted=false`;
- `unsafe-admitted`: the evaluator returns `admitted=true` and fails the
  benchmark.

The JSON report records the seed, bounds, path coverage, payload digests,
fail-closed rate and unsafe survivor IDs. It deliberately contains no wall
clock or host-dependent metric, so repeated runs are byte-stable for the same
arguments.

This is synthetic fuzz evidence, not authenticity proof. It says nothing about
who produced a receipt, whether a CI artifact was protected, whether a worker
was isolated, or whether an external platform faithfully supplied the input.
It also does not prove universal parser safety. The full suite, clean-room
integration evidence, scanner results and protected producer policy remain
separate gates.

Local invocation:

```powershell
python scripts/receipt_fuzz_benchmark.py --output .docs/test-reports/receipt-fuzz.json
```
