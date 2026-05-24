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


def state_hook_prefix(state_name: str) -> str:
    base_name = state_display_name(state_name)
    return re.sub(r"(?<!^)(?=[A-Z])", "_", base_name).lower()


def default_user_output_path(output_path: Path) -> Path:
    if output_path.parent.name == "generated" and output_path.stem.endswith("_generated"):
        base_name = output_path.stem[: -len("_generated")]
        return output_path.parent.parent / f"{base_name}_user{output_path.suffix}"
    return output_path.with_name(f"{output_path.stem}_user{output_path.suffix}")


def default_wrapper_output_path(output_path: Path) -> Path | None:
    if output_path.parent.name == "generated" and output_path.stem.endswith("_generated"):
        base_name = output_path.stem[: -len("_generated")]
        return output_path.parent.parent / f"{base_name}{output_path.suffix}"
    return None


def infer_controller_name(output_path: Path) -> str:
    stem = output_path.stem
    if stem.endswith("_generated"):
        stem = stem[: -len("_generated")]
    if stem.endswith("_controller"):
        stem = stem[: -len("_controller")]

    parts = [part for part in stem.split("_") if part]
    if not parts:
        raise SystemExit(
            "Unable to infer controller name from output path; pass --controller explicitly"
        )

    return "".join(part.capitalize() for part in parts) + "Controller"


def infer_namespace(output_path: Path) -> str:
    parts = output_path.parts
    if "include" in parts:
        include_index = parts.index("include")
        namespace_parts = []
        for part in parts[include_index + 1 : -1]:
            if part == "generated":
                break
            namespace_parts.append(part)
        if namespace_parts:
            return "::".join(namespace_parts)

    return "simple_state"


def render_generated_controller(namespace: str, controller_name: str, states, initial_state: str) -> str:
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
    lines.append(f"struct {controller_name}Hooks;")
    lines.append("")
    lines.append("template <typename Board>")
    lines.append(f"class {controller_name} {{")
    lines.append("public:")

    for state in states:
        lines.append(f"    struct {state};")
    lines.append("")

    lines.append(f"    struct Context : {controller_name}Hooks<Board>::Data {{")
    lines.append("        Board& board;")
    lines.append("        Machine<Context>* machine{};")
    lines.append("        std::uint32_t state_started_at{};")
    lines.append("")
    lines.append("        explicit Context(Board& board_ref) : board(board_ref) {}")
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
        hook_prefix = state_hook_prefix(state)
        lines.append(f"    struct {state} : State<{state}, Context> {{")
        lines.append("        static void on_enter(Context& context) {")
        lines.append(f"            {controller_name}Hooks<Board>::{hook_prefix}_on_enter(context);")
        lines.append("        }")
        lines.append("")
        lines.append("        static void on_update(Context& context) {")
        lines.append(f"            {controller_name}Hooks<Board>::{hook_prefix}_on_update(context);")
        lines.append("        }")
        lines.append("")
        lines.append("        static void on_exit(Context& context) {")
        lines.append(f"            {controller_name}Hooks<Board>::{hook_prefix}_on_exit(context);")
        lines.append("        }")
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
    lines.append("    [[nodiscard]] bool led_is_on() const {")
    lines.append("        return context_.board.led_is_on();")
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


def render_user_hooks(namespace: str, controller_name: str, generated_include: str, states, transitions) -> str:
    transitions_by_source = {state: [] for state in states}
    for src, dst, label in transitions:
        transitions_by_source[src].append((dst, label))

    lines = []
    lines.append("#pragma once")
    lines.append("")
    lines.append(f'#include "{generated_include}"')
    lines.append("")
    lines.append(f"namespace {namespace} {{")
    lines.append("")
    lines.append("template <typename Board>")
    lines.append(f"struct {controller_name}Hooks {{")
    lines.append(f"    using Controller = {controller_name}<Board>;")
    lines.append("    using Context = typename Controller::Context;")
    lines.append("")
    lines.append("    struct Data {};")
    lines.append("")

    for state in states:
        hook_prefix = state_hook_prefix(state)
        lines.append(f"    static void {hook_prefix}_on_enter(Context& context) {{")
        lines.append("        context.mark_state_entry();")
        lines.append("    }")
        lines.append("")
        lines.append(f"    static void {hook_prefix}_on_update(Context& context) {{")
        state_transitions = transitions_by_source.get(state, [])
        if not state_transitions:
            lines.append("        (void)context;")
        else:
            for index, (dst, label) in enumerate(state_transitions):
                transition_label = f" [{label}]" if label else ""
                lines.append(f"        // TODO: replace placeholder condition for {state} -> {dst}{transition_label}")
                lines.append("        if (false) {")
                lines.append(f"            context.template transition<typename Controller::{dst}>();")
                lines.append("        }")
                if index != len(state_transitions) - 1:
                    lines.append("")
        lines.append("    }")
        lines.append("")
        lines.append(f"    static void {hook_prefix}_on_exit(Context&) {{}}")
        lines.append("")

    lines.append("};")
    lines.append("")
    lines.append(f"}}  // namespace {namespace}")
    lines.append("")
    return "\n".join(lines)


