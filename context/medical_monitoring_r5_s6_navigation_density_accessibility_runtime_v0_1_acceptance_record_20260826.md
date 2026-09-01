# R5-S6 Navigation, Density and Accessibility Runtime v0.1 Acceptance Record

Decision: `ACCEPT_R5_S6_RUNTIME_V0_1`

Date: 2026-08-26 CST

## Accepted scope

The exact ten-path synthetic/offline, renderer-neutral S6 runtime is accepted.
It implements typed deep links, no-nearest fallback, canonical and ephemeral
return restoration, density/semantic zoom, keyboard/non-colour encoding and the
frozen 1,000-event/40-indicator/300-risk corpus.

This is not frontend/browser, visual design, measured performance, real
project/model, clinical conclusion, product/production, security or
medical-writing acceptance.

## Owned hashes

- `s6_contracts.py`: `a9dff69baafb1947569771e0f35ad2982e9e78a57c55c89322fd29e90394b095`
- `s6_navigation.py`: `fcb6dec0b10af4110f096c9f20be2180226aaecbe7d2212e8eb5a27928fcdc36`
- `s6_accessibility.py`: `9617d3fe16fccfdfbfb4412346678115d4ef6463bda33313fe3aa8b2d3c4ddc6`
- `s6_validator.py`: `5e1dc0c05c5046709fd0953d4cac48b0cf874ab9de7dba547e0cb21d96ff3090`
- `s6_runtime_fixtures.py`: `130e74bd38a38af3a1cf4ca3c41f5275fd97dd8c55772ac68c433f48b67ab721`
- `test_s6_contracts.py`: `a3f62b8137e3b932777fe868c50353e28a6b5c4da372f1bb95d60e52d0c63a76`
- `test_s6_navigation.py`: `163e5d56911bf4269a0e2ef9afa5f2eea7899b2d543e16017485c4f94677c56a`
- `test_s6_validator.py`: `69a475de4b2b1d6753b735014e11baf849e684388bbe8484aecd658c82280e91`
- `test_s6_runtime_challenges.py`: `adf9d595a0a6f1d62e09e360cb2e2fa650114b34ab3d44f43485cf20b2f56447`
- evidence: `16bc0ee0f549546da6238a16ba6f9bac6c94302eb7d226a2494f5704a1198232`

## Decisive gates

- S6 `133 passed` and S5 `349 passed` in normal, `-O`, `-OO`;
- explicit non-assert matrix 104/104 in every mode;
- corpus identity 1,000/40/300 and 1,340 records;
- exact ten-path closure and all evidence hashes match;
- 8911 stopped; governed execution audit passed;
- independent verdict `ACCEPT_R5_S6_RUNTIME_V0_1`.

## Next unlocked action

Freeze S7 product-minimal-integration and real-browser acceptance contract before
touching frontend or starting 8911. S7 must define the exact product allowlist,
temporary service lifecycle, Playwright/visual evidence, 1440x900 and 1600x1000
states, task timing/click budgets, console/network gates and final shutdown.
