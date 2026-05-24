#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

STATE_BLOCK_RE = re.compile(
    r"struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*State<[^>]+>\s*\{(.*?)\n\s*\};",
    re.DOTALL,
)
TRANSITION_CALL_RE = re.compile(r"transition<\s*([A-Za-z_][A-Za-z0-9_]*)\s*>\s*\(")


def parse_header(path: Path):
    text = path.read_text(encoding="utf-8")
    states = set()
    transitions = set()

    for state_name, block in STATE_BLOCK_RE.findall(text):
        states.add(state_name)
        for target in TRANSITION_CALL_RE.findall(block):
            transitions.add((state_name, target))

    return states, transitions


def format_pairs(pairs):
    if not pairs:
        return "  (none)"
    return "\n".join(f"  - {src} -> {dst}" for src, dst in sorted(pairs))


def main():
    parser = argparse.ArgumentParser(description="Compare states/transitions between two controller headers")
    parser.add_argument("--expected", required=True, help="Reference header path")
    parser.add_argument("--actual", required=True, help="Generated header path")
    args = parser.parse_args()

    expected_states, expected_transitions = parse_header(Path(args.expected))
    actual_states, actual_transitions = parse_header(Path(args.actual))

    missing_states = expected_states - actual_states
    extra_states = actual_states - expected_states

    missing_transitions = expected_transitions - actual_transitions
    extra_transitions = actual_transitions - expected_transitions

    print("Expected states:", ", ".join(sorted(expected_states)))
    print("Actual states:", ", ".join(sorted(actual_states)))
    print("Expected transitions:")
    print(format_pairs(expected_transitions))
    print("Actual transitions:")
    print(format_pairs(actual_transitions))

    if missing_states or extra_states or missing_transitions or extra_transitions:
        print("\nComparison FAILED")
        if missing_states:
            print("Missing states:", ", ".join(sorted(missing_states)))
        if extra_states:
            print("Extra states:", ", ".join(sorted(extra_states)))
        if missing_transitions:
            print("Missing transitions:")
            print(format_pairs(missing_transitions))
        if extra_transitions:
            print("Extra transitions:")
            print(format_pairs(extra_transitions))
        raise SystemExit(1)

    print("\nComparison PASSED: states and transitions match.")


if __name__ == "__main__":
    main()
