#!/usr/bin/env python3
"""Compare the configurable Lean kernel against an independent Python scheduler.

The oracle keeps activation records with order tickets, and selects by sorting
(-priority, ticket).  It does not import Lean code or parse implementation output
to determine expected results.  Saved continuations are represented by a small
program counter; the QEMU test separately checks actual stacks and registers.
"""
from __future__ import annotations

import argparse
import dataclasses
import itertools
import json
import pathlib
import random
import subprocess


OK, ID, LIMIT, CALLEVEL, RESOURCE, BADINPUT = range(6)
ACTIVATE, TERMINATE, CHAIN, SCHEDULE, GET_ID, GET_STATE, STEP, ENTER_ISR, EXIT_ISR = range(9)


@dataclasses.dataclass
class Activation:
    task: int
    ticket: int
    pc: int = 0


class Oracle:
    def __init__(self, config):
        self.config = config
        self.running = None
        self.waiting = []
        self.next_ticket = 0
        self.front_ticket = -1
        self.depth = 0

    def new_activation(self, task):
        self.waiting.append(Activation(task, self.next_ticket))
        self.next_ticket += 1

    def outstanding(self, task):
        return sum(job.task == task for job in self.waiting) + int(
            self.running is not None and self.running.task == task)

    def reschedule(self, explicit=False):
        if self.depth or not self.waiting:
            return
        candidate = min(self.waiting, key=lambda job: (-self.config[job.task][0], job.ticket))
        if self.running is not None:
            priority, _, preemptive = self.config[self.running.task]
            if self.config[candidate.task][0] <= priority or not (preemptive or explicit):
                return
            self.running.ticket = self.front_ticket
            self.front_ticket -= 1
            self.waiting.append(self.running)
        self.waiting.remove(candidate)
        self.running = candidate

    def task_context(self, context):
        return context < 8 and context % 4 == 0 and self.depth == 0 and self.running is not None

    def query_context(self, context):
        return context < 8 and ((context % 4 == 0 and self.depth == 0) or
                                (context % 4 == 1 and self.depth > 0))

    def snapshot(self, status=OK, discard=0, value=0):
        current = 0 if self.running is None else self.running.task + 1
        waiting = sorted(self.waiting, key=lambda job: job.ticket)
        output = [status, current, discard, value, len(waiting)]
        output.extend(itertools.chain.from_iterable((job.task + 1, job.pc) for job in waiting))
        output.extend((0 if self.running is None else self.running.pc, self.depth))
        self.invariant()
        return output

    def invariant(self):
        for task, (_, limit, _) in enumerate(self.config):
            assert self.outstanding(task) <= limit
        # A saved continuation must be selected before any fresh activation of
        # the same task.  There can be at most one partially executed instance.
        for task in range(len(self.config)):
            instances = [job for job in self.waiting if job.task == task]
            if self.running is not None and self.running.task == task:
                instances.append(self.running)
            assert sum(job.pc > 0 for job in instances) <= 1

    def call(self, op, target, context):
        if op == ENTER_ISR:
            self.depth += 1
            return self.snapshot()
        if op == EXIT_ISR:
            if self.depth == 0:
                return self.snapshot(CALLEVEL)
            self.depth -= 1
            self.reschedule()
            return self.snapshot()
        if op == ACTIVATE:
            if not self.query_context(context) or (context % 4 == 0 and self.running is None):
                return self.snapshot(CALLEVEL)
            if target >= len(self.config):
                return self.snapshot(ID)
            if self.outstanding(target) >= self.config[target][1]:
                return self.snapshot(LIMIT)
            self.new_activation(target)
            self.reschedule()
            return self.snapshot()
        if op in (TERMINATE, CHAIN, SCHEDULE, STEP):
            if not self.task_context(context):
                return self.snapshot(CALLEVEL)
            if op != STEP and context // 4 % 2:
                return self.snapshot(RESOURCE)
            if op == CHAIN:
                if target >= len(self.config):
                    return self.snapshot(ID)
                if target != self.running.task and self.outstanding(target) >= self.config[target][1]:
                    return self.snapshot(LIMIT)
            if op == STEP:
                self.running.pc += 1
                return self.snapshot()
            if op == SCHEDULE:
                self.reschedule(explicit=True)
                return self.snapshot()
            self.running = None
            if op == CHAIN:
                self.new_activation(target)
            self.reschedule()
            return self.snapshot(discard=1)
        if op in (GET_ID, GET_STATE):
            if not self.query_context(context):
                return self.snapshot(CALLEVEL)
            if op == GET_ID:
                return self.snapshot(value=0 if self.running is None else self.running.task + 1)
            if target >= len(self.config):
                return self.snapshot(ID)
            value = 1 if self.outstanding(target) == 0 else (
                3 if self.running is not None and self.running.task == target else 2)
            return self.snapshot(value=value)
        return self.snapshot(BADINPUT)


