#!/usr/bin/env python3
"""One-host, stdlib-only shared-intention coordinator; not a scientific agent.

All commands print JSON. Allocation units meter accepted request lifecycles and
explicit research accounting, not tokens or CPU measurements. This consumer is
not the external scored experiment harness. Only this coordinator writes the
channel journal and snapshot. The registered caller identity is --actor; it is a
trusted runner identity, not authentication against hostile local processes.
"""

import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


SCHEMA = "ara.community-transport/v1"
STATES = ["planned", "active", "completed", "abandoned", "expired"]
ROLES = ["reader", "contributor", "fork-pm", "integration-pm"]
FAILURE_POLICY = {
    "channel_unavailable": "pause-budget-consuming-work",
    "round_closure": "all-admitted-actors-finished-or-registered-failure",
    "registered_failures": ["actor-unavailable", "channel-unavailable", "budget-exhausted"],
}
OPERATIONS = ["initialize", "snapshot", "refresh", "publish", "refresh-intention",
              "execute", "finish-round", "close-failure", "recover"]
IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
MAX_JSON_BYTES = 1024 * 1024
MAX_LOG_BYTES = 64 * 1024 * 1024


class ChannelError(Exception):
    def __init__(self, code, message, unavailable=False):
        super().__init__(message)
        self.code = code
        self.unavailable = unavailable


def reject(code, message):
    raise ChannelError(code, message)


def unavailable(message):
    raise ChannelError("channel_unavailable", message, True)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) != set(required) | (set(value) & set(optional)):
        reject("invalid_request", "Expected fields " + ", ".join(sorted(required)) +
               "; optional: " + ", ".join(sorted(optional)))


def integer(value, name, minimum=0, maximum=1000000):
    if type(value) is not int or not minimum <= value <= maximum:
        reject("invalid_request", name + " must be a bounded whole number")
    return value


def text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 16384:
        reject("invalid_request", name + " must be a nonempty bounded string")
    return value


def identity(value, name):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        reject("invalid_request", name + " must be a portable run-scoped identity")
    return value


def owned(value, actor, name):
    text(value, name)
    if not value.startswith(actor + ":") or not IDENTITY.fullmatch(value[len(actor) + 1:]):
        reject("actor_ownership", name + " must have the registered actor prefix " + actor + ":")
    return value


def read_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_JSON_BYTES:
        reject("invalid_request", "JSON input exceeds bounded request size")
    try:
        return decode(raw)
    except (ValueError, UnicodeError) as error:
        reject("invalid_request", "Invalid JSON: " + str(error))