def render_wrapper_header(generated_include: str, user_include: str) -> str:
    lines = []
    lines.append("#pragma once")
    lines.append("")
    lines.append(f'#include "{generated_include}"')
    lines.append(f'#include "{user_include}"')
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate split controller headers from a Mermaid state diagram")
    parser.add_argument("--input", required=True, help="Path to Mermaid diagram file")
    parser.add_argument("--output", required=True, help="Path to generated controller .hpp file")
    parser.add_argument("--user-output", help="Path to user-owned hooks .hpp file")
    parser.add_argument("--wrapper-output", help="Path to stable wrapper .hpp file")
    parser.add_argument("--controller", help="Controller class name")
    parser.add_argument("--namespace", help="C++ namespace")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve inferred outputs and metadata without writing files",
    )
    parser.add_argument(
        "--overwrite-user-output",
        action="store_true",
        help="Overwrite the user hooks file if it already exists",
    )
    args = parser.parse_args()

    diagram_text = Path(args.input).read_text(encoding="utf-8")
    states, transitions, initial_state = parse_mermaid(diagram_text)
    if not states:
        raise SystemExit("No states parsed from Mermaid input")
    if initial_state is None:
        raise SystemExit("No initial state found")

    output_path = Path(args.output)
    controller_name = args.controller or infer_controller_name(output_path)
    namespace = args.namespace or infer_namespace(output_path)
    user_output_path = Path(args.user_output) if args.user_output else default_user_output_path(output_path)
    wrapper_output_path = Path(args.wrapper_output) if args.wrapper_output else default_wrapper_output_path(output_path)

    generated_header = render_generated_controller(namespace, controller_name, states, initial_state)
    user_header = render_user_hooks(namespace, controller_name, output_path.name, states, transitions)

    user_file_written = False
    wrapper_file_written = False

    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated_header, encoding="utf-8")

        user_output_path.parent.mkdir(parents=True, exist_ok=True)
        if args.overwrite_user_output or not user_output_path.exists():
            user_output_path.write_text(user_header, encoding="utf-8")
            user_file_written = True

        if wrapper_output_path is not None:
            wrapper_header = render_wrapper_header(
                f"generated/{output_path.name}",
                user_output_path.name,
            )
            wrapper_output_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_output_path.write_text(wrapper_header, encoding="utf-8")
            wrapper_file_written = True

    generated_verb = "Would generate" if args.dry_run else "Generated"
    preserved_verb = "Would preserve existing" if args.dry_run else "Preserved existing"
    print(f"{generated_verb} controller header: {output_path}")
    if args.overwrite_user_output or not user_output_path.exists():
        user_message = f"{generated_verb} user hooks header: {user_output_path}"
    else:
        user_message = f"{preserved_verb} user hooks header: {user_output_path}"
    print(user_message)
    if wrapper_output_path is not None:
        print(f"{generated_verb} wrapper header: {wrapper_output_path}")
    print(f"Controller: {controller_name}")
    print(f"Namespace: {namespace}")
    if args.dry_run:
        print("Dry run: no files written")
    print(f"States: {', '.join(states)}")
    print("Transitions:")
    for src, dst, label in transitions:
        suffix = f" [{label}]" if label else ""
        print(f"  - {src} -> {dst}{suffix}")


if __name__ == "__main__":
    main()
