from pathlib import Path

import docker
import pandas as pd

# Activate docker client.
client = docker.from_env()

# List available images on the current device.
available_images = [
    img
    for tags in [i.tags for i in client.images.list() if len(i.tags) > 0]
    for img in tags
]


def wait_and_close_container(container):
    """Wait for a container execution and remove it, returning logs and duration."""
    container.wait()
    logs = container.logs()
    state = client.api.inspect_container(container.id)["State"]
    execution_time = pd.to_datetime(state["FinishedAt"]) - pd.to_datetime(
        state["StartedAt"]
    )
    container.stop()
    container.remove(v=True)
    return (logs.decode("utf-8"), execution_time)


def get_volume(folder, isMatlab=False):
    """Build a docker volume definition for a local folder."""
    docker_dir = "/tmp/.X11-unix/" if isMatlab else "/usr/local/src/"
    return {
        Path(folder).absolute(): {
            "bind": f"{docker_dir}/{Path(folder).name}",
            "mode": "rw",
        }
    }


__all__ = ["available_images", "client", "get_volume", "wait_and_close_container"]