def fsync_directory(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def remove_durable(path):
    path.unlink()
    fsync_directory(path.parent)


def contract_section(contract):
    if not isinstance(contract, dict) or contract.get("schema") != "ara.collective-contract/v1":
        reject("invalid_contract", "Expected pinned ara.collective-contract/v1 contract")
    section = contract.get("transport_consumer")
    expected = {
        "schema": SCHEMA,
        "channel_path": "shared/community/{community_id}/intentions",
        "writer": "coordinator-only",
        "durability": "event-fsync-before-atomic-snapshot",
        "states": STATES,
        "roles": ROLES,
        "failure_policy": FAILURE_POLICY,
    }
    if not isinstance(section, dict) or any(section.get(k) != v for k, v in expected.items()):
        reject("invalid_contract", "Pinned transport schema, roles or failure policy disagree with consumer")
    accounting = section.get("accounting", {})
    if (not isinstance(accounting, dict) or
            accounting.get("allocation") != "equal-total-per-actor" or
            accounting.get("includes") != ["coordination", "research"] or
            type(accounting.get("coordination_units")) is not int or
            accounting.get("coordination_units") != 1 or
            accounting.get("unit") != "protocol-allocation-unit" or
            accounting.get("request_lifecycle_includes") != ["submission", "deduplication", "receipt-recovery"]):
        reject("invalid_contract", "Unsupported accounting contract")
    return section


def validate_config(config, community):
    keys(config, ["schema", "run_id", "community_id", "coordinator_id", "actors",
                  "allocation_per_actor", "refresh_cadence_rounds", "expiry_rounds",
                  "max_rounds", "failure_policy"])
    if config["schema"] != "ara.community-run/v1" or config["community_id"] != community:
        reject("invalid_config", "Run schema or community identity mismatch")
    for key in ("run_id", "community_id", "coordinator_id"):
        identity(config[key], key)
    actors = config["actors"]
    if not isinstance(actors, list) or not 2 <= len(actors) <= 64:
        reject("invalid_config", "Admit between two and 64 actors before initialization")
    seen = set()
    for actor in actors:
        keys(actor, ["actor_id", "source_identity", "role"])
        identity(actor["actor_id"], "actor_id")
        text(actor["source_identity"], "source_identity")
        if actor["actor_id"] in seen or actor["role"] not in ROLES:
            reject("invalid_config", "Duplicate actor or unknown role")
        seen.add(actor["actor_id"])
    if config["coordinator_id"] not in seen:
        reject("invalid_config", "Coordinator must be an admitted, budgeted actor")
    integer(config["allocation_per_actor"], "allocation_per_actor", 1)
    integer(config["refresh_cadence_rounds"], "refresh_cadence_rounds", 1, 10000)
    integer(config["expiry_rounds"], "expiry_rounds", config["refresh_cadence_rounds"], 10000)
    integer(config["max_rounds"], "max_rounds", 1, 10000)
    if config["failure_policy"] != FAILURE_POLICY:
        reject("invalid_config", "Failure policy must equal the pinned registered policy")


def initial_state(config, contract_digest):
    actors = {actor["actor_id"]: dict(actor, coordination_used=0, research_used=0,
              remaining=config["allocation_per_actor"], last_refresh_round=None,
              last_observed_sequence=None) for actor in config["actors"]}
    return {"schema": "ara.community-snapshot/v1", "run_id": config["run_id"],
            "community_id": config["community_id"], "contract_digest": contract_digest,
            "config": config, "sequence": 0, "round": 1, "status": "running",
            "actors": actors, "intentions": {}, "round_closures": {},
            "requests": {}, "last_event_hash": None}


def refs(values, source=None):
    if not isinstance(values, list) or len(values) > 1024:
        reject("invalid_request", "Refs must be a bounded list of source-qualified objects")
    for value in values:
        keys(value, ["source_identity", "native_ref"])
        text(value["source_identity"], "source_identity")
        text(value["native_ref"], "native_ref")
        if source is not None and value["source_identity"] != source:
            reject("source_identity", "Native refs must belong to the publisher's registered fork")


def fresh(record, round_number):
    return record["state"] in ("planned", "active") and round_number <= record["expires_after_round"]


def overlaps(state):
    records = sorted((value for value in state["intentions"].values()
                      if fresh(value, state["round"])), key=lambda item: item["intention_id"])
    result = []
    for index, first in enumerate(records):
        for second in records[index + 1:]:
            if first["experiment_signature"] == second["experiment_signature"]:
                result.append({"experiment_signature": first["experiment_signature"],
                               "owners": [{key: value[key] for key in
                                           ("actor_id", "intention_id", "revision", "source_identity",
                                            "native_refs", "verification_of", "verification_rationale")}
                                          for value in (first, second)],
                               "judgment_required": True, "exclusive_lock": False})
    return result


def view(state):
    return {key: copy.deepcopy(state[key]) for key in
            ("run_id", "community_id", "sequence", "round", "status", "actors",
             "intentions", "round_closures")}


def reserved(state, actor):
    return sum(max(0, record["budget_reserved"] - record["budget_used"])
               for record in state["intentions"].values()
               if record["actor_id"] == actor and fresh(record, state["round"]))


def charge(state, actor, research=0):
    allocation = state["actors"][actor]
    if allocation["remaining"] < 1 + research:
        reject("budget_exhausted", "Coordination and research share the actor's finite total allocation")
    allocation["coordination_used"] += 1
    allocation["research_used"] += research
    allocation["remaining"] -= 1 + research


def record_history(record, sequence, round_number, operation):
    record["history"].append(dict({key: copy.deepcopy(value) for key, value in record.items()
                                  if key != "history"}, event_sequence=sequence,
                                 event_round=round_number, operation=operation))


def verify_replication(state, record):
    verification = record["verification_of"]
    rationale = record["verification_rationale"]
    if rationale is not None:
        text(rationale, "verification_rationale")
    if verification is not None:
        keys(verification, ["source_identity", "intention_id", "revision"])
        integer(verification["revision"], "verification revision", 1)
        text(verification["source_identity"], "verification source_identity")
        text(verification["intention_id"], "verification intention_id")
        prior = state["intentions"].get(verification["intention_id"])
        if (prior is None or prior["source_identity"] != verification["source_identity"] or
                not any(h["revision"] == verification["revision"] for h in prior["history"])):
            reject("invalid_verification", "Verification must identify a retained source-qualified intention revision")
        if rationale is None:
            reject("invalid_verification", "Intentional verification must record its rationale")


def apply(state, operation, actor, request, sequence, contract_digest):
    """Deterministic transition; used both for live commits and journal replay."""
    if operation == "initialize":
        keys(request, ["request_id", "config"])
        config = request["config"]
        if not isinstance(config, dict) or "community_id" not in config:
            reject("invalid_config", "Initialization requires a complete run configuration")
        validate_config(config, config["community_id"])
        if actor != config["coordinator_id"]:
            reject("coordinator_only", "Only the registered coordinator initializes the channel")
        state = initial_state(copy.deepcopy(config), contract_digest)
    elif state is None:
        unavailable("Journal has no initialization event")
    if actor not in state["actors"]:
        reject("unknown_actor", "Caller process actor is not admitted to this run")
    owned(request.get("request_id"), actor, "request_id")
    if operation != "initialize" and state["status"] != "running":
        reject("run_closed", "This bounded run is closed; recovery remains available")
    if operation not in ("initialize", "refresh"):
        integer(request.get("observed_sequence"), "observed_sequence", 1)
        integer(request.get("observed_round"), "observed_round", 1, 10001)
        if request["observed_sequence"] != state["sequence"] or request["observed_round"] != state["round"]:
            reject("stale_snapshot", "Refresh and reconsider: observed sequence/round is no longer current")
    if operation in ("publish", "refresh-intention", "execute"):
        if state["actors"][actor]["last_refresh_round"] != state["round"]:
            reject("refresh_required", "Refresh the shared snapshot this round before publishing or executing")
    if operation not in ("initialize", "refresh", "close-failure"):
        if actor in state["round_closures"].get(str(state["round"]), {}):
            reject("round_finished", "Actor already finished or was failure-closed in this round")
    record = None
    research = 0
    if operation == "initialize":
        pass
    elif operation == "refresh":
        keys(request, ["request_id"])
        state["actors"][actor]["last_refresh_round"] = state["round"]
        state["actors"][actor]["last_observed_sequence"] = sequence
    elif operation == "publish":
        keys(request, ["request_id", "observed_sequence", "observed_round", "expected_revision", "intention"])
        integer(request["expected_revision"], "expected_revision")
        if request["expected_revision"] != 0:
            reject("stale_revision", "New intention publication expects revision zero")
        item = request["intention"]
        keys(item, ["intention_id", "source_identity", "artifact_revision", "native_refs", "action",
                    "question", "experiment_signature", "verification_of", "verification_rationale",
                    "state", "budget_reserved", "result_refs"])
        owned(item["intention_id"], actor, "intention_id")
        if item["intention_id"] in state["intentions"]:
            reject("stale_revision", "Intention identity is already retained; do not overwrite history")
        if item["source_identity"] != state["actors"][actor]["source_identity"]:
            reject("source_identity", "Publisher must use its registered fork identity")
        for key in ("artifact_revision", "action", "question", "experiment_signature"):
            text(item[key], key)
        refs(item["native_refs"], item["source_identity"])
        refs(item["result_refs"], item["source_identity"])
        if item["state"] != "planned" or item["result_refs"]:
            reject("invalid_transition", "New intentions start planned without claimed results")
        integer(item["budget_reserved"], "budget_reserved")
        record = dict(copy.deepcopy(item), community_id=state["community_id"], actor_id=actor,
                      revision=1, published_sequence=sequence, refresh_round=state["round"],
                      expires_after_round=state["round"] + state["config"]["expiry_rounds"],
                      budget_used=0, history=[])
        verify_replication(state, record)
        state["intentions"][record["intention_id"]] = record
    elif operation in ("refresh-intention", "execute"):
        required = ["request_id", "observed_sequence", "observed_round", "intention_id", "expected_revision"]
        keys(request, required + (["research_units"] if operation == "execute" else ["state"]),
             [] if operation == "execute" else ["budget_reserved", "result_refs"])
        owned(request["intention_id"], actor, "intention_id")
        record = state["intentions"].get(request["intention_id"])
        if record is None or record["actor_id"] != actor:
            reject("actor_ownership", "Only the intention owner may change it")
        integer(request["expected_revision"], "expected_revision", 1)
        if request["expected_revision"] != record["revision"]:
            reject("stale_revision", "Expected intention revision is no longer current")
        if not fresh(record, state["round"]):
            reject("invalid_transition", "Terminal or expired records are retained, not revived")
        if operation == "execute":
            if record["state"] != "active":
                reject("invalid_transition", "Execution requires acknowledged active intention")
            if state["round"] - record["refresh_round"] >= state["config"]["refresh_cadence_rounds"]:
                reject("refresh_required", "Refresh the owned intention at its registered whole-round cadence before execution")
            research = integer(request["research_units"], "research_units", 1)
            if record["budget_used"] + research > record["budget_reserved"]:
                reject("budget_exhausted", "Execution exceeds its visible intention reservation")
            record["budget_used"] += research
        else:
            next_state = request["state"]
            allowed = {"planned": ["planned", "active", "abandoned"],
                       "active": ["active", "completed", "abandoned"]}
            if next_state not in allowed[record["state"]]:
                reject("invalid_transition", "Unsupported intention lifecycle transition")
            if "budget_reserved" in request:
                integer(request["budget_reserved"], "budget_reserved", record["budget_used"])
                record["budget_reserved"] = request["budget_reserved"]
            if "result_refs" in request:
                refs(request["result_refs"], record["source_identity"])
                record["result_refs"] = copy.deepcopy(request["result_refs"])
            if next_state == "completed" and not record["result_refs"]:
                reject("missing_results", "Completion records native result refs; it does not certify scientific success")
            record["state"] = next_state
            record["refresh_round"] = state["round"]
            record["expires_after_round"] = state["round"] + state["config"]["expiry_rounds"]
        record["revision"] += 1
        record["published_sequence"] = sequence
    elif operation in ("finish-round", "close-failure"):
        required = ["request_id", "observed_sequence", "observed_round"]
        keys(request, required + (["target_actor", "reason", "close_run"] if operation == "close-failure" else []))
        target = actor
        closure = {"kind": "finished", "sequence": sequence}
        if operation == "close-failure":
            if actor != state["config"]["coordinator_id"]:
                reject("coordinator_only", "Registered failure closure belongs to the coordinator")
            target = request["target_actor"]
            identity(target, "target_actor")
            if target not in state["actors"] or request["reason"] not in FAILURE_POLICY["registered_failures"]:
                reject("invalid_failure", "Unknown actor or unregistered failure reason")
            if type(request["close_run"]) is not bool:
                reject("invalid_failure", "close_run must be boolean")
            closure = {"kind": "failure", "reason": request["reason"], "sequence": sequence,
                       "registered_by": actor}
        closures = state["round_closures"].setdefault(str(state["round"]), {})
        if target in closures:
            reject("round_finished", "A round actor can be closed only once")
        closures[target] = closure
        if operation == "close-failure" and request["close_run"]:
            state["status"] = "failure-closed"
            state["run_failure"] = copy.deepcopy(closure)
        elif set(closures) == set(state["actors"]):
            state["round"] += 1
            for intention in state["intentions"].values():
                if intention["state"] in ("planned", "active") and state["round"] > intention["expires_after_round"]:
                    intention["state"] = "expired"
                    intention["revision"] += 1
                    intention["published_sequence"] = sequence
                    record_history(intention, sequence, state["round"], "logical-expiry")
            if state["round"] > state["config"]["max_rounds"]:
                state["status"] = "round-limit-closed"
    else:
        reject("invalid_operation", "Unknown coordinator operation")
    charge(state, actor, research)
    if reserved(state, actor) > state["actors"][actor]["remaining"]:
        reject("budget_exhausted", "Reservations plus coordination cannot exceed the same total allocation")
    state["sequence"] = sequence
    if record is not None:
        record_history(record, sequence, state["round"], operation)
    ack = {"schema": "ara.community-ack/v1", "request_id": request["request_id"],
           "operation": operation, "actor_id": actor, "sequence": sequence,
           "round": state["round"], "status": state["status"],
           "accounting": copy.deepcopy(state["actors"][actor]), "overlaps": overlaps(state)}
    if record is not None:
        ack["intention"] = copy.deepcopy(record)
    if operation in ("initialize", "refresh", "finish-round", "close-failure"):
        ack["view"] = view(state)
    return state, ack


class Channel:
    def __init__(self, run_root, community_id, contract, fault=None):
        identity(community_id, "community_id")
        self.contract = copy.deepcopy(contract)
        contract_section(contract)
        self.contract_digest = digest(contract)
        self.directory = Path(run_root).resolve() / "shared" / "community" / community_id / "intentions"
        self.community_id = community_id
        self.fault = fault  # Deterministic fault hook only used by scenario programs.

    def _fault(self, point):
        if self.fault is not None:
            self.fault(point)

    def _lock(self, initialize=False):
        if initialize:
            missing = []
            ancestor = self.directory
            while not ancestor.exists():
                missing.append(ancestor)
                ancestor = ancestor.parent
            self.directory.mkdir(parents=True, exist_ok=True)
            for directory in missing:
                fsync_directory(directory)
            if missing:
                fsync_directory(ancestor)
        if not self.directory.is_dir():
            unavailable("Shared channel directory is unavailable; collective work must pause")
        try:
            stream = (self.directory / "coordinator.lock").open("a+b")
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            return stream
        except OSError as error:
            unavailable("Cannot lock shared channel: " + str(error))

    def _replay(self, raw):
        if len(raw) > MAX_LOG_BYTES or not raw or not raw.endswith(b"\n"):
            unavailable("Journal is empty, truncated or exceeds its bounded capacity")
        state = None
        receipts = {}
        prefix_states = {}
        previous_hash = None
        try:
            for sequence, line in enumerate(raw.splitlines(), 1):
                event = decode(line)
                keys(event, ["schema", "sequence", "previous_hash", "contract_digest", "actor_id",
                             "operation", "request", "request_digest", "ack", "hash"])
                unsigned = {key: value for key, value in event.items() if key != "hash"}
                if (event["schema"] != "ara.community-event/v1" or
                        type(event["sequence"]) is not int or event["sequence"] != sequence or
                        event["previous_hash"] != previous_hash or event["hash"] != digest(unsigned) or
                        event["contract_digest"] != self.contract_digest):
                    unavailable("Journal hash chain, sequence or pinned contract mismatch")
                request_digest = digest({"actor_id": event["actor_id"], "operation": event["operation"],
                                         "request": event["request"]})
                if request_digest != event["request_digest"] or event["request"]["request_id"] in receipts:
                    unavailable("Invalid or duplicate committed request identity")
                if (sequence == 1) != (event["operation"] == "initialize"):
                    unavailable("Journal initialization order is corrupt")
                state, ack = apply(state, event["operation"], event["actor_id"], event["request"],
                                   sequence, self.contract_digest)
                if canonical(ack) != canonical(event["ack"]) or state["community_id"] != self.community_id:
                    unavailable("Committed acknowledgement or community identity is corrupt")
                receipt = {"digest": request_digest, "ack": ack}
                receipts[event["request"]["request_id"]] = receipt
                state["requests"] = copy.deepcopy(receipts)
                state["last_event_hash"] = event["hash"]
                previous_hash = event["hash"]
                prefix_states[sequence] = digest(state)
        except ChannelError as error:
            if error.unavailable:
                raise
            unavailable("Invalid committed transition: " + str(error))
        except (ValueError, UnicodeError, KeyError, TypeError) as error:
            unavailable("Malformed committed journal: " + str(error))
        return state, prefix_states

    def _read_log(self):
        try:
            return (self.directory / "events.jsonl").read_bytes()
        except OSError as error:
            unavailable("Cannot read committed journal: " + str(error))

    def _load(self, reconstruct=False):
        state, prefixes = self._replay(self._read_log())
        path = self.directory / "snapshot.json"
        try:
            snapshot = decode(path.read_bytes())
        except FileNotFoundError:
            if not reconstruct:
                unavailable("Snapshot missing; explicit request recovery is required")
            atomic_json(path, state)
            return state
        except (OSError, ValueError, UnicodeError) as error:
            unavailable("Snapshot corrupt or unavailable: " + str(error))
        if canonical(snapshot) == canonical(state):
            return state
        sequence = snapshot.get("sequence") if isinstance(snapshot, dict) else None
        if (not reconstruct or type(sequence) is not int or sequence not in prefixes or
                digest(snapshot) != prefixes[sequence]):
            unavailable("Snapshot does not match its complete committed journal prefix")
        atomic_json(path, state)
        return state

    def _repair_pending(self):
        path = self.directory / "pending-append.json"
        if not path.exists():
            return
        try:
            pending = decode(path.read_bytes())
            keys(pending, ["schema", "prefix_bytes", "prefix_digest", "event"])
            if pending["schema"] != "ara.community-pending/v1":
                unavailable("Invalid interrupted-append record")
            integer(pending["prefix_bytes"], "prefix_bytes", 0, MAX_LOG_BYTES)
            raw = self._read_log()
            prefix_size = pending["prefix_bytes"]
            prefix = raw[:prefix_size]
            expected_line = canonical(pending["event"]) + b"\n"
            if (len(prefix) != prefix_size or
                    "sha256:" + hashlib.sha256(prefix).hexdigest() != pending["prefix_digest"] or
                    not expected_line.startswith(raw[prefix_size:])):
                unavailable("Interrupted append cannot be recovered without discarding committed bytes")
            state, _ = self._replay(prefix + expected_line)
            snapshot_exists = True
            try:
                snapshot = decode((self.directory / "snapshot.json").read_bytes())
            except FileNotFoundError:
                snapshot_exists = False
            if snapshot_exists and canonical(snapshot) != canonical(state):
                if not prefix or canonical(snapshot) != canonical(self._replay(prefix)[0]):
                    unavailable("Interrupted append has a corrupt, not merely stale, snapshot")
            with (self.directory / "events.jsonl").open("ab") as stream:
                stream.write(expected_line[len(raw) - prefix_size:])
                stream.flush()
                os.fsync(stream.fileno())
            fsync_directory(self.directory)
            atomic_json(self.directory / "snapshot.json", state)
            remove_durable(path)
        except ChannelError as error:
            if error.unavailable:
                raise
            unavailable("Invalid interrupted append: " + str(error))
        except (OSError, ValueError, UnicodeError, KeyError, TypeError) as error:
            unavailable("Interrupted append unavailable: " + str(error))

    def call(self, operation, actor, request, repair_interrupted=False):
        if len(canonical(request)) > MAX_JSON_BYTES:
            reject("invalid_request", "Request exceeds bounded size")
        identity(actor, "actor_id")
        owned(request.get("request_id") if isinstance(request, dict) else None, actor, "request_id")
        normalized = "refresh" if operation == "snapshot" else operation
        lock = self._lock(normalized == "initialize")
        try:
            if normalized == "recover":
                keys(request, ["request_id"], ["request_digest"])
                if repair_interrupted:
                    self._repair_pending()
                elif (self.directory / "pending-append.json").exists():
                    unavailable("Interrupted append requires explicit --repair-interrupted recovery")
                state = self._load(reconstruct=True)
                if actor not in state["actors"]:
                    reject("unknown_actor", "Recovery caller is not admitted")
                receipt = state["requests"].get(request["request_id"])
                if receipt is None:
                    reject("unknown_request", "Request has no durable acknowledgement; do not assume publication")
                if "request_digest" in request and request["request_digest"] != receipt["digest"]:
                    reject("request_digest_mismatch", "Recovery request digest differs from committed request")
                return copy.deepcopy(receipt["ack"])
            if (self.directory / "pending-append.json").exists():
                unavailable("Interrupted append requires explicit request recovery; pause collective execution")
            log_path = self.directory / "events.jsonl"
            if normalized == "initialize" and not log_path.exists():
                if (self.directory / "snapshot.json").exists():
                    unavailable("Existing snapshot without journal must not be overwritten")
                state = None
                raw = b""
            else:
                state = self._load()
                raw = self._read_log()
            request_digest = digest({"actor_id": actor, "operation": normalized, "request": request})
            if state is not None:
                receipt = state["requests"].get(request["request_id"])
                if receipt is not None:
                    if receipt["digest"] != request_digest:
                        reject("request_digest_mismatch", "Stable request identity was reused with different content")
                    return copy.deepcopy(receipt["ack"])
                if normalized == "initialize":
                    reject("already_initialized", "Run configuration is immutable once initialized")
            sequence = 1 if state is None else state["sequence"] + 1
            next_state, ack = apply(copy.deepcopy(state), normalized, actor, request, sequence,
                                    self.contract_digest)
            if next_state["community_id"] != self.community_id:
                reject("invalid_config", "Configuration community differs from selected channel")
            event = {"schema": "ara.community-event/v1", "sequence": sequence,
                     "previous_hash": None if state is None else state["last_event_hash"],
                     "contract_digest": self.contract_digest, "actor_id": actor,
                     "operation": normalized, "request": copy.deepcopy(request),
                     "request_digest": request_digest, "ack": ack}
            event["hash"] = digest(event)
            line = canonical(event) + b"\n"
            if len(raw) + len(line) > MAX_LOG_BYTES:
                reject("capacity_exhausted", "Bounded journal capacity reached; no additional work may be committed")
            pending = {"schema": "ara.community-pending/v1", "prefix_bytes": len(raw),
                       "prefix_digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "event": event}
            # Create an empty durable log before the write-ahead record on first initialization.
            if state is None:
                with log_path.open("xb") as stream:
                    stream.flush()
                    os.fsync(stream.fileno())
                fsync_directory(self.directory)
            atomic_json(self.directory / "pending-append.json", pending)
            self._fault("before-append")
            with log_path.open("ab") as stream:
                halfway = len(line) // 2
                stream.write(line[:halfway])
                stream.flush()
                os.fsync(stream.fileno())
                self._fault("mid-append")
                stream.write(line[halfway:])
                stream.flush()
                os.fsync(stream.fileno())
            fsync_directory(self.directory)
            self._fault("after-append")
            next_state["requests"][request["request_id"]] = {"digest": request_digest, "ack": copy.deepcopy(ack)}
            next_state["last_event_hash"] = event["hash"]
            atomic_json(self.directory / "snapshot.json", next_state)
            self._fault("after-snapshot")
            remove_durable(self.directory / "pending-append.json")
            self._fault("lost-ack")
            return ack
        except OSError as error:
            unavailable("Coordinator filesystem unavailable: " + str(error))
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-root", required=True, help="Common runner root, outside every private fork")
    parser.add_argument("--community-id", required=True)
    parser.add_argument("--actor", required=True, help="Exact registered run-scoped caller process identity")
    parser.add_argument("--contract", type=Path,
                        default=Path(__file__).resolve().parent.parent / "collective-contract.json",
                        help="Pinned collective contract; its complete digest is frozen in the initial event")
    parser.add_argument("operation", choices=OPERATIONS,
                        help="snapshot is a billed durable refresh; recover retransmits its original receipt")
    parser.add_argument("--request", type=Path, help="JSON request file; omit to read JSON from stdin")
    parser.add_argument("--repair-interrupted", action="store_true",
                        help="recover only: finish a matching write-ahead append and rebuild its snapshot")
    args = parser.parse_args(argv)
    try:
        if args.repair_interrupted and args.operation != "recover":
            reject("invalid_request", "--repair-interrupted is restricted to explicit recovery")
        contract = read_json(args.contract)
        if args.request:
            request = read_json(args.request)
        else:
            raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
            if len(raw) > MAX_JSON_BYTES:
                reject("invalid_request", "Request exceeds bounded size")
            try:
                request = decode(raw)
            except (ValueError, UnicodeError) as error:
                reject("invalid_request", "Invalid request JSON: " + str(error))
        result = Channel(args.run_root, args.community_id, contract).call(
            args.operation, args.actor, request, args.repair_interrupted)
        print(canonical(result).decode("utf-8"))
        return 0
    except ChannelError as error:
        print(canonical({"schema": "ara.community-error/v1", "error": error.code,
                         "message": str(error), "pause_budget_consuming_work": error.unavailable}).decode("utf-8"))
        return 2 if error.unavailable else 1
    except OSError as error:
        print(canonical({"schema": "ara.community-error/v1", "error": "setup_failure",
                         "message": str(error), "pause_budget_consuming_work": True}).decode("utf-8"))
        return 2


if __name__ == "__main__":
    sys.exit(main())
