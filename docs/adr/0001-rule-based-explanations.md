# Title

Rule-Based Explanations

# Status

Accepted

# Context

The alert explanation logic needs to describe alert severity and metric
conditions. `generate_explanation()` in `services/explainer.py` builds text
from alert fields and fixed rules.

# Decision

`generate_explanation()` builds explanations from fixed rules based on the
alert's severity, metric value, and threshold instead of calling an external
LLM API.

The reasons for this decision are:

- Explanations are instant and free.
- The service works offline in CI.
- Explanations are deterministic: the same alert always produces the same
  explanation, and tests do not depend on variable LLM output.

# Consequences

Explanations are more generic and cannot handle alert patterns that the rules
do not anticipate.