def boot(task=0):
    """Project startup harness: ISR activation followed by outermost ISR exit."""
    return [(ENTER_ISR, 0, 0), (ACTIVATE, task, 1), (EXIT_ISR, 0, 1)]


def encode(config, commands):
    values = [len(config)]
    values.extend(itertools.chain.from_iterable(config))
    values.append(len(commands))
    values.extend(itertools.chain.from_iterable(commands))
    return " ".join(map(str, values))


def scenarios():
    preempt = [(1, 2, 1), (2, 2, 1), (3, 1, 1)]
    equal = [(2, 3, 1), (2, 2, 1), (3, 1, 1)]
    cooperative = [(1, 1, 0), (2, 1, 1)]
    yield "preempt_resume_restart", preempt, boot() + [
        (STEP, 0, 0), (ACTIVATE, 2, 0), (STEP, 0, 0), (TERMINATE, 0, 0),
        (CHAIN, 0, 0), (TERMINATE, 0, 0)]
    yield "equal_priority_fifo_and_saved_instance", equal, boot() + [
        (STEP, 0, 0), (ACTIVATE, 1, 0), (ACTIVATE, 0, 0), (ACTIVATE, 2, 0),
        (TERMINATE, 0, 0), (TERMINATE, 0, 0), (TERMINATE, 0, 0), (TERMINATE, 0, 0)]
    yield "nonpreemptive_explicit_schedule", cooperative, boot() + [
        (STEP, 0, 0), (ACTIVATE, 1, 0), (SCHEDULE, 0, 0), (TERMINATE, 0, 0)]
    yield "schedule_does_not_round_robin", equal, boot() + [
        (ACTIVATE, 1, 0), (SCHEDULE, 0, 0), (GET_ID, 0, 0), (GET_STATE, 1, 0)]
    yield "chain_atomic_error_and_self_at_limit", [(2, 1, 1), (1, 1, 1)], boot() + [
        (ACTIVATE, 1, 0), (STEP, 0, 0), (CHAIN, 1, 0), (CHAIN, 0, 0),
        (CHAIN, 99, 0), (TERMINATE, 0, 0)]
    yield "self_chain_joins_fifo_tail", equal, boot() + [
        (ACTIVATE, 1, 0), (ACTIVATE, 0, 0), (STEP, 0, 0), (CHAIN, 0, 0),
        (TERMINATE, 0, 0), (TERMINATE, 0, 0), (TERMINATE, 0, 0)]
    yield "nested_isr_defers_dispatch", preempt, boot() + [
        (STEP, 0, 0), (ENTER_ISR, 0, 0), (ACTIVATE, 2, 1), (GET_ID, 0, 1),
        (GET_STATE, 0, 1), (ENTER_ISR, 0, 1), (TERMINATE, 0, 1),
        (SCHEDULE, 0, 1), (ACTIVATE, 1, 0), (EXIT_ISR, 0, 1),
        (GET_ID, 0, 1), (EXIT_ISR, 0, 1), (TERMINATE, 0, 0)]
    yield "isr_return_respects_nonpreemptive", cooperative, boot() + [
        (ENTER_ISR, 0, 0), (ACTIVATE, 1, 1), (EXIT_ISR, 0, 1), (SCHEDULE, 0, 0)]
    yield "resource_guard_preserves_state", preempt, boot() + [
        (STEP, 0, 0), (TERMINATE, 0, 4), (CHAIN, 1, 4), (SCHEDULE, 0, 4),
        (GET_ID, 0, 4), (GET_STATE, 0, 4), (TERMINATE, 0, 0)]
    yield "idle_queries_and_invalid_calls", preempt, [
        (GET_ID, 0, 0), (GET_STATE, 0, 0), (TERMINATE, 0, 0),
        (ACTIVATE, 0, 0), (CHAIN, 0, 0), (SCHEDULE, 0, 0), (EXIT_ISR, 0, 1),
        (GET_ID, 0, 1), (GET_STATE, 2**32 - 1, 0), (99, 0, 0)]
    large = [(task % 7, 2, task % 2) for task in range(64)]
    yield "sixty_four_tasks", large, [(ENTER_ISR, 0, 0)] + [
        (ACTIVATE, task, 1) for task in range(64)] + [(EXIT_ISR, 0, 1)] + [
        (STEP, 0, 0), (GET_STATE, 63, 0)] + [(TERMINATE, 0, 0)] * 64


