from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="titanos", description="TITANOS CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    run_parser = subparsers.add_parser("run", help="Run a single goal")
    run_parser.add_argument("goal", nargs="*", help="The goal to achieve")
    run_parser.add_argument("--model", help="AI model to use")

    ask_parser = subparsers.add_parser("ask", help="Ask TITANOS a goal")
    ask_parser.add_argument("goal", nargs="*", help="The goal to achieve")
    ask_parser.add_argument("--model", help="AI model to use")

    memory_parser = subparsers.add_parser("memory", help="Use TITANOS Memory")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")
    memory_add = memory_subparsers.add_parser("add", help="Store a memory")
    memory_add.add_argument("text", nargs="+")
    memory_search = memory_subparsers.add_parser("search", help="Search memory")
    memory_search.add_argument("query", nargs="*")
    memory_list = memory_subparsers.add_parser("list", help="List recent memory")
    memory_update = memory_subparsers.add_parser("update", help="Update a memory")
    memory_update.add_argument("id")
    memory_update.add_argument("text", nargs="+")
    memory_delete = memory_subparsers.add_parser("delete", help="Delete a memory")
    memory_delete.add_argument("id")

    subparsers.add_parser("doctor", help="Check local TITANOS runtime health")

    app_parser = subparsers.add_parser("app", help="Start the desktop app server")
    app_parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    app_parser.add_argument("--ui", action="store_true", help="Launch in a standalone window")

    # Legacy flags (handled for compatibility)
    parser.add_argument("--sources", action="store_true", help="Show source bodies")
    parser.add_argument("--providers", action="store_true", help="Show AI providers")
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Start interactive chat"
    )
    parser.add_argument("--model", help="AI model to use (legacy)")

    args = parser.parse_args()

    if args.sources:
        from .sources import source_report

        print("TITANOS source bodies:")
        for line in source_report():
            print(f"- {line}")
        return 0

    if args.providers:
        from .providers import provider_report

        print("TITANOS AI providers:")
        for line in provider_report():
            print(f"- {line}")
        return 0

    if args.command == "app":
        from .app import start_app
        start_app(port=args.port, use_window=args.ui)
        return 0

    from .contracts import BodySystem, ChatMessage
    from .config.settings import settings
    from .defaults import create_titanos

    titanos = create_titanos()

    model_name = getattr(args, "model", None)
    cortex = next((a for a in titanos.body if a.info.name == BodySystem.CORTEX), None)
    if cortex and model_name:
        cortex.model_name = model_name

    if args.interactive:
        print("TITANOS Interactive Mode (Ctrl+C to exit)")
        history: list[ChatMessage] = []
        while True:
            try:
                user_input = input("\n> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit"):
                    break
                
                result = titanos.run(user_input, context=[m.content for m in history])
                print(f"\n[{result.system.value}] {result.summary}")
                
                history.append(ChatMessage(role="user", content=user_input))
                history.append(ChatMessage(role="assistant", content=result.summary))
                
            except KeyboardInterrupt:
                break
        return 0

    if args.command == "doctor":
        from .providers import configured_model_provider, provider_health_report

        print("TITANOS doctor:")
        print("- CLI: ok")
        print(f"- Version: {settings.VERSION}")
        print(f"- Model: {settings.TITANOS_MODEL}")
        print(f"- Model provider: {configured_model_provider()}")
        print(f"- Data path: {settings.DATA_DIR}")
        print(f"- Log path: {settings.LOG_PATH}")
        print(f"- Memory path: {settings.DATA_DIR / 'memory.sqlite'}")
        print(f"- Session path: {settings.DATA_DIR / 'sessions'}")
        print(f"- Body systems: {len(titanos.body)} registered")
        for health in titanos.health_report():
            print(f"- {health.system.value}: {health.status} - {health.summary}")
        print("- Provider health:")
        for line in provider_health_report(timeout=1.0):
            print(f"  - {line}")
        if settings.CORS_ALLOW_ORIGINS == "*":
            print("- Warning: CORS allows all origins")
        if settings.JWT_SECRET == "super-secret-dev-key":
            print("- Warning: using development JWT secret")
        return 0

    if args.command == "memory":
        if args.memory_command == "add":
            goal = "remember " + " ".join(args.text)
        elif args.memory_command == "search":
            goal = "recall " + " ".join(args.query)
        elif args.memory_command == "list":
            goal = "memory list"
        elif args.memory_command == "update":
            goal = f"memory update {args.id} " + " ".join(args.text)
        elif args.memory_command == "delete":
            goal = f"memory delete {args.id}"
        else:
            memory_parser.print_help()
            return 2
    else:
        goal = " ".join(getattr(args, "goal", [])).strip()
    
    if not goal:
        parser.print_help()
        return 2

    result = titanos.run(goal)
    print(f"[{result.system.value}] {result.status}: {result.summary}")
    for step in result.next_steps:
        print(f"- {step}")
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
