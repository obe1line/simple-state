#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

STATE_BLOCK_RE = re.compile(r"struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*State<[^>]+>\s*\{")
HOOK_SIGNATURE_RE = re.compile(
    r"static\s+void\s+([A-Za-z_][A-Za-z0-9_]*)_on_(?:enter|update|exit)\s*\([^)]*\)\s*\{"
)
TRANSITION_CALL_RE = re.compile(r"transition<\s*(?:typename\s+)?(?:Controller::)?([A-Za-z_][A-Za-z0-9_]*)\s*>")


def strip_cpp_comments(source: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//.*", "", without_block_comments)


def hook_prefix_to_state(prefix: str) -> str:
    state_name = "".join(part.capitalize() for part in prefix.split("_"))
    return f"{state_name}State"


def parse_generated_states(path: Path):
    text = path.read_text(encoding="utf-8")
    return set(STATE_BLOCK_RE.findall(text))


def parse_user_transitions(path: Path):
    text = strip_cpp_comments(path.read_text(encoding="utf-8"))
    transitions = set()

    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        match = HOOK_SIGNATURE_RE.search(line)
        if match is None:
            index += 1
            continue

        hook_prefix = match.group(1)
        source_state = hook_prefix_to_state(hook_prefix)
        body_lines = []
        brace_depth = line.count("{") - line.count("}")
        index += 1

        while index < len(lines) and brace_depth > 0:
            body_line = lines[index]
            brace_depth += body_line.count("{") - body_line.count("}")
            body_lines.append(body_line)
            index += 1

        body_text = "\n".join(body_lines)
        for target in TRANSITION_CALL_RE.findall(body_text):
            transitions.add((source_state, target))

    return transitions


def format_pairs(pairs):
    if not pairs:
        return "  (none)"
    return "\n".join(f"  - {src} -> {dst}" for src, dst in sorted(pairs))


def main():
    parser = argparse.ArgumentParser(description="Compare states and transitions between split controller files")
    parser.add_argument("--expected-generated", required=True, help="Reference generated controller header path")
    parser.add_argument("--expected-user", required=True, help="Reference user hooks header path")
    parser.add_argument("--actual-generated", required=True, help="Generated controller header path under test")
    parser.add_argument("--actual-user", required=True, help="Generated user hooks header path under test")
    args = parser.parse_args()

    expected_states = parse_generated_states(Path(args.expected_generated))
    actual_states = parse_generated_states(Path(args.actual_generated))

    expected_transitions = parse_user_transitions(Path(args.expected_user))
    actual_transitions = parse_user_transitions(Path(args.actual_user))

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