def oracle_self_checks(named):
    """A few independently stated expected observations protect scenario intent."""
    assert [(row[1], row[-2]) for row in named["preempt_resume_restart"][-6:]] == [
        (1, 1), (3, 0), (3, 1), (1, 1), (1, 0), (0, 0)]
    assert [row[1] for row in named["equal_priority_fifo_and_saved_instance"][-4:]] == [1, 2, 1, 0]
    assert [row[1] for row in named["nonpreemptive_explicit_schedule"][-3:]] == [1, 2, 1]
    chain = named["chain_atomic_error_and_self_at_limit"]
    assert chain[5][0] == LIMIT and chain[5][1] == 1 and chain[5][-2] == 1
    assert chain[6][0] == OK and chain[6][2] == 1 and chain[6][-2] == 0
    assert [row[0] for row in named["resource_guard_preserves_state"][4:7]] == [RESOURCE] * 3
    assert named["schedule_does_not_round_robin"][-2][3] == 1
    assert named["schedule_does_not_round_robin"][-1][3] == 2


def all_cases():
    yield from scenarios()
    # Exhaust every length-four word of this service alphabet, from four
    # configurations that distinguish priority, FIFO, limits and cooperation.
    configs = [[(1, 1, 1), (2, 1, 1)], [(2, 2, 1), (2, 2, 1)],
               [(1, 2, 0), (3, 2, 1)], [(3, 2, 1), (1, 1, 0), (3, 1, 1)]]
    alphabet = [(ACTIVATE, 0, 0), (ACTIVATE, 1, 0), (TERMINATE, 0, 0),
                (CHAIN, 0, 0), (CHAIN, 1, 0), (SCHEDULE, 0, 0), (STEP, 0, 0)]
    for config_index, config in enumerate(configs):
        for sequence_index, commands in enumerate(itertools.product(alphabet, repeat=4)):
            yield f"exhaustive_{config_index}_{sequence_index}", config, boot() + list(commands)
    # Reproducible long traces add invalid IDs, wrong call levels, nested ISRs,
    # queries and unusual priority magnitudes to the exhaustive short traces.
    rng = random.Random(20261013)
    for i in range(200):
        config = [(rng.choice([0, 1, 2, 1000000]), rng.randint(1, 3), rng.randrange(2))
                  for _ in range(rng.randint(1, 8))]
        commands = boot() + [(rng.randrange(11), rng.choice([0, 1, 2, len(config), 2**32 - 1]),
                              rng.choice([0, 0, 1, 2, 4, 5, 6, 8, 2**32 - 1])) for _ in range(30)]
        yield f"random_{i}", config, commands


def check_protocol(runner, output):
    invalid = ["", "0 0", "1 1 0 1 0", "1 1 1 2 0", "1 1 1 1",
               "1 1 1 1 1 0 0", "1 1 1 1 0 99", "1 -1 1 1 0",
               "one 1 1 1 0", "1 1 1 1 1 4 0 0 99"]
    # Valid zero-command trace has no result; whitespace and zero priority work.
    payload = "\n".join(invalid + ["1 0 1 0 0", "\t1  0 1 1\t1 4 0 0\r"]) + "\n"
    expected = ["INVALID"] * len(invalid) + ["0 0 0 0 0 0 0"]
    process = subprocess.run(runner, input=payload, text=True, capture_output=True, timeout=30)
    (output / "task-protocol.stdout").write_text(process.stdout)
    (output / "task-protocol.stderr").write_text(process.stderr)
    passed = process.returncode == 0 and process.stdout.splitlines() == expected
    return dict(status="passed" if passed else "failed", cases=len(invalid) + 2,
                expected=expected if not passed else None,
                actual=process.stdout.splitlines() if not passed else None)


def scalar_config(config):
    return (len(config) << 36) | sum(
        (priority << (4 * task)) | (limit << (16 + 4 * task)) | (preemptive << (32 + task))
        for task, (priority, limit, preemptive) in enumerate(config))


def scalar_state(row):
    # The generic protocol includes each frame's educational progress counter;
    # the bounded adapter stores machine continuations outside the scalar word.
    queue = sum(row[5 + 2 * i] << (4 * i) for i in range(row[4]))
    return queue | (row[1] << 32) | (row[-1] << 36)


