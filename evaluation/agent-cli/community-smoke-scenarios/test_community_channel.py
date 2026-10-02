"""Generated-output scenarios. Run only after the pinned contract has landed.

These tests exercise this actual coordinator and subprocesses, not an external
scored harness, scientific outcome or approved experimental threshold.
"""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from community_channel import Channel, ChannelError, FAILURE_POLICY, canonical, digest


HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "collective-contract.json"
UTILITY = HERE / "community_channel.py"


def run_config(allocation=100, expiry=1, max_rounds=8):
    return {"schema": "ara.community-run/v1", "run_id": "deterministic-smoke",
            "community_id": "community", "coordinator_id": "alice",
            "actors": [{"actor_id": "alice", "source_identity": "fork-alice", "role": "fork-pm"},
                       {"actor_id": "bob", "source_identity": "fork-bob", "role": "contributor"}],
            "allocation_per_actor": allocation, "refresh_cadence_rounds": 1,
            "expiry_rounds": expiry, "max_rounds": max_rounds,
            "failure_policy": copy.deepcopy(FAILURE_POLICY)}


def intention(actor, local="work", signature="sha256:identical-configuration"):
    return {"intention_id": actor + ":" + local, "source_identity": "fork-" + actor,
            "artifact_revision": "sha256:fixture-revision",
            "native_refs": [{"source_identity": "fork-" + actor, "native_ref": "trace/exploration_tree.yaml:N12"}],
            "action": "Run the bounded fixture action", "question": "Does the fixture action preserve its recorded source?",
            "experiment_signature": signature, "verification_of": None, "verification_rationale": None,
            "state": "planned", "budget_reserved": 10, "result_refs": []}


