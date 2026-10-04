# Collaborative-research contribution contracts
**Date:** 2026-10-04

Status: proposed for review in phase 1c ("freeze contribution contracts") of the collaborative research plan series that is staged in `ara-cli` (`plans/collaborative-research/`, plan 02). Nothing here has upstream approval yet. No runner implements these contracts yet; `ara-eval` is the intended first runtime.

## What this directory is

Several researchers (people or agents) work in private copies ("forks") of one ARA. When one of them finishes a piece of work, an external runner freezes it and publishes it as a *contribution*. A contribution is an immutable record that binds three things: a frozen ARA snapshot made by `ara snapshot`, the code and evidence the work used, and an envelope that says who published it and what it builds on. Peers can then read it, check it, or import it, and one integration project manager (the "integration PM") merges selected contributions into the shared canonical ARA.

This directory fixes the formats and the hash rules for those records, so that two independent programs compute the same identities from the same inputs. It contains:

| File | What it defines |
|---|---|
| `common.schema.json` | Shared value types: digests, fingerprints, identities, safe paths, native references. |
| `contribution.schema.json` | `ara.contribution/v1`, the envelope: identity, lineage, research pointers, execution binding, inventory pointer. |
| `payload-inventory.schema.json` | `ara.payload-inventory/v1`, the list of every frozen file and external object, with digest, size and mode. |
| `publication.schema.json` | Publication request, receipt, rejection, and workflow-state events. |
| `attachment.schema.json` | `ara.attachment/v1`, a later record about one contribution: verification, correction, review attestation, argument check, dispute, superseding verdict, or external-file acknowledgment. |
| `verification.schema.json` | `ara.verification/v1`, the body of a verification or superseding verdict. |
| `integration-receipt.schema.json` | `ara.integration-receipt/v1`, the import receipt and the resolution receipts appended after it. |
| `roles.schema.json` | `ara.role-policy/v1`, who may publish, verify, review, write each fork, and integrate. |
| `visibility.schema.json` | `ara.visibility/v1`, the community's list of published records at one point in the coordinator's sequence. |
| `community-request-v2.schema.json` | `ara.community-request/v2`, the reviewed revision of the plan-14 intention request schema. |
| `identity.py` | Reference implementation of the canonical encoding and every identity formula, plus checks that JSON Schema cannot express. Python standard library only. |
| `schema_check.py` | A small JSON Schema checker for exactly the keywords these schemas use, so tests need no new dependency. |
| `vectors.json` | Test vectors: inputs and expected digests, including three real `ara snapshot` manifests. |
| `test_identity.py`, `test_schemas.py` | Tests. |
| `lara/` | Stage L1 (plan 03): the contracts that attach Lara arguments, reviews and checks to contributions. See [Lara contracts (stage L1)](#lara-contracts-stage-l1). |

The directory sits beside `evaluation/agent-cli/` and follows its pattern: a short name for the plan series, JSON Schema files, a standard-library Python consumer, and `unittest` tests. It is separate from `agent-cli/` because these contracts do not change the archived interface-only skill variants or the plan-14 files.

## Which identity covers what

There are four identities. Each answers a different question.

| Identity | Covers | Does not cover | Format |
|---|---|---|---|
| Native revision (`fingerprint`) | The ARA's nonprivate file paths and bytes, as `ara merge` sees them (`ara.artifact/v1`). | File modes, code outside the ARA, who published it. | 64 lowercase hex digits, no prefix. |
| Capture ID | The exact `ara snapshot` manifest: every path, digest, size and full mode, plus the diagnostics. | Code and inputs outside the ARA, attribution. | `sha256:` + 64 hex. |
| Payload digest | The full payload inventory: the snapshot manifest and package files, code, evidence, external objects, entry point, configuration and environment. | Who published it, parents, scientific claims. | `sha256:` + 64 hex. |
| Contribution ID | The envelope, which includes the payload digest, community, publisher, request, source key, lineage and research pointers. | Later receipts, verdicts and integration state. | `sha256:` + 64 hex. |

Two consequences follow. A change to only one file's mode keeps the native revision but changes the capture ID, and so changes the payload digest and the contribution ID. Two identical payloads published by different people, or with different parents, get different contribution IDs. Parent links, verification targets and integration receipts always name contribution IDs, never a payload digest.

No identity proves authorship. The runner's actor permissions bind the publisher.

## How every digest is computed

All records are JSON encoded with RFC 8785 (the JSON Canonicalization Scheme, "JCS"): object keys sorted by UTF-16 code units, no whitespace, minimal string escaping. The value domain is objects, arrays, strings, booleans, null and integers between -(2^53-1) and 2^53-1. Floating-point numbers are not allowed anywhere, so measured values are written as decimal strings. Duplicate keys and invalid Unicode reject.

Every identity is `"sha256:" + hex(SHA-256(domain || 0x00 || JCS(value)))`:

| Identity | Domain | Value hashed |
|---|---|---|
| Capture ID | `ara.capture/v1` | snapshot manifest without `capture_id` (ara-cli's rule, reproduced) |
| Payload digest | `ara.payload/v1` | the whole payload inventory |
| Contribution ID | `ara.contribution/v1` | envelope without `contribution_id` |
| Attachment `record_id` | `ara.attachment/v1` | attachment without `record_id` |
| Integration `record_id` | `ara.integration-receipt/v1` | receipt without `record_id` |
| Publication `request_digest` | `ara.publication-request/v1` | the whole request |
| Publication `receipt_id` | `ara.publication-receipt/v1` or `ara.publication-rejection/v1` | receipt without `receipt_id` |
| `visibility_id` | `ara.visibility/v1` | snapshot without `visibility_id` |
| `policy_id` | `ara.role-policy/v1` | role policy without `policy_id` |

The domain is always the record's own `schema` value, so two kinds of record can never share an identity. Plain file digests (inventory entries, `snapshot.json` itself) are `sha256:` over the raw bytes with no domain.

Arrays that the schemas call sorted use code-point order of their sort key, which is the same as UTF-8 byte order, and reject duplicates. The sort keys are: inventory entries and external objects by `(root, path)`, roots by `name`, parents by value, `uses` by `(source_key, native_revision, selector)`, identity mappings by `(source_key, original, layer, path, target)`, external references by `(contribution_id, source_key, native_revision, path)`, visibility lists by `sequence`. `identity.py` checks all of these.

## Rules the schemas carry beyond field shapes

- **Request idempotency.** A publication request is identified by `(community, publisher, request)`, and `request` must start with `<publisher>:` as in plan 14. Once accepted, that triple is bound to one record identity. An exact retry returns the original receipt. Any other content under the same triple rejects with `request_conflict`. Contributions and attachments share this namespace. `identity.RequestLedger` implements the rule.
- **Pre-execution predictions.** When a contribution names a `prediction`, it must also name the acknowledged plan-14 `request_digest` that authorized execution and the acknowledged input signature. A prediction first written after the run cannot be presented as made before it.
- **Native binding.** The inventory's snapshot root must hold exactly `snapshot.json` and one `ara/<path>` entry per manifest file, with the same digest, size and mode. The recomputed capture ID must match. `identity.check_native_binding` does this check.
- **Paths.** Paths are relative, use `/`, and contain no empty, `.`, `..`, `.ara` or `.git` component, no backslash and no control character. Private `.ara/transactions` and lock files never enter a payload.
- **States are external.** Publication goes `draft → frozen → published`. Integration is a separate track: `pending`, `imported-with-conflicts`, `integrated`, `rejected-for-integration`. These are recorded as events; none of them changes a contribution or a native claim status. Publication means "durably available and structurally valid", never "scientifically correct".
- **Later records never rewrite earlier ones.** Verifications, corrections, disputes, review attestations and superseding verdicts are new attachments that target a contribution ID. A superseding verdict names the record it replaces; that record stays.
- **Integration.** A receipt marked `integrated` must report zero unresolved conflicts. An external-file acknowledgment records that the integration PM kept canonical's own file (`merge resolve --take ours`) while the incoming bytes stay in the named contribution. It does not approve the experiment.
- **Roles.** Exactly one actor is the integration PM. Each fork has exactly one continuity writer. The independence section lists known shared factors such as the same model or operator; separate accounts are never evidence of independence.

Each schema lists its remaining consumer rules under `x-consumer-invariants`.

## The intention schema revision (v2)

`community-request-v2.schema.json` is a copy of the plan-14 file `evaluation/agent-cli/community-smoke-scenarios/request.schema.json` with these changes, and no others (the test `IntentionRevisionDiff` enforces this):

| Definition | Change |
|---|---|
| `$id` | `ara.community-request/v1` → `ara.community-request/v2`. |
| `prediction` (new) | `null` or `{native_revision, selector, input_signature}`: the prediction's native revision and selector, bound before execution together with the acknowledged input signature. |
| `contribution_ids` (new) | Sorted, unique contribution IDs. |
| `intention` | Adds required `prediction` and `result_contributions` (must be empty at publish). `verification_of` gains a third form, `{contribution_id, selectors}`, so an intention can verify a published contribution instead of only another intention. |
| `refresh-intention` | Adds optional `prediction` (may be set once, before the execute request) and `result_contributions` (accepted only with state `completed`). |
| `initialize` | Only the `$ref` path to the unchanged `run-config.schema.json`. |

Completion keeps the pre-work `artifact_revision` and the prediction unchanged and adds result contribution IDs separately. An intention-completion receipt is not a publication certificate. The v1 file and the plan-14 coordinator are unchanged; a coordinator that accepts v2 is runner work.

## Adopted ara-cli contracts

These contracts build on two contracts frozen in `ara-cli` and adopt them by exact reference to commit `da43bf642fca52ab201bc6d44d6b972ebf22b6f7` on its `feat/collaborative-ara` branch:

| ara-cli file | SHA-256 of the file at that commit | Bytes | Used for |
|---|---|---|---|
| `docs/collaborative-research/snapshot-contract.md` (`ara.snapshot/v1`) | `013abf0c9614eae7d19eb2c8145de2d815b24b972c8f396385daf54a0801b1d1` | 7265 | Snapshot package layout, manifest fields, capture ID. |
| `docs/collaborative-research/provenance-contract.md` (peer-feedback provenance) | `6b5898ef8249694d865db03b46c47e60f9d19887130c0647c366015e1337557c` | 17454 | Source facts versus import events, `--self-key`, identity mappings copied into integration receipts. |

`identity.capture_id` reproduces ara-cli's capture ID. We checked this against the real binary: ara 0.1.25 built at that commit (`cargo build -p ara-cli`) captured three packages from `examples/minimal-artifact`. For all three, `JCS(parsed snapshot.json)` equals the file's bytes and the recomputed capture ID equals the one ara printed. The second package differs from the first only in one file's mode; it has the same fingerprint and a different capture ID. The third adds a diagnostic and a file whose name has a non-ASCII letter and quotes, to exercise string escaping. The manifests are stored verbatim in `vectors.json`. Set `ARA_BIN` to repeat the check against a live binary.

A later ara-cli contract revision needs a new pin here; it does not silently replace this one.

### Current pin: ara-cli `afd96b4` (ara 0.1.26)

ara-cli amended the provenance contract after the first pin. Phase 4 review (ARA-Labs/ara-cli#104) and the plan-04b fixes (ARA-Labs/ara-cli#112) changed four rules:
- a peer-supplied self fact proves identity only, never a content base;
- `merge.unshared_origin_revision`;
- external code and evidence never prove an origin, and a retired ID proves only its retired identity;
- protected YAML history compares exact relocated bytes.

The snapshot contract is unchanged. The current adoption is commit `afd96b4957dd4acca2213be0941533a89608d2c2` on ara-cli `feat/collaborative-ara`:

| ara-cli file | SHA-256 at `afd96b4` | Bytes | Status |
|---|---|---|---|
| `docs/collaborative-research/snapshot-contract.md` | `013abf0c9614eae7d19eb2c8145de2d815b24b972c8f396385daf54a0801b1d1` | 7265 | Unchanged from the first pin. |
| `docs/collaborative-research/provenance-contract.md` | `b00fe527f231b1978a3e739f152b67597c3173239d4ace3d99fce794a701970d` | 20331 | Supersedes `6b5898ef…557c` (17454 bytes) at `da43bf6`. |

The runner (`ara-eval` `vendor/ara-cli`) pins the same commit.

## What these contracts do not cover

- Running anything. Capture, publication, the coordinator, announcements, the briefing, recovery and rebuilds belong to the runner (`ara-eval`). This directory has no coordinator.
- Authentication. Publisher identity comes from the runner's registered actors, not from any hash.
- Running Lara. Stage L1 (`lara/`, below) freezes the Lara documents that `review_attestation` and `argument_check` attachments point to; invoking the checker and building views is stage L2 runner work.
- Scientific judgment. No field here changes claim status, ranks work, or turns a reuse count into evidence.
- Transport across hosts and Git publication of packages.

## Versioning and unknown fields

Every object is closed: an unknown field rejects. Adding a field, a root kind, an attachment kind or a new meaning for an existing field requires a new schema version (for example `ara.contribution/v2`), which also changes the hash domain. A consumer that sees a version it does not know must reject the record rather than ignore parts of it. Records under an old version stay valid and keep their identities.

## How to run the tests

From the repository root, with Python 3.9 or later and no extra packages:

```sh
python3 -m unittest discover -s evaluation/collaborative -p 'test_*.py' -v
ARA_BIN=/path/to/ara python3 -m unittest discover -s evaluation/collaborative -p 'test_identity.py' -v
LARA_BIN=/path/to/lara python3 -m unittest discover -s evaluation/collaborative -p 'test_lara_checker.py' -v
```

The second command adds the live ara cross-check, which needs ara 0.1.24 or later. The third runs the Lara smoke test (see below). The expected values in `vectors.json` come from three sources: ara-cli produced the snapshot manifests and their capture IDs, RFC 8785 provides two of the encoding examples, and `identity.py` computed the rest when these contracts were frozen. The tests recompute every value.

## Lara contracts (stage L1)

Status: proposed for review in stage L1 ("Lara contracts") of plan 03. Nothing here runs Lara; stage L2 does.

[Lara](https://github.com/ARA-Labs/Lara) is a separate checker for structured arguments. For a few selected claims, an argument producer can write a Lara argument (a `.lara` file) that states the claim formally and cites the measured cells it rests on. `lara check` then rechecks the arithmetic (for example, that 0.71 < 0.74), applies the declared policy, and reports each claim as `justified`, `gap`, `defeated` or `contested`. Several members' arguments can also be checked together through a `.laramap` manifest, which is how two contributions that contradict each other under the same setting become `contested`.

The files in `lara/` say exactly which inputs such a check used, who reviewed the formalization, and which contributions a combined map covers.

### What each record binds

| File | Record (hash domain) | Binds |
|---|---|---|
| `lara-binding.schema.json` | `ara.lara-binding/v1` | One argument file to the native ARA it was written against: the snapshot (fingerprint and capture ID), the argument bytes and their `artifact … at sha256:<fingerprint>` header, the policy file, the setting registry, and, for each selected claim, every Lara claim, leaf, argument and attack mapped to a source key, native revision, selector and evidence digest. Also the formalization author, rationale, assumptions and the author's own audit label, which is kept but never trusted. |
| `review-attestation.schema.json` | `ara.lara-review-attestation/v1` | One reviewer's judgment of one binding: reviewer, role policy, target contribution (or the initial payload), native snapshot, the exact argument, binding, policy and registry reviewed, the reviewed claims and selectors, `approved`, `disputed` or `rejected`, a rationale, and an optional link that supersedes the reviewer's own earlier record or disputes another one. |
| `setting-descriptor.schema.json` | `ara.lara-setting-descriptor/v1`, `ara.lara-system-descriptor/v1` | What makes two measurements comparable: dataset and split digests, evaluator revision and configuration digest, metric definition and polarity (`higher_is_better` or `lower_is_better`), controls, and how seeds and other replication variables are treated. Systems and baselines are separate descriptors bound to code and configuration digests. Outcomes never enter a descriptor. |
| `setting-registry.schema.json` | `ara.lara-setting-registry/v1` | A versioned vocabulary: which Lara symbols (`accuracy`, `imagenet_val`, `sys_new`) stand for which descriptors, under which policy. Each symbol has one meaning. An extension is a new registry revision that keeps every old symbol. |
| `argument-check.schema.json` | `ara.lara-argument-check/v1` | One run of the pinned checker: the checker build, backends and theories, the policy, every input digest, the target (a contribution or a map revision), the exit status, the digest of the verdict bytes, the outcome (`accepted`, `rejected`, `unavailable`, `not-performed`), per-claim statuses, and admission-blocked claims kept in their own list. |
| `map-revision.schema.json` | `ara.lara-map-revision/v1` | The input scope of one composite map: the exact `.laramap` bytes, members in manifest order (alias → contribution, argument, binding, source identity), policy, registry, checker, the intended population at a visibility sequence, the coverage scope (`audited` or `exploratory`), and every excluded contribution with its reason. It holds no outputs, so its identity never depends on a verdict. |
| `lara-common.schema.json` | none | Shared value types. |
| `checker-pin.json` | `ara.lara-checker-pin/v1` (data) | The checker used to freeze these contracts (see below). |

Identities follow the rules above: `"sha256:" + hex(SHA-256(schema || 0x00 || JCS(record without its own ID field)))`. Lara documents stored in an attachment are stored as their exact JCS bytes. An argument's location is either the target contribution's initial payload, a named `argument_check` attachment, or (for a check only) the attachment that also holds the check, since that attachment cannot name its own record ID.

`lara_identity.py` computes the identities and checks bindings, descriptors, registries, check records and Lara attachments. `lara_audit.py` holds the review and map-scope rules. Both use only the Python standard library and reuse `identity.py`.

### Rules beyond field shapes

- **Arguments target one snapshot.** The argument's header must name `sha256:<native fingerprint>`. Otherwise the package is rejected (`snapshot_mismatch`) and a new argument must be written against the new snapshot.
- **No self-review.** A review counts only if the reviewer holds `authorized_reviewer` in the pinned role policy and is neither the producer nor the formalization author of any reviewed claim. Self-reviews and unauthorized reviews are kept and shown, but supply no coverage. Lara's own `audit-status = reviewed` label never counts.
- **Changed inputs void a review.** If the argument, binding, policy, registry or snapshot changes, earlier approvals do not apply to the new version.
- **Disputes win until withdrawn.** A claim is audited only when a current approval covers it and no current `disputed` or `rejected` attestation (or open `ara.dispute/v1` naming the approval) covers the same inputs. A reviewer withdraws a dispute by superseding their own record.
- **Supersession is narrow.** A record can supersede only an earlier one from the same verifier or reviewer with the same target, method/configuration, inputs and scope. Nothing is erased.
- **Exit status first.** `lara check --out <path>` replaces the file only on success, so a failed run leaves an older verdict behind. A check record may say `verdict_source: out_file` only when the exit status is 0; `exit_checked_before_output_read` is always `true`. Exit 0 is `accepted`, exit 1 is `rejected`, exit 2 is a `rejected` boundary error (ill-formed input), and anything else, including an executable whose digest differs from the pin, is `unavailable`.
- **Maps cover a stated population.** Members plus exclusions must equal the intended population. Audited maps admit only members whose every selected claim is audited; the rest stay listed with a reason (`absent_argument`, `unreviewed_binding`, `disputed_binding`, `vocabulary_mismatch`, `incompatible_policy`, `unsupported_admission`, `other`). Any change to the roster, population, visibility point, policy, registry, checker or manifest is a new map revision, and earlier verdicts, including contests, stay attached to their own revision.
- **Settings are not names.** Two replications of one setting with different outcomes share one descriptor ID. Two evaluator configurations on the same dataset name do not.

### Trust boundary

These are four different facts, recorded separately:

| Fact | Established by | Does not establish |
|---|---|---|
| Lara argument status | an `ara.lara-argument-check/v1` record | that the formal statement matches the evidence, that the experiment was run correctly, or anything about ARA maturity |
| Formalization review | an authorized `ara.lara-review-attestation/v1` | measurement correctness, reproduction, or reviewer independence |
| Reproduction | an `ara.verification/v1` record with raw outputs | argument status or review |
| ARA research maturity | the native ARA closure procedure | anything above; no Lara record changes a claim's status |

A `justified` claim can still rest on a wrong formalization or an unsuitable policy. A `rejected` check says the argument failed, not that the experiment failed.

### Pins

- Lara source: `ARA-Labs/Lara` commit `a31299feafb484404b62bc3b4fd313d987cdda44`, the revision plan 03 inspected. Verdicts there name `lara-core@0.2`.
- Executable: SHA-256 `dfbc5966941a4be55524073ca375787b8e5b2ed05c916e14232773e7ba28d645`, a local `aarch64-apple-darwin` cabal build (GHC 9.14.1) of that commit. It is **not** a release artifact and prints no version string (`--version` prints usage and exits 2). Registering a scored study must re-pin a release executable.
- Policy used by the vectors: Lara's `examples/S4/ord-setting-v1.policy.lara` at that commit, SHA-256 `17d383fa0205f4303eda1cd1bc4f895abd30d91dfe7caee962fe6ceeb6eb85e5`. The vocabulary `imagenet-cls` in `lara/vectors.json` is a test fixture, not a registered study vocabulary.
- `ara.attachment/v1` is unchanged. Its `deferred_body` pattern already admits `ara.lara-review-attestation/v1` and `ara.lara-argument-check/v1`; `lara_identity.check_lara_attachment` enforces which kind carries which document.

### What stage L2 (the runner adapter in `ara-eval`) must do

1. Run Lara only under an explicitly selected runner policy. Ordinary CLI reads, writes, validation and merges must not look for the checker.
2. Verify the executable's SHA-256 against the pin before running it, and record `unavailable` on a mismatch or a missing checker. A policy that requires Lara then fails explicitly.
3. Materialize the exact argument, binding, policy, registry and member bytes named by the records (Lara maps read local paths and do not check digests), run `lara check`, read the exit status first, and archive stdout, stderr and the verdict bytes.
4. Build `ara.lara-argument-check/v1` records from that run, publish contribution checks and reviews as attachments with the matching kind, and publish map revisions and map checks under their own hash domains with the same request and recovery rules.
5. Compute audited coverage with the rules above, build audited maps only from audited members, and label exploratory maps as exploratory.
6. Show checker status, audit state, reproduction and maturity side by side, never merged. Add map revisions and map checks to a later visibility snapshot revision.
7. Re-pin a release executable before any scored registration.
