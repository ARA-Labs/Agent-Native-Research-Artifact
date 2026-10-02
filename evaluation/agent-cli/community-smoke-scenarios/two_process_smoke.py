#!/usr/bin/env python3
"""Run two independent fork processes against one shared channel and real ara.

Example:
  python3 two_process_smoke.py --ara /path/to/ara --artifact-dir /path/to/fixture \
    --run-root /tmp/community-smoke-new --selector N12

The fixture is copied administratively, never edited in place or through a
private knowledge-file shortcut. Both processes invoke actual ara open --json
and show --full --json. The driver records complete outputs and authoritative
administrative knowledge inventories, not invented CLI revision fields. It
makes no scientific decisions, merges, model calls or performance/score claims.
"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from community_channel import Channel, ChannelError, FAILURE_POLICY, canonical, digest, read_json


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE.parent / "collective-contract.json"
INVENTORY_ENCODING = "ara.runner-knowledge-inventory/v1: canonical sorted JSON of relative POSIX path, byte count and SHA256 of exact file bytes"
EXCLUDED = {".ara", ".git", "src", "evidence"}


def knowledge_inventory(fork, extra_paths):
    """Administrative revision authority, not an agent knowledge read surface."""
    paths = set()
    if (fork / "PAPER.md").is_file():
        paths.add(fork / "PAPER.md")
    for directory in ("logic", "trace", "staging", "rubric"):
        root = fork / directory
        if root.exists():
            paths.update(path for path in root.rglob("*") if path.is_file())
    for relative in extra_paths:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or set(path.parts) & EXCLUDED:
            raise ValueError("Explicit knowledge path is outside the registered knowledge boundary: " + relative)
        candidate = fork / path
        if not candidate.is_file():
            raise ValueError("Explicit knowledge path is not a regular file: " + relative)
        paths.add(candidate)
    inventory = []
    for path in sorted(paths, key=lambda path: path.relative_to(fork).as_posix()):
        relative = path.relative_to(fork)
        if set(relative.parts) & EXCLUDED or path.is_symlink():
            raise ValueError("Knowledge inventory refuses excluded or symlinked files: " + relative.as_posix())
        raw = path.read_bytes()
        inventory.append({"path": relative.as_posix(), "bytes": len(raw),
                          "sha256": "sha256:" + hashlib.sha256(raw).hexdigest()})
    if not inventory:
        raise ValueError("Fixture has no registered knowledge files")
    return {"encoding": INVENTORY_ENCODING, "files": inventory,
            "artifact_revision": digest({"encoding": INVENTORY_ENCODING, "files": inventory})}


def actual_reads(binary, fork, selector, source_identity, sequence, extra_paths):
    outputs = {}
    invocations = {}
    for name, arguments, expected in (
            ("open", ["open", "--json"], "ara.open/v1"),
            ("show", ["show", selector, "--full", "--json"], "ara.show/v1")):
        command = [binary, "-C", str(fork)] + arguments
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode != 0:
            raise RuntimeError("Actual ara invocation failed: " + json.dumps({"command": command,
                               "returncode": result.returncode, "stdout": result.stdout.decode(),
                               "stderr": result.stderr.decode()}))
        output = json.loads(result.stdout)
        if output.get("format") != expected:
            raise RuntimeError("Actual ara read returned unexpected wire format")
        outputs[name] = output
        invocations[name] = {"command": command, "returncode": result.returncode,
                             "stderr": result.stderr.decode(), "stdout": result.stdout.decode()}
    if not isinstance(outputs["open"].get("items"), list):
        raise RuntimeError("ara open response does not contain its native item list")
    if not isinstance(outputs["show"].get("entries"), list) or not outputs["show"]["entries"]:
        raise RuntimeError("ara show did not produce the requested full source object")
    inventory = knowledge_inventory(fork, extra_paths)
    frontier = []
    for item in outputs["open"]["items"]:
        native = item.get("id", item.get("key"))
        if not isinstance(native, str) or not native or not isinstance(item.get("source"), str):
            raise RuntimeError("Open item lacks its actual native identity or source")
        frontier.append({"category": "current-local", "source_identity": source_identity,
                         "artifact_revision": inventory["artifact_revision"],
                         "intention_snapshot_sequence": sequence,
                         "native_refs": [{"source_identity": source_identity, "native_ref": native}],
                         "source_file": item["source"], "native_object": copy.deepcopy(item)})
    return {"actor_source_identity": source_identity, "fork": str(fork),
            "knowledge_inventory": inventory, "invocations": invocations, "outputs": outputs,
            "frontier": frontier, "remote_coverage_claimed": False}


def worker(args):
    contract = read_json(args.contract)
    channel = Channel(args.run_root, args.community_id, contract)
    sequence = None
    observed_view = None
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if message["kind"] == "stop":
                return 0
            if message["kind"] == "read":
                payload = actual_reads(args.ara, args.fork, args.selector, args.source_identity,
                                       sequence, args.knowledge_path)
                payload["observed_intention_snapshot"] = copy.deepcopy(observed_view)
                payload["remote_intention_context"] = []
                if observed_view is not None:
                    for record in observed_view["intentions"].values():
                        if record["source_identity"] == args.source_identity:
                            continue
                        category = "remote-history"
                        if record["state"] == "expired":
                            category = "stale-remote-intention"
                        elif record["state"] in ("planned", "active"):
                            category = ("active-remote-intention" if
                                        observed_view["round"] <= record["expires_after_round"] else
                                        "stale-remote-intention")
                        payload["remote_intention_context"].append({
                            "category": category, "source_identity": record["source_identity"],
                            "artifact_revision": record["artifact_revision"],
                            "native_refs": copy.deepcopy(record["native_refs"]),
                            "intention_snapshot_sequence": observed_view["sequence"],
                            "intention_snapshot_round": observed_view["round"],
                            "publisher_declared_intention": copy.deepcopy(record),
                            "verified_full_source_in_this_fork": False,
                            "scientific_coverage_claimed": False})
            elif message["kind"] == "call":
                payload = channel.call(message["operation"], args.actor, message["request"],
                                       message.get("repair_interrupted", False))
                if sequence is None or payload["sequence"] >= sequence:
                    sequence = payload["sequence"]
                    if "view" in payload:
                        observed_view = copy.deepcopy(payload["view"])
            else:
                raise ValueError("Unknown deterministic scenario instruction")
            response = {"ok": True, "actor_id": args.actor, "pid": os.getpid(),
                        "channel_directory": str(channel.directory), "payload": payload}
        except ChannelError as error:
            response = {"ok": False, "actor_id": args.actor, "pid": os.getpid(),
                        "channel_directory": str(channel.directory), "error": error.code,
                        "message": str(error), "pause_budget_consuming_work": error.unavailable}
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            response = {"ok": False, "actor_id": args.actor, "pid": os.getpid(),
                        "error": "scenario_failure", "message": str(error)}
        print(canonical(response).decode(), flush=True)
    return 0


class ForkProcess:
    def __init__(self, args, actor, source_identity, fork):
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--ara", args.ara,
                   "--run-root", str(args.run_root), "--community-id", args.community_id,
                   "--contract", str(args.contract), "--actor", actor, "--source-identity", source_identity,
                   "--fork", str(fork), "--selector", args.selector]
        for relative in args.knowledge_path:
            command.extend(["--knowledge-path", relative])
        self.actor = actor
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, bufsize=1)
        self.frames = []

    def send(self, message):
        self.process.stdin.write(canonical(message).decode() + "\n")
        self.process.stdin.flush()

    def receive(self):
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Fork process stopped before response: " + self.process.stderr.read())
        frame = json.loads(line)
        self.frames.append(frame)
        return frame

    def message(self, message, expected_error=None):
        self.send(message)
        frame = self.receive()
        if expected_error is not None:
            if frame.get("ok") or frame.get("error") != expected_error:
                raise RuntimeError("Expected actual channel transition " + expected_error + ": " + json.dumps(frame))
        elif not frame.get("ok"):
            raise RuntimeError("Scenario operation failed: " + json.dumps(frame))
        return frame

    def call(self, operation, request, expected_error=None):
        return self.message({"kind": "call", "operation": operation, "request": request}, expected_error)

    def close(self):
        if self.process.poll() is None:
            try:
                self.send({"kind": "stop"})
                self.process.stdin.close()
                self.process.wait(timeout=15)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait()
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream and not stream.closed:
                stream.close()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def scenario(args):
    if args.run_root.exists():
        raise ValueError("--run-root must be new; existing run data is never overwritten")
    if not args.artifact_dir or not args.artifact_dir.is_dir():
        raise ValueError("--artifact-dir must select a real existing ARA fixture")
    args.artifact_dir = args.artifact_dir.resolve()
    if args.artifact_dir == args.run_root or args.artifact_dir in args.run_root.parents:
        raise ValueError("--run-root must be outside the original fixture knowledge tree")
    args.run_root.mkdir(parents=True)
    forks = {}
    for actor in ("alice", "bob"):
        fork = args.run_root / "forks" / actor / "ara"
        shutil.copytree(args.artifact_dir, fork, ignore=shutil.ignore_patterns(".git", ".ara"))
        forks[actor] = fork
    sources = {actor: "fixture-fork-" + actor for actor in forks}
    processes = {actor: ForkProcess(args, actor, sources[actor], forks[actor]) for actor in forks}
    steps = []
    counters = {actor: 0 for actor in forks}
    current = None
    initial_inventory = {}

    def request(actor, **fields):
        counters[actor] += 1
        value = {"request_id": actor + ":smoke-" + str(counters[actor])}
        if fields:
            value.update(observed_sequence=current["sequence"], observed_round=current["round"])
            value.update(fields)
        return value

    def call(actor, operation, payload, expected_error=None):
        nonlocal current
        frame = processes[actor].call(operation, payload, expected_error)
        steps.append({"actor_id": actor, "operation": operation, "request": payload, "response": frame})
        if frame["ok"]:
            current = frame["payload"]
            return current
        return frame

    def refresh(actor):
        return call(actor, "refresh", request(actor))

    def change(actor, intention_id, revision, next_state, **fields):
        return call(actor, "refresh-intention", request(actor, intention_id=intention_id,
                    expected_revision=revision, state=next_state, **fields))

    def finish_round():
        first = call("alice", "finish-round", dict(request("alice"), observed_sequence=current["sequence"], observed_round=current["round"]))
        first_round = first["round"]
        second = call("bob", "finish-round", dict(request("bob"), observed_sequence=current["sequence"], observed_round=current["round"]))
        require(second["round"] == first_round + 1, "Logical round did not wait for both real actors")
        return second

    try:
        # Launch both actual reads before collecting either response: distinct live processes.
        for process in processes.values():
            process.send({"kind": "read"})
        initial_reads = {actor: process.receive() for actor, process in processes.items()}
        for actor, frame in initial_reads.items():
            require(frame["ok"], "Initial real ara read failed: " + json.dumps(frame))
            initial_inventory[actor] = frame["payload"]["knowledge_inventory"]
        require(initial_reads["alice"]["pid"] != initial_reads["bob"]["pid"], "Forks are not independent processes")
        require(initial_reads["alice"]["channel_directory"] == initial_reads["bob"]["channel_directory"], "Forks do not share one channel")
        config = {"schema": "ara.community-run/v1", "run_id": "two-process-smoke",
                  "community_id": args.community_id, "coordinator_id": "alice",
                  "actors": [{"actor_id": actor, "source_identity": sources[actor],
                              "role": "fork-pm" if actor == "alice" else "contributor"} for actor in forks],
                  "allocation_per_actor": 100, "refresh_cadence_rounds": 1,
                  "expiry_rounds": 1, "max_rounds": 8, "failure_policy": copy.deepcopy(FAILURE_POLICY)}
        call("alice", "initialize", {"request_id": "alice:initialize", "config": config})
        refresh("alice")
        signature = digest({"action": "read-complete-native-source", "selector": args.selector,
                            "fixture_revision": initial_inventory["alice"]["artifact_revision"]})

        def planned(actor, local):
            return {"intention_id": actor + ":" + local, "source_identity": sources[actor],
                    "artifact_revision": initial_inventory[actor]["artifact_revision"],
                    "native_refs": [{"source_identity": sources[actor], "native_ref": args.selector}],
                    "action": "Read the complete native source through actual ara show --full",
                    "question": "Can two independent fork processes share durable advisory context?",
                    "experiment_signature": signature, "verification_of": None, "verification_rationale": None,
                    "state": "planned", "budget_reserved": 5, "result_refs": []}

        alice = call("alice", "publish", request("alice", expected_revision=0, intention=planned("alice", "read")))
        bob_view = refresh("bob")
        require(bob_view["view"]["intentions"]["alice:read"]["published_sequence"] == alice["sequence"],
                "Actor B did not observe actor A's actual durable publication before its choice")
        bob_item = planned("bob", "read")
        bob_item["verification_of"] = {"source_identity": sources["alice"], "intention_id": "alice:read", "revision": 1}
        bob_item["verification_rationale"] = "Deliberate independent fixture-source read, not exclusion or proof of scientific agreement"
        bob = call("bob", "publish", request("bob", expected_revision=0, intention=bob_item))
        require(len(bob["overlaps"]) == 1 and bob["overlaps"][0]["judgment_required"], "Fresh overlap was not returned for explicit judgment")
        refresh("alice")
        active = change("alice", "alice:read", alice["intention"]["revision"], "active")
        execution = call("alice", "execute", request("alice", intention_id="alice:read",
                         expected_revision=active["intention"]["revision"], research_units=1))
        channel_directory = Path(initial_reads["alice"]["channel_directory"])
        log = channel_directory / "events.jsonl"
        disabled = channel_directory / "events.jsonl.outage"
        log.rename(disabled)
        outage = []
        try:
            outage.append(call("alice", "execute", request("alice", intention_id="alice:read",
                               expected_revision=execution["intention"]["revision"], research_units=1), "channel_unavailable"))
            outage.append(call("bob", "refresh", request("bob"), "channel_unavailable"))
            require(all(frame["pause_budget_consuming_work"] for frame in outage), "Outage silently allowed collective work")
            offline_reads = {actor: process.message({"kind": "read"}) for actor, process in processes.items()}
            require(all(frame["ok"] for frame in offline_reads.values()), "Offline ara reads failed during channel outage")
        finally:
            disabled.rename(log)
        restored = refresh("alice")
        require(restored["view"]["actors"]["alice"]["research_used"] == 1, "Unavailable execution consumed hidden research budget")
        require(restored["view"]["intentions"]["alice:read"]["revision"] == execution["intention"]["revision"], "Outage changed retained intention history")
        completed_request = request("alice", intention_id="alice:read", expected_revision=execution["intention"]["revision"],
                                    state="completed", result_refs=[{"source_identity": sources["alice"], "native_ref": args.selector}])
        completed = call("alice", "refresh-intention", completed_request)
        refresh("bob")
        active_bob = change("bob", "bob:read", bob["intention"]["revision"], "active")
        exec_bob = call("bob", "execute", request("bob", intention_id="bob:read",
                        expected_revision=active_bob["intention"]["revision"], research_units=1))
        change("bob", "bob:read", exec_bob["intention"]["revision"], "completed",
               result_refs=[{"source_identity": sources["bob"], "native_ref": args.selector}])
        # Recovery is receipt retransmission, not a new round/sequence or fresh view.
        recovered_frame = processes["alice"].call("recover", {"request_id": completed_request["request_id"]})
        require(recovered_frame["ok"] and recovered_frame["payload"] == completed, "Original durable acknowledgement was not recovered")
        steps.append({"actor_id": "alice", "operation": "recover", "response": recovered_frame})
        refresh("alice")
        pending = call("alice", "publish", request("alice", expected_revision=0, intention=planned("alice", "expiry")))
        finish_round()  # round two, still fresh because round == expires_after_round
        refresh("alice")
        extended = change("alice", "alice:expiry", pending["intention"]["revision"], "planned")
        require(extended["intention"]["expires_after_round"] == 3, "Logical refresh did not extend whole-round expiry")
        seen_extended = refresh("bob")
        require(seen_extended["view"]["intentions"]["alice:expiry"]["revision"] == 2, "Other process did not observe intention refresh")
        finish_round()  # round three is still fresh
        expired_ack = finish_round()  # round four exceeds expires_after_round
        require(expired_ack["view"]["intentions"]["alice:expiry"]["state"] == "expired", "Unrefreshed advisory intention did not expire")
        final_view = refresh("bob")
        final_reads = {actor: process.message({"kind": "read"}) for actor, process in processes.items()}
        for actor, frame in final_reads.items():
            require(frame["payload"]["knowledge_inventory"] == initial_inventory[actor], "Scenario changed private knowledge files")
            require(all(item["source_identity"] == sources[actor] and
                        item["intention_snapshot_sequence"] is not None for item in frame["payload"]["frontier"]),
                    "Frontier lost authoritative source or observed snapshot sequence")
        remote_expiry = [item for item in final_reads["bob"]["payload"]["remote_intention_context"]
                         if item["publisher_declared_intention"]["intention_id"] == "alice:expiry"]
        require(len(remote_expiry) == 1 and remote_expiry[0]["category"] == "stale-remote-intention" and
                remote_expiry[0]["source_identity"] == sources["alice"] and
                remote_expiry[0]["intention_snapshot_sequence"] == final_view["sequence"] and
                remote_expiry[0]["scientific_coverage_claimed"] is False,
                "Source-qualified remote expiry was not retained as advisory stale context")
        snapshot = json.loads((channel_directory / "snapshot.json").read_text())
        events = [json.loads(line) for line in log.read_text().splitlines()]
        require(snapshot["sequence"] == events[-1]["sequence"] == final_view["sequence"], "Produced snapshot/log acknowledgement disagree")
        require([event["sequence"] for event in events] == list(range(1, len(events) + 1)), "Durable coordination sequence contains a gap")
        require([history["state"] for history in snapshot["intentions"]["alice:expiry"]["history"]] ==
                ["planned", "planned", "expired"], "Refresh and expiry did not preserve generated state history")
        for actor in snapshot["actors"].values():
            require(actor["remaining"] + actor["coordination_used"] + actor["research_used"] == 100,
                    "Coordination and research escaped the same actor allocation")
        result = {"schema": "ara.community-two-process-smoke/v1", "status": "exercised",
                  "scope": "one-host deterministic protocol consumer, not scored experiments",
                  "external_harness_and_scored_experiments": "deferred",
                  "merge_proof": "not performed by this driver; parent combines the real merge scenario",
                  "config": config, "initial_reads": initial_reads, "offline_reads": offline_reads,
                  "final_reads": final_reads, "steps": steps, "snapshot": snapshot, "events": events,
                  "scientific_outcome": "not evaluated", "approval_claimed": False}
        (args.run_root / "scenario-result.json").write_bytes(canonical(result) + b"\n")
        for actor, process in processes.items():
            (args.run_root / (actor + "-frames.jsonl")).write_bytes(b"".join(canonical(frame) + b"\n" for frame in process.frames))
        print(canonical({"status": "exercised", "result": str(args.run_root / "scenario-result.json"),
                         "fork_pids": {actor: frame["pid"] for actor, frame in initial_reads.items()},
                         "channel_directory": str(channel_directory), "sequence": snapshot["sequence"],
                         "round": snapshot["round"], "expired_intention": "alice:expiry",
                         "external_harness_and_scored_experiments": "deferred"}).decode())
        return 0
    finally:
        for process in processes.values():
            process.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ara", required=True, help="Actual ara executable, never a mock")
    parser.add_argument("--artifact-dir", type=Path, help="Real fixture copied unchanged into two independent forks")
    parser.add_argument("--run-root", type=Path, required=True, help="New common output/run directory")
    parser.add_argument("--community-id", default="community-smoke")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--selector", default="N12", help="Native selector actually readable in the supplied fixture")
    parser.add_argument("--knowledge-path", action="append", default=[], help="Additional explicitly registered knowledge file")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--actor", help=argparse.SUPPRESS)
    parser.add_argument("--source-identity", help=argparse.SUPPRESS)
    parser.add_argument("--fork", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        executable = shutil.which(args.ara)
        if executable is None:
            raise ValueError("Actual --ara executable is unavailable")
        args.ara = str(Path(executable).resolve())
        args.run_root = args.run_root.resolve()
        args.contract = args.contract.resolve()
        if args.worker:
            if not args.actor or not args.source_identity or not args.fork:
                raise ValueError("Internal worker requires registered actor, source and fork")
            return worker(args)
        return scenario(args)
    except (ChannelError, OSError, ValueError, RuntimeError) as error:
        print(canonical({"schema": "ara.community-smoke-error/v1", "status": "failed", "message": str(error),
                         "external_harness_and_scored_experiments": "deferred"}).decode())
        return 1


if __name__ == "__main__":
    sys.exit(main())
