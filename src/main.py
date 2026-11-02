"""Text CLI: python -m src.main [--debug]"""

import sys

from src.agent import build_system_prompt, create_client, get_reply, load_config

GREETING = "Oi! Sou o assistente virtual da Empório da Música. Como posso ajudar? (digite \"sair\" para encerrar)"
EXIT_COMMAND = "sair"


def main() -> None:
    debug = "--debug" in sys.argv[1:]
    try:
        config = load_config()
    except ValueError as error:
        sys.exit(str(error))

    client = create_client(config)
    history = [{"role": "system", "content": build_system_prompt(config["reference_datetime"])}]

    print(f"Assistente: {GREETING}")
    while True:
        try:
            user_message = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if user_message.lower() == EXIT_COMMAND:
            return
        if not user_message:
            continue
        history.append({"role": "user", "content": user_message})
        print(f"Assistente: {get_reply(history, client, config, debug)}")


if __name__ == "__main__":
    main()
