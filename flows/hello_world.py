from prefect import flow, task
from datetime import datetime


@task(log_prints=True)
def say_hello(name: str) -> str:
    message = f"Hello, {name}! Greetings from Prefect."
    print(message)
    return message


@task(log_prints=True)
def get_timestamp() -> str:
    now = datetime.now().isoformat()
    print(f"Current time: {now}")
    return now


@flow(name="hello-world", log_prints=True)
def hello_world(name: str = "World"):
    """A simple hello world flow for testing your Prefect deployment."""
    timestamp = get_timestamp()
    greeting = say_hello(name)
    print(f"Flow completed at {timestamp}")
    return greeting


if __name__ == "__main__":
    hello_world()
