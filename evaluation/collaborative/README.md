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

## What these contracts do not cover

- Running anything. Capture, publication, the coordinator, announcements, the briefing, recovery and rebuilds belong to the runner (`ara-eval`). This directory has no coordinator.
- Authentication. Publisher identity comes from the runner's registered actors, not from any hash.
- Lara argument and review documents. `review_attestation` and `argument_check` attachments point to a document whose schema stage L1 (plan 03) will freeze; only the pointer shape is fixed here.
- Scientific judgment. No field here changes claim status, ranks work, or turns a reuse count into evidence.
- Transport across hosts and Git publication of packages.

## Versioning and unknown fields

Every object is closed: an unknown field rejects. Adding a field, a root kind, an attachment kind or a new meaning for an existing field requires a new schema version (for example `ara.contribution/v2`), which also changes the hash domain. A consumer that sees a version it does not know must reject the record rather than ignore parts of it. Records under an old version stay valid and keep their identities.

## How to run the tests

From the repository root, with Python 3.9 or later and no extra packages:

```sh
python3 -m unittest discover -s evaluation/collaborative -p 'test_*.py' -v
ARA_BIN=/path/to/ara python3 -m unittest discover -s evaluation/collaborative -p 'test_identity.py' -v
```

The second command adds the live ara cross-check, which needs ara 0.1.24 or later. The expected values in `vectors.json` come from three sources: ara-cli produced the snapshot manifests and their capture IDs, RFC 8785 provides two of the encoding examples, and `identity.py` computed the rest when these contracts were frozen. The tests recompute every value.
