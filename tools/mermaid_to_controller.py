#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

TRANSITION_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*|\[\*\])\s*-->\s*([A-Za-z_][A-Za-z0-9_]*|\[\*\])(?:\s*:\s*(.+))?\s*$"
)


def ordered_unique(items):
    seen = set()
    ordered = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def parse_mermaid(source: str):
    states_in_order = []
    transitions = []
    initial_state = None

    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("%%"):
            continue
        if line.startswith("stateDiagram"):
            continue

        match = TRANSITION_RE.match(line)
        if not match:
            continue

        src, dst, label = match.groups()
        label = (label or "").strip()

        if src == "[*]":
            if dst != "[*]":
                initial_state = dst
                states_in_order.append(dst)
            continue

        if dst == "[*]":
            states_in_order.append(src)
            continue

        states_in_order.extend([src, dst])
        transitions.append((src, dst, label))

    states = ordered_unique(states_in_order)
    if initial_state is None and states:
        initial_state = states[0]

    return states, transitions, initial_state


def state_display_name(state_name: str) -> str:
    return state_name[:-5] if state_name.endswith("State") else state_name


def render_controller(namespace: str, controller_name: str, states, transitions, initial_state: str) -> str:
    transitions_by_source = {state: [] for state in states}
    for src, dst, label in transitions:
        transitions_by_source[src].append((dst, label))

    lines = []
    lines.append("#pragma once")
    lines.append("")
    lines.append("#include <cstdint>")
    lines.append("")
    lines.append('#include "simple_state/crtp_state_machine.hpp"')
    lines.append("")
    lines.append(f"namespace {namespace} {{")
    lines.append("")
    lines.append("template <typename Board>")
    lines.append(f"class {controller_name} {{")
    lines.append("public:")

    for state in states:
        lines.append(f"    struct {state};")
    lines.append("")

    lines.append("    struct Context {")
    lines.append("        Board& board;")
    lines.append("        Machine<Context>* machine{};")
    lines.append("        std::uint32_t state_started_at{};")
    lines.append("")
    lines.append("        [[nodiscard]] std::uint32_t now() const {")
    lines.append("            return board.millis();")
    lines.append("        }")
    lines.append("")
    lines.append("        void mark_state_entry() {")
    lines.append("            state_started_at = now();")
    lines.append("        }")
    lines.append("")
    lines.append("        [[nodiscard]] std::uint32_t elapsed_in_state() const {")
    lines.append("            return now() - state_started_at;")
    lines.append("        }")
    lines.append("")
    lines.append("        template <typename NextState>")
    lines.append("        void transition() {")
    lines.append("            machine->template transition_to<NextState>();")
    lines.append("        }")
    lines.append("    };")
    lines.append("")

    for state in states:
        lines.append(f"    struct {state} : State<{state}, Context> {{")
        lines.append("        static void on_enter(Context& context) {")
        lines.append("            context.mark_state_entry();")
        lines.append("        }")
        lines.append("")
        lines.append("        static void on_update(Context& context) {")
        state_transitions = transitions_by_source.get(state, [])
        if not state_transitions:
            lines.append("            (void)context;")
        else:
            for dst, label in state_transitions:
                transition_label = f" [{label}]" if label else ""
                lines.append(f"            // Transition: {state} -> {dst}{transition_label}")
                lines.append(f"            // context.template transition<{dst}>();")
        lines.append("        }")
        lines.append("")
        lines.append("        static void on_exit(Context&) {}")
        lines.append("")
        lines.append("        static const char* name() {")
        lines.append(f"            return \"{state_display_name(state)}\";")
        lines.append("        }")
        lines.append("    };")
        lines.append("")

    lines.append(f"    explicit {controller_name}(Board& board) : context_{{board}}, machine_(context_) {{")
    lines.append("        context_.machine = &machine_;")
    lines.append("    }")
    lines.append("")
    lines.append("    void start() {")
    lines.append(f"        machine_.template start<{initial_state}>();")
    lines.append("    }")
    lines.append("")
    lines.append("    void run_once() {")
    lines.append("        machine_.dispatch();")
    lines.append("    }")
    lines.append("")
    lines.append("    [[nodiscard]] const char* state_name() const {")
    lines.append("        return machine_.current_name();")
    lines.append("    }")
    lines.append("")
    lines.append("private:")
    lines.append("    Context context_;")
    lines.append("    Machine<Context> machine_;")
    lines.append("};")
    lines.append("")
    lines.append(f"}}  // namespace {namespace}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate a controller header from a Mermaid state diagram")
    parser.add_argument("--input", required=True, help="Path to Mermaid diagram file")
    parser.add_argument("--output", required=True, help="Path to generated .hpp file")
    parser.add_argument("--controller", default="GeneratedController", help="Controller class name")
    parser.add_argument("--namespace", default="simple_state", help="C++ namespace")
    args = parser.parse_args()

    diagram_text = Path(args.input).read_text(encoding="utf-8")
    states, transitions, initial_state = parse_mermaid(diagram_text)
    if not states:
        raise SystemExit("No states parsed from Mermaid input")
    if initial_state is None:
        raise SystemExit("No initial state found")

    rendered = render_controller(args.namespace, args.controller, states, transitions, initial_state)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    print(f"Generated {args.output}")
    print(f"States: {', '.join(states)}")
    print("Transitions:")
    for src, dst, label in transitions:
        suffix = f" [{label}]" if label else ""
        print(f"  - {src} -> {dst}{suffix}")


if __name__ == "__main__":
    main()
