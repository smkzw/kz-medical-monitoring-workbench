# R5-S5 Typed Authority Model Delta v0.1 Acceptance Record

Decision: `ACCEPT_R5_S5_TYPED_AUTHORITY_MODEL_DELTA_V0_1`

Accepted scope: the typed-authority model delta v0.1 only. Accepted temporal v0.2
`AuthorityBundleV02` is the sole serialized input authority; 17 frozen typed records
are lossless decoders. Of 272 parent leaves, 268 are accepted recipe outputs compared
to the parent packet and four shared cutoff leaves are deterministically constructed
from accepted `cutoff_binding` under the parent object-content-hash recipe.

Immutable accepted pins:

- contract raw SHA-256: `bc0c60db30721401315605f69b1d6e3c0e26b39161ea3135f1fcc547828c09cc`
- context raw SHA-256: `0950b5c463afe6cfc70a0b5cdfa249c8b329ea0c9a99589b52e265067d524d9a`
- author review raw SHA-256: `d2d1a0e953fb648366e95252d24c44e9bb2c6e32e3b8d526f62d2a0a4394e425`
- generator raw SHA-256: `4eb9f895c59867a690631a89ea412a9b00bd9ffd2bd9dbfc330618afc7d6b31a`
- verifier raw SHA-256: `f6cebddcd96658a800fc9c59f388d0b2e62c66c8b142c34e5ef511109e886b8d`
- manifest raw SHA-256: `a71f0937dd5d0a0fc77de98b41f6308b5caed0ae7d460f0282884c56127cd22c`
- manifest content hash: `38a8cadee3bcac6dd74a5ce9d522c9f744e82592f87089423e7783be7f6be976`

Codex verification passed in normal, `-O`, `-OO`, and `PYTHONHASHSEED=0,1,777`:
`decoded=2 compared=272 parent_valid=2 challenges=12 medical_writing=542
producers_absent=11 port_8911=stopped`. Generator `--check` also passed.

Fresh contradiction review resolved two repair loops and returned exact
`ACCEPT_R5_S5_TYPED_AUTHORITY_MODEL_DELTA_V0_1` for the pins above.

This record does not accept or modify v0.4.1, create or execute any producer, unlock
S5 runtime/UI/browser/real-project/model work, change medical-writing, or start 8911.
