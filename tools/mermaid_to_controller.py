#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"

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


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["hook_prefix"] = state_hook_prefix
    env.filters["display_name"] = state_display_name
    return env


def render_generated_controller(namespace: str, controller_name: str, states, initial_state: str) -> str:
    return _env().get_template("controller_generated.hpp.jinja").render(
        namespace=namespace,
        controller_name=controller_name,
        states=states,
        initial_state=initial_state,
    )


def render_user_hooks(namespace: str, controller_name: str, generated_include: str, states, transitions) -> str:
    transitions_by_source = {state: [] for state in states}
    for src, dst, label in transitions:
        transitions_by_source[src].append((dst, label))

    return _env().get_template("controller_user.hpp.jinja").render(
        namespace=namespace,
        controller_name=controller_name,
        generated_include=generated_include,
        states=states,
        transitions_by_source=transitions_by_source,
    )


def render_wrapper_header(generated_include: str, user_include: str) -> str:
    return _env().get_template("controller_wrapper.hpp.jinja").render(
        generated_include=generated_include,
        user_include=user_include,
    )


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
