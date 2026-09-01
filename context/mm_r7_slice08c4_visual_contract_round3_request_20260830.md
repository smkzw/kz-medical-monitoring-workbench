# 08C-4 visual contract same-session round 3

Continue the same bounded read-only acceptance session. Re-open the revised contract and fixture spec after Round-2 corrections.

Confirm specifically:

- continuity GET exactly matches the live client;
- public identity keys use `result_context_token/site_ref/subject_ref/spine_ref/window_start/window_end`;
- live states are selected only through distinct existing result tokens;
- `host_width` is isolation-page-only and never enters a product request;
- rule/closure disposition Chinese matches the frozen closed set;
- every Round-1 and Round-2 P0-P2 is zero.

Return only boundary statement, residual P0-P4, and verdict `ACCEPT_CONTRACT` if and only if P0-P2 are zero. Do not start services, use ego(lite), edit files, or claim runtime visual acceptance.
