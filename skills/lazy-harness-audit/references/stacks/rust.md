# Rust Stack Checklist

Maps to `references/universal-rubric.md`. See `references/stack-checklists.md` for the cross-stack heading-to-rubric mapping table.

**Markers**: `Cargo.toml`, `Cargo.lock`, `rust-toolchain*`, workspace `members`.

**Verification surfaces** (rubric §2):
- `cargo test`, `cargo test --workspace`, `cargo check`, `cargo build`.
- `cargo clippy --all-targets --all-features -- -D warnings`, `cargo fmt --check`.
- `cargo deny check`, `cargo audit`.

**Architecture fitness** (rubric §3):
- Workspace crate boundaries, `pub(crate)` discipline, feature-flag matrix.
- Public API: `cargo public-api`, semver checks (`cargo semver-checks`).

**Behavior harness** (rubric §4):
- Integration tests under `tests/`, doctest coverage, property tests (`proptest`, `quickcheck`).
- Snapshot tests (`insta`) for serialization-heavy code.

**Safety tooling** (rubric §5):
- `cargo deny` policy, `cargo audit`, supply-chain pinning, `unsafe` boundaries documented.

**Priority notes**:
- Reward only the lints actually enforced (`-D warnings` vs warn-only); warn-only Clippy is mostly cosmetic.
