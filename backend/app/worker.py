"""Worker entrypoint reserved for durable queue consumers in deployment."""


def main() -> None:
    raise SystemExit("Configure a durable queue consumer before starting the worker")


if __name__ == "__main__":
    main()