class CommunityScenarios(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.contract = json.loads(CONTRACT.read_text())
        self.channel = Channel(self.root, "community", self.contract)
        self.count = 0
        self.initialize()

    def initialize(self, config=None):
        return self.channel.call("initialize", "alice", {"request_id": "alice:init", "config": config or run_config()})

    def state(self):
        return json.loads((self.channel.directory / "snapshot.json").read_text())

    def events(self):
        return [json.loads(line) for line in (self.channel.directory / "events.jsonl").read_text().splitlines()]

    def request(self, actor, **fields):
        self.count += 1
        result = {"request_id": actor + ":request-" + str(self.count)}
        if fields:
            state = self.state()
            result.update(observed_sequence=state["sequence"], observed_round=state["round"])
            result.update(fields)
        return result

    def refresh(self, actor):
        return self.channel.call("refresh", actor, self.request(actor))

    def publish(self, actor, item=None):
        self.refresh(actor)
        return self.channel.call("publish", actor, self.request(actor, expected_revision=0,
                                                                 intention=item or intention(actor)))

    def change(self, actor, intention_id, state, **fields):
        revision = self.state()["intentions"][intention_id]["revision"]
        return self.channel.call("refresh-intention", actor,
                                 self.request(actor, intention_id=intention_id, expected_revision=revision,
                                              state=state, **fields))

    def finish(self, actor):
        # Finish is a coordination-only allotted turn when no research was selected.
        state = self.state()
        request = self.request(actor)
        request.update(observed_sequence=state["sequence"], observed_round=state["round"])
        return self.channel.call("finish-round", actor, request)

    def round(self):
        self.finish("alice")
        return self.finish("bob")

    def assert_rejected_unchanged(self, code, operation, actor, request):
        before_state = (self.channel.directory / "snapshot.json").read_bytes()
        before_log = (self.channel.directory / "events.jsonl").read_bytes()
        with self.assertRaises(ChannelError) as raised:
            self.channel.call(operation, actor, request)
        self.assertEqual(raised.exception.code, code)
        self.assertEqual((self.channel.directory / "snapshot.json").read_bytes(), before_state)
        self.assertEqual((self.channel.directory / "events.jsonl").read_bytes(), before_log)

    def cli(self, operation, actor, request):
        return subprocess.run([sys.executable, str(UTILITY), "--run-root", str(self.root),
                               "--community-id", "community", "--actor", actor,
                               "--contract", str(CONTRACT), operation], input=canonical(request),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def crash_process(self, point, operation, actor, request):
        request_file = self.root / "crash-request.json"
        request_file.write_bytes(canonical(request))
        code = ("import json,os,sys; from pathlib import Path; "
                "from community_channel import Channel; "
                "root,contract,request,point,op,actor=sys.argv[1:]; "
                "fault=lambda p: os._exit(73) if p==point else None; "
                "c=Channel(root,'community',json.loads(Path(contract).read_text()),fault=fault); "
                "c.call(op,actor,json.loads(Path(request).read_text()))")
        result = subprocess.run([sys.executable, "-c", code, str(self.root), str(CONTRACT),
                                 str(request_file), point, operation, actor], cwd=HERE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(result.returncode, 73, result.stderr.decode())

    def test_generated_completion_preserves_source_history_and_joint_budget(self):
        published = self.publish("alice")
        self.assertEqual(published["intention"]["revision"], 1)
        self.assertEqual(published["intention"]["state"], "planned")
        active = self.change("alice", "alice:work", "active")
        request = self.request("alice", intention_id="alice:work", expected_revision=active["intention"]["revision"],
                               research_units=3)
        execution = self.channel.call("execute", "alice", request)
        completed = self.change("alice", "alice:work", "completed",
                                result_refs=[{"source_identity": "fork-alice", "native_ref": "trace/exploration_tree.yaml:N62"}])
        state = self.state()
        record = state["intentions"]["alice:work"]
        self.assertEqual([h["state"] for h in record["history"]], ["planned", "active", "active", "completed"])
        self.assertEqual([h["revision"] for h in record["history"]], [1, 2, 3, 4])
        self.assertEqual(record["budget_used"], 3)
        self.assertEqual(record["native_refs"], intention("alice")["native_refs"])
        self.assertEqual(record["artifact_revision"], "sha256:fixture-revision")
        self.assertEqual(record["result_refs"], completed["intention"]["result_refs"])
        self.assertEqual(execution["accounting"]["research_used"], 3)
        self.assertEqual(state["actors"]["alice"]["coordination_used"], 6)
        self.assertEqual(state["actors"]["alice"]["remaining"], 91)
        events = self.events()
        self.assertEqual([event["sequence"] for event in events], list(range(1, 7)))
        self.assertEqual(events[-1]["ack"], completed)
        self.assertEqual(events[-1]["hash"], state["last_event_hash"])
        self.assertEqual(state["requests"][request["request_id"]]["ack"], execution)
        self.assertEqual(events[-1]["previous_hash"], events[-2]["hash"])

    def test_actor_ownership_cas_and_registered_fork_are_enforced(self):
        published = self.publish("alice")
        self.refresh("bob")
        request = self.request("bob", intention_id="alice:work", expected_revision=1, state="abandoned")
        self.assert_rejected_unchanged("actor_ownership", "refresh-intention", "bob", request)
        request = self.request("alice", intention_id="alice:work", expected_revision=0, state="active")
        self.assert_rejected_unchanged("invalid_request", "refresh-intention", "alice", request)
        request["expected_revision"] = 2
        self.assert_rejected_unchanged("stale_revision", "refresh-intention", "alice", request)
        request["expected_revision"] = 1
        request["observed_sequence"] = published["sequence"]
        self.assert_rejected_unchanged("stale_snapshot", "refresh-intention", "alice", request)
        request["observed_sequence"] = self.state()["sequence"]
        request["observed_round"] = 2
        self.assert_rejected_unchanged("stale_snapshot", "refresh-intention", "alice", request)
        foreign = intention("bob", "foreign")
        foreign["source_identity"] = "fork-alice"
        self.assert_rejected_unchanged("source_identity", "publish", "bob",
                                       self.request("bob", expected_revision=0, intention=foreign))
        self.assert_rejected_unchanged("unknown_actor", "refresh", "eve", {"request_id": "eve:refresh"})
        self.assert_rejected_unchanged("actor_ownership", "recover", "bob", {"request_id": "alice:init"})

    def test_request_identity_returns_original_ack_and_rejects_changed_digest(self):
        self.refresh("alice")
        request = self.request("alice", expected_revision=0, intention=intention("alice"))
        original = self.channel.call("publish", "alice", request)
        self.refresh("bob")
        before = self.state()
        self.assertEqual(self.channel.call("publish", "alice", request), original)
        self.assertEqual(self.state(), before)
        recovered = self.channel.call("recover", "alice", {"request_id": request["request_id"],
                       "request_digest": digest({"actor_id": "alice", "operation": "publish", "request": request})})
        self.assertEqual(recovered, original)
        changed = copy.deepcopy(request)
        changed["intention"]["question"] = "Different research question"
        self.assert_rejected_unchanged("request_digest_mismatch", "publish", "alice", changed)
        self.assert_rejected_unchanged("request_digest_mismatch", "recover", "alice",
                                       {"request_id": request["request_id"], "request_digest": "sha256:wrong"})
        self.assert_rejected_unchanged("unknown_request", "recover", "alice", {"request_id": "alice:never-accepted"})

    def test_two_real_processes_publish_cas_then_explicitly_refresh_and_reconsider(self):
        self.refresh("alice")
        self.refresh("bob")
        first = self.request("alice", expected_revision=0, intention=intention("alice"))
        second = self.request("bob", expected_revision=0, intention=intention("bob"))
        processes = []
        for actor, request in (("alice", first), ("bob", second)):
            process = subprocess.Popen([sys.executable, str(UTILITY), "--run-root", str(self.root),
                                        "--community-id", "community", "--actor", actor,
                                        "--contract", str(CONTRACT), "publish"],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.stdin.write(canonical(request))
            process.stdin.close()
            processes.append(process)
        responses = []
        for process in processes:
            output = process.stdout.read()
            errors = process.stderr.read()
            process.wait()
            process.stdout.close()
            process.stderr.close()
            self.assertFalse(errors, errors.decode())
            responses.append((process.returncode, json.loads(output)))
        self.assertEqual(sorted(code for code, _ in responses), [0, 1])
        loser = 0 if responses[0][0] == 1 else 1
        actor = ["alice", "bob"][loser]
        self.assertEqual(responses[loser][1]["error"], "stale_snapshot")
        refreshed = self.cli("refresh", actor, {"request_id": actor + ":reconsider"})
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr.decode())
        view = json.loads(refreshed.stdout)
        winner = ["bob", "alice"][loser]
        self.assertIn(winner + ":work", view["view"]["intentions"])
        request = self.request(actor, expected_revision=0, intention=intention(actor))
        accepted = self.cli("publish", actor, request)
        self.assertEqual(accepted.returncode, 0, accepted.stdout.decode())
        ack = json.loads(accepted.stdout)
        self.assertEqual(set(self.state()["intentions"]), {"alice:work", "bob:work"})
        self.assertEqual(len(ack["overlaps"]), 1)
        self.assertTrue(ack["overlaps"][0]["judgment_required"])
        self.assertFalse(ack["overlaps"][0]["exclusive_lock"])
        self.assertEqual({owner["actor_id"] for owner in ack["overlaps"][0]["owners"]}, {"alice", "bob"})

    def test_refresh_extends_logical_expiry_and_preserves_planned_active_history(self):
        self.publish("alice")
        self.publish("bob", intention("bob", signature="other"))
        self.change("alice", "alice:work", "active")
        self.assertEqual(self.finish("alice")["round"], 1)
        self.assertEqual(self.finish("bob")["round"], 2)
        self.assertEqual(self.state()["intentions"]["bob:work"]["state"], "planned")
        self.refresh("alice")
        refreshed = self.change("alice", "alice:work", "active")
        self.assertEqual(refreshed["intention"]["expires_after_round"], 3)
        self.round()
        state = self.state()
        self.assertEqual(state["round"], 3)
        self.assertEqual(state["intentions"]["bob:work"]["state"], "expired")
        self.assertEqual(state["intentions"]["alice:work"]["state"], "active")
        self.round()
        record = self.state()["intentions"]["alice:work"]
        self.assertEqual(record["state"], "expired")
        self.assertEqual([h["state"] for h in record["history"]], ["planned", "active", "active", "expired"])
        self.assertEqual(record["history"][-1]["operation"], "logical-expiry")
        self.assertEqual(record["history"][-1]["event_round"], 4)
        self.refresh("alice")
        self.assert_rejected_unchanged("invalid_transition", "refresh-intention", "alice",
                                       self.request("alice", intention_id="alice:work", expected_revision=record["revision"], state="active"))

    def test_lost_ack_after_commit_is_recovered_without_duplicate_event(self):
        self.refresh("alice")
        request = self.request("alice", expected_revision=0, intention=intention("alice"))
        self.crash_process("lost-ack", "publish", "alice", request)
        durable = self.events()[-1]["ack"]
        before = self.state()
        self.assertEqual(self.channel.call("recover", "alice", {"request_id": request["request_id"]}), durable)
        self.assertEqual(self.channel.call("publish", "alice", request), durable)
        self.assertEqual(self.state(), before)
        self.assertEqual(sum(event["request"]["request_id"] == request["request_id"] for event in self.events()), 1)

    def test_crash_append_snapshot_windows_recover_all_accepted_history(self):
        for index, point in enumerate(("before-append", "mid-append", "after-append", "after-snapshot")):
            with self.subTest(point=point):
                self.refresh("alice")
                request = self.request("alice", expected_revision=0, intention=intention("alice", "crash-" + str(index)))
                before_events = self.events()
                before_bytes = (self.channel.directory / "events.jsonl").read_bytes()
                self.crash_process(point, "publish", "alice", request)
                self.assert_rejected_unchanged("channel_unavailable", "refresh", "bob", self.request("bob"))
                recovered = self.channel.call("recover", "alice", {"request_id": request["request_id"]}, repair_interrupted=True)
                events = self.events()
                self.assertEqual(events[:-1], before_events)
                self.assertTrue((self.channel.directory / "events.jsonl").read_bytes().startswith(before_bytes))
                self.assertEqual(events[-1]["ack"], recovered)
                self.assertEqual(self.state()["requests"][request["request_id"]]["ack"], recovered)
                self.assertEqual(self.state()["intentions"]["alice:crash-" + str(index)]["revision"], 1)
                self.assertFalse((self.channel.directory / "pending-append.json").exists())
                self.assertEqual(self.channel.call("publish", "alice", request), recovered)

    def test_corrupt_interrupted_append_never_discards_complete_accepted_prefix(self):
        self.publish("bob", intention("bob", signature="other"))
        self.refresh("alice")
        before = self.state()
        accepted = (self.channel.directory / "events.jsonl").read_bytes()
        request = self.request("alice", expected_revision=0, intention=intention("alice"))
        self.crash_process("mid-append", "publish", "alice", request)
        path = self.channel.directory / "events.jsonl"
        partial = path.read_bytes()
        self.assertTrue(partial.startswith(accepted))
        corrupt = partial[:-1] + (b"!" if partial[-1:] != b"!" else b"?")
        path.write_bytes(corrupt)
        with self.assertRaises(ChannelError) as raised:
            self.channel.call("recover", "alice", {"request_id": request["request_id"]}, repair_interrupted=True)
        self.assertEqual(raised.exception.code, "channel_unavailable")
        self.assertEqual(path.read_bytes(), corrupt)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.state()["intentions"]["bob:work"]["state"], "planned")

    def test_snapshot_reconstruction_requires_valid_committed_prefix(self):
        previous = (self.channel.directory / "snapshot.json").read_bytes()
        refreshed = self.refresh("alice")
        (self.channel.directory / "snapshot.json").write_bytes(previous)
        self.assert_rejected_unchanged("channel_unavailable", "refresh", "bob", self.request("bob"))
        recovered = self.channel.call("recover", "alice", {"request_id": refreshed["request_id"]})
        self.assertEqual(recovered, refreshed)
        self.assertEqual(self.state()["sequence"], refreshed["sequence"])
        (self.channel.directory / "snapshot.json").unlink()
        self.assertEqual(self.channel.call("recover", "alice", {"request_id": refreshed["request_id"]}), refreshed)
        malformed = self.state()
        malformed["actors"]["alice"]["remaining"] += 50
        (self.channel.directory / "snapshot.json").write_bytes(canonical(malformed))
        self.assert_rejected_unchanged("channel_unavailable", "recover", "alice", {"request_id": refreshed["request_id"]})

    def test_malformed_corrupt_and_truncated_committed_journal_pause_without_budget(self):
        self.publish("alice")
        path = self.channel.directory / "events.jsonl"
        original = path.read_bytes()
        before = self.state()
        corruptions = [original[:-5], original + b"{not-json}\n", original + b"\n"]
        events = self.events()
        changed = copy.deepcopy(events)
        changed[-1]["ack"]["sequence"] += 1
        corruptions.append(b"".join(canonical(event) + b"\n" for event in changed))
        for raw in corruptions:
            with self.subTest(raw_size=len(raw)):
                path.write_bytes(raw)
                request = self.request("bob")
                response = self.cli("refresh", "bob", request)
                self.assertEqual(response.returncode, 2, response.stdout.decode())
                error = json.loads(response.stdout)
                self.assertEqual(error["error"], "channel_unavailable")
                self.assertTrue(error["pause_budget_consuming_work"])
                self.assertEqual(self.state(), before)
                with self.assertRaises(ChannelError) as raised:
                    self.channel.call("recover", "alice", {"request_id": "alice:init"}, repair_interrupted=True)
                self.assertEqual(raised.exception.code, "channel_unavailable")
                self.assertEqual(path.read_bytes(), raw)
        path.write_bytes(original)
        path.rename(path.with_suffix(".disabled"))
        response = self.cli("execute", "alice", self.request("alice", intention_id="alice:work", expected_revision=1, research_units=1))
        self.assertEqual(response.returncode, 2)
        self.assertEqual(self.state(), before)
        path.with_suffix(".disabled").rename(path)
        self.assertEqual(self.refresh("bob")["view"]["intentions"]["alice:work"]["state"], "planned")

    def test_intentional_verification_is_advisory_and_retains_source_revision(self):
        original = self.publish("alice")
        item = intention("bob")
        item["verification_of"] = {"source_identity": "fork-alice", "intention_id": "alice:work", "revision": 1}
        self.refresh("bob")
        self.assert_rejected_unchanged("invalid_verification", "publish", "bob",
                                       self.request("bob", expected_revision=0, intention=item))
        item["verification_rationale"] = "Independent verification of the same source-grounded configuration"
        verification = self.channel.call("publish", "bob", self.request("bob", expected_revision=0, intention=item))
        self.assertEqual(verification["intention"]["verification_of"]["revision"], original["intention"]["revision"])
        self.assertEqual(verification["intention"]["verification_rationale"], item["verification_rationale"])
        self.assertEqual(verification["overlaps"][0]["owners"][1]["verification_of"], item["verification_of"])
        self.assertEqual(self.state()["intentions"]["alice:work"]["state"], "planned")
        self.assertNotIn("scientific_outcome", verification)

    def test_exhaustion_and_registered_failure_use_no_extra_actor_allocation(self):
        separate = self.root / "finite"
        self.channel = Channel(separate, "community", self.contract)
        self.initialize(run_config(allocation=8))
        item = intention("bob")
        item["budget_reserved"] = 3
        self.publish("bob", item)
        active = self.change("bob", "bob:work", "active")
        self.channel.call("execute", "bob", self.request("bob", intention_id="bob:work",
                          expected_revision=active["intention"]["revision"], research_units=3))
        self.assertEqual(self.state()["actors"]["bob"]["remaining"], 1)
        self.finish("bob")
        allocation = self.state()["actors"]["bob"]
        self.assertEqual(allocation["remaining"], 0)
        self.assertEqual(allocation["coordination_used"] + allocation["research_used"], 8)
        self.assert_rejected_unchanged("budget_exhausted", "refresh", "bob", self.request("bob"))
        self.finish("alice")
        self.assertEqual(self.state()["round"], 2)
        failure = self.channel.call("close-failure", "alice", self.request("alice", target_actor="bob",
                                   reason="budget-exhausted", close_run=False))
        self.assertEqual(failure["view"]["round_closures"]["2"]["bob"]["reason"], "budget-exhausted")
        self.assertEqual(self.state()["actors"]["bob"], allocation)
        advanced = self.finish("alice")
        self.assertEqual(advanced["round"], 3)
        self.assertEqual(self.state()["intentions"]["bob:work"]["state"], "expired")
        for actor in self.state()["actors"].values():
            self.assertEqual(actor["remaining"] + actor["research_used"] + actor["coordination_used"], 8)

    def test_registered_failure_closes_run_without_role_or_policy_override(self):
        self.publish("alice")
        self.assert_rejected_unchanged("coordinator_only", "close-failure", "bob",
                                       self.request("bob", target_actor="alice", reason="actor-unavailable", close_run=True))
        self.assert_rejected_unchanged("invalid_failure", "close-failure", "alice",
                                       self.request("alice", target_actor="bob", reason="continue-alone", close_run=True))
        closure = self.channel.call("close-failure", "alice",
                                    self.request("alice", target_actor="bob", reason="channel-unavailable", close_run=True))
        self.assertEqual(closure["status"], "failure-closed")
        self.assertEqual(self.state()["run_failure"]["reason"], "channel-unavailable")
        self.assertEqual(self.state()["round"], 1)
        self.assertEqual(self.state()["actors"]["alice"]["coordination_used"], 4)
        self.assert_rejected_unchanged("run_closed", "refresh", "bob", self.request("bob"))
        self.assertEqual(self.channel.call("recover", "alice", {"request_id": closure["request_id"]}), closure)

    def test_execution_requires_current_context_and_intention_cadence(self):
        self.publish("alice")
        self.change("alice", "alice:work", "active")
        self.round()
        record = self.state()["intentions"]["alice:work"]
        self.assert_rejected_unchanged("refresh_required", "execute", "alice",
                                       self.request("alice", intention_id="alice:work", expected_revision=record["revision"], research_units=1))
        self.refresh("alice")
        self.assert_rejected_unchanged("refresh_required", "execute", "alice",
                                       self.request("alice", intention_id="alice:work", expected_revision=record["revision"], research_units=1))
        renewed = self.change("alice", "alice:work", "active")
        accounted = self.channel.call("execute", "alice",
                                      self.request("alice", intention_id="alice:work",
                                                   expected_revision=renewed["intention"]["revision"], research_units=1))
        self.assertEqual(accounted["intention"]["budget_used"], 1)
        self.assertEqual(accounted["intention"]["refresh_round"], 2)

    def test_abandonment_releases_advisory_reservation_but_retains_terminal_history(self):
        published = self.publish("alice")
        abandoned = self.change("alice", "alice:work", "abandoned")
        record = abandoned["intention"]
        self.assertEqual([history["state"] for history in record["history"]], ["planned", "abandoned"])
        self.assertEqual(record["experiment_signature"], published["intention"]["experiment_signature"])
        self.assertEqual(record["native_refs"], published["intention"]["native_refs"])
        self.assertEqual(record["verification_of"], published["intention"]["verification_of"])
        self.assert_rejected_unchanged("invalid_transition", "refresh-intention", "alice",
                                       self.request("alice", intention_id="alice:work", expected_revision=record["revision"], state="active"))
        next_item = intention("alice", "next", signature="next")
        next_item["budget_reserved"] = self.state()["actors"]["alice"]["remaining"] - 1
        replacement = self.channel.call("publish", "alice", self.request("alice", expected_revision=0, intention=next_item))
        self.assertEqual(replacement["intention"]["budget_reserved"], replacement["accounting"]["remaining"])
        self.assertEqual(self.state()["intentions"]["alice:work"], record)

    def test_whole_round_limit_and_immutable_preregistered_config(self):
        self.channel = Channel(self.root / "round-limit", "community", self.contract)
        self.initialize(run_config(max_rounds=1))
        self.assertEqual(self.finish("alice")["round"], 1)
        closed = self.finish("bob")
        self.assertEqual(closed["round"], 2)
        self.assertEqual(closed["status"], "round-limit-closed")
        self.assert_rejected_unchanged("run_closed", "refresh", "alice", self.request("alice"))
        recovered = self.channel.call("recover", "bob", {"request_id": closed["request_id"]})
        self.assertEqual(recovered, closed)
        bad_configs = []
        for field, value in (("allocation_per_actor", True), ("expiry_rounds", 0), ("max_rounds", 1.5)):
            config = run_config()
            config[field] = value
            bad_configs.append(config)
        config = run_config()
        config["actors"][1]["actor_id"] = "alice"
        bad_configs.append(config)
        config = run_config()
        config["failure_policy"]["channel_unavailable"] = "continue-alone"
        bad_configs.append(config)
        for index, config in enumerate(bad_configs):
            with self.subTest(index=index):
                channel = Channel(self.root / ("invalid-" + str(index)), "community", self.contract)
                with self.assertRaises(ChannelError):
                    channel.call("initialize", "alice", {"request_id": "alice:init", "config": config})
                self.assertFalse((channel.directory / "events.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
