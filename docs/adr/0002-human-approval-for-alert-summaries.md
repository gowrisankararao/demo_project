# Title

Human Approval for Alert Summaries

# Status

Accepted

# Context

The capstone's n8n alert-summary workflow drafts summaries of new alerts for
the on-call channel.

# Decision

The workflow routes each generated summary to a human for approval before it
is sent to the on-call channel, rather than sending it automatically.

This approval gate is intended to prevent an incorrect or misleading automated
summary from causing the on-call engineer to under-react or over-react to a
real incident. A few minutes of approval delay costs much less than a bad
summary during an active incident.

# Consequences

Delivery is slower, and sending depends on someone being available to approve
the summary.