def check_scalar(runner, cases, output):
    vectors, expected, names = [], [], []
    for name, config, commands in cases:
        if len(config) > 4 or sum(task[1] for task in config) > 8 or any(task[0] > 15 for task in config):
            continue
        oracle = Oracle(config)
        cfg = scalar_config(config)
        for i, command in enumerate(commands):
            if command[0] == STEP:
                continue
            before = scalar_state(oracle.snapshot())
            row = oracle.call(*command)
            assert row[-1] <= 15
            vectors.append((cfg, before, *command))
            expected.append(scalar_state(row) | (row[0] << 40) | (row[3] << 44) | (row[2] << 48))
            names.append((name, i))

    # Capacity, UINT64 boundary and malformed packed inputs are exercised
    # directly because they are specific to this bounded adapter.
    config = [(1, 2, 1)] * 4
    cfg = scalar_config(config)
    oracle = Oracle(config)
    commands = [(ENTER_ISR, 0, 0)] + [(ACTIVATE, task, 1) for task in range(4) for _ in range(2)]
    commands += [(ACTIVATE, 0, 1), (ACTIVATE, 2**64 - 1, 1), (EXIT_ISR, 0, 1)]
    commands += [(TERMINATE, 0, 0)] * 8
    for i, command in enumerate(commands):
        before = scalar_state(oracle.snapshot())
        row = oracle.call(*command)
        vectors.append((cfg, before, *command))
        expected.append(scalar_state(row) | (row[0] << 40) | (row[3] << 44) | (row[2] << 48))
        names.append(("scalar_capacity", i))
    invalid = [(0, 0), (cfg | (1 << 40), 0), (2**64 - 1, 0), (cfg & ~(15 << 16), 0),
               (scalar_config([(1, 3, 1)] * 3), 0), (cfg, 5 << 32),
               (cfg, 0x101), (cfg, 0x111), (cfg, 0x5), (cfg, 2**64 - 1)]
    for i, (bad_cfg, state) in enumerate(invalid):
        vectors.append((bad_cfg, state, GET_ID, 0, 0))
        expected.append(BADINPUT << 40)
        names.append(("scalar_invalid_input", i))
    vectors.append((cfg, 15 << 36, ENTER_ISR, 0, 1))
    expected.append((15 << 36) | BADINPUT << 40)
    names.append(("scalar_nesting_bound", 0))

    payload = "".join(" ".join(map(str, vector)) + "\n" for vector in vectors)
    (output / "task-scalar-input.txt").write_text(payload)
    (output / "task-scalar-oracle.txt").write_text("".join(f"{value}\n" for value in expected))
    process = subprocess.run([str(runner)], input=payload, text=True, capture_output=True, timeout=60)
    (output / "task-scalar.stdout").write_text(process.stdout)
    (output / "task-scalar.stderr").write_text(process.stderr)
    try:
        actual = [int(line) for line in process.stdout.splitlines()]
    except ValueError:
        actual = []
    mismatches = [dict(case=names[i][0], step=names[i][1], vector=vectors[i], expected=value,
                       actual=actual[i] if i < len(actual) else None)
                  for i, value in enumerate(expected) if i >= len(actual) or actual[i] != value]
    passed = process.returncode == 0 and not mismatches and len(actual) == len(expected)
    return dict(id="T-TASK-SCALAR", status="passed" if passed else "failed",
                vectors=len(vectors), returncode=process.returncode,
                actual_count=len(actual), mismatches=mismatches[:20])


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--scalar-runner", type=pathlib.Path)
    parser.add_argument("--runner", nargs=argparse.REMAINDER,
                        default=["lake", "env", "lean", "--run", "TaskMain.lean"])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = list(all_cases())
    expected, names, named = [], [], {}
    named_cases = {item[0] for item in scenarios()}
    for name, config, commands in cases:
        oracle = Oracle(config)
        rows = [oracle.call(*command) for command in commands]
        if name in named_cases:
            named[name] = rows
        expected.extend(rows)
        names.extend((name, i, command) for i, command in enumerate(commands))
    oracle_self_checks(named)
    payload = "\n".join(encode(config, commands) for _, config, commands in cases) + "\n"
    (args.output / "task-control-input.txt").write_text(payload)
    (args.output / "task-control-oracle.txt").write_text(
        "".join(" ".join(map(str, row)) + "\n" for row in expected))
    process = subprocess.run(args.runner, input=payload, text=True, capture_output=True, timeout=180)
    (args.output / "task-control.stdout").write_text(process.stdout)
    (args.output / "task-control.stderr").write_text(process.stderr)
    try:
        actual = [list(map(int, line.split())) for line in process.stdout.splitlines()]
    except ValueError:
        actual = []
    mismatches = [dict(case=names[i][0], step=names[i][1], command=names[i][2],
                       expected=row, actual=actual[i] if i < len(actual) else None)
                  for i, row in enumerate(expected) if i >= len(actual) or row != actual[i]]
    passed = process.returncode == 0 and not mismatches and len(actual) == len(expected)
    protocol = check_protocol(args.runner, args.output)
    passed = passed and protocol["status"] == "passed"
    scalar = check_scalar(args.scalar_runner, cases, args.output) if args.scalar_runner else None
    passed = passed and (scalar is None or scalar["status"] == "passed")
    summary = dict(id="T-TASK-CONTROL", status="passed" if passed else "failed",
                   traces=len(cases), transitions=len(expected), exhaustive_traces=4 * 7**4,
                   exhaustive_depth=4, random_seed=20261013, returncode=process.returncode,
                   actual_count=len(actual), scenarios=list(named), protocol=protocol,
                   scalar=scalar, mismatches=mismatches[:20])
    (args.output / "task-control.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
