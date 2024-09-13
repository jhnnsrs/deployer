import asyncio
import datetime
import os
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict
import xarray as xr
import numpy as np
from docker import DockerClient, from_env

from arkitekt_next import background, context, easy, register, startup
from kabinet.api.schema import (
    Backend,
    Deployment,
    Pod,
    PodStatus,
    Release,
    adeclare_backend,
    adump_logs,
    aupdate_pod,
    create_deployment,
    create_pod,
    delete_pod,
)
from mikro_next.api.schema import Image, from_array_like
from rekuest_next.actors.reactive.api import (
    progress,
    log,
    useInstanceID,
)
from unlok_next.api.schema import (
    DevelopmentClientInput,
    ManifestInput,
    Requirement,
    create_client,
)

# Connect to local Docker

ME = os.getenv("INSTANCE_ID", "FAKE GOD")
ARKITEKT_GATEWAY = os.getenv("ARKITEKT_GATEWAY", "caddy")
ARKITEKT_NETWORK = os.getenv("ARKITEKT_NETWORK", "next_default")


@context
@dataclass
class ArkitektContext:
    backend: Backend
    docker: DockerClient
    instance_id: str
    gateway: str = field(default=ARKITEKT_GATEWAY)
    network: str = field(default=ARKITEKT_NETWORK)


@startup
async def on_startup(instance_id) -> ArkitektContext:
    print("Starting up")
    print("Check sfosr scontainers that are no longer pods?")

    x = await adeclare_backend(instance_id=instance_id, name="Docker", kind="apptainer")

    return ArkitektContext(
        docker=from_env(),
        gateway=ARKITEKT_GATEWAY,
        network=ARKITEKT_NETWORK,
        backend=x,
        instance_id=instance_id,
    )


@background
async def container_checker(context: ArkitektContext):
    print("Starting dup")
    print("Check for containers that are dno longer pods?")

    pod_status: Dict[str, PodStatus] = {}

    while True:
        docker = context.docker

        my_containers = []
        container = docker.containers.list(all=True)
        for c in container:
            if "arkitekt.live.kabinet" in c.labels:
                classifier = c.labels["arkitekt.live.kabinet"]
                if classifier != ME:
                    continue
                my_containers.append(c)

        for container in my_containers:
            try:
                old_status = pod_status.get(container.id, None)
                if container.status != old_status:
                    p = await aupdate_pod(
                        local_id=container.id,
                        status=PodStatus.RUNNING
                        if container.status == "running"
                        else PodStatus.STOPPED,
                        instance_id=context.instance_id,
                    )

                    pod_status[container.id] = container.status
                    print("Updated Container Status")

                    logs = container.logs(tail=60)
                    await adump_logs(p.id, logs.decode("utf-8"))
            except Exception as e:
                print("Error updating pod status", e)
                container.stop()
                container.remove()

        await asyncio.sleep(5)


@register(name="dump_logs")
async def dump_logs(context: ArkitektContext, pod: Pod) -> Pod:
    print(pod.pod_id)
    print(context.docker.containers.list())
    container = context.docker.containers.get(pod.pod_id)
    print("Getting logs")
    logs = container.logs(tail=60)
    print("Dumping logs")
    await adump_logs(pod.id, logs.decode("utf-8"))

    return pod


@register(name="Runner")
def run(deployment: Deployment, context: ArkitektContext) -> Pod:
    print(deployment)
    container = context.docker.containers.run(
        deployment.local_id, detach=True, labels={"arkitekt.live.kabinet": ME}
    )

    z = create_pod(
        deployment=deployment, instance_id=useInstanceID(), local_id=container.id
    )

    print(z)
    return z


@register(name="Restart")
def restart(pod: Pod, context: ArkitektContext) -> Pod:
    """Restart

    Restarts a pod by stopping and starting it again.


    """

    print("Running")
    container = context.docker.containers.get(pod.pod_id)

    progress(50)
    container.restart()
    progress(100)
    return pod


@register(name="Move")
def move(pod: Pod) -> Pod:
    """Move"""
    print("Moving node")

    progress(0)

    # Simulating moving a node
    for i in range(10):
        progress(i * 10)
        time.sleep(1)

    return pod


@register(name="Stop")
def stop(pod: Pod, context: ArkitektContext) -> Pod:
    """Stop

    Stops a pod by stopping and does not start it again.


    """

    print("Running")
    container = context.docker.containers.get(pod.pod_id)

    container.stop()

    return pod


@register(name="Removedd")
def remove(pod: Pod, context: ArkitektContext) -> Pod:
    """Remove

    Remove a pod by stopping and removing it.


    """

    print("Running")
    try:
        container = context.docker.containers.get(pod.pod_id)

        container.remove()
    except Exception as e:
        log(e)
        print(e)

    delete_pod(pod.id)

    return pod


@register(name="Deploy")
def deploy(release: Release, context: ArkitektContext) -> Pod:
    print(release)
    docker: DockerClient = context.docker
    caddy_url = context.gateway
    network = context.network

    flavour = release.flavours[0]

    progress(0)

    print("OAINDFOAIWNDOAINWDOIANWd")

    print(
        [Requirement(key=key, **value) for key, value in flavour.requirements.items()]
    )

    token = create_client(
        DevelopmentClientInput(
            manifest=ManifestInput(
                identifier=release.app.identifier,
                version=release.version,
                scopes=flavour.manifest["scopes"],
            ),
            requirements=[
                Requirement(key=key, **value)
                for key, value in flavour.requirements.items()
            ],
        )
    )

    print(docker.api.pull(flavour.image))

    progress(10)

    deployment = create_deployment(
        flavour=flavour,
        instance_id=useInstanceID(),
        local_id=flavour.image,
        last_pulled=datetime.datetime.now(),
    )

    progress(30)

    print(os.getenv("ARKITEKT_GATEWAY"))

    # COnver step here for apptainer

    container = docker.containers.run(
        flavour.image,
        detach=True,
        labels={
            "arkitekt.live.kabinet": ME,
            "arkitekt.live.kabinet.deployment": deployment.id,
        },
        environment={"FAKTS_TOKEN": token},
        command=f"arkitekt-next run prod --token {token} --url {caddy_url}",
        network=network,
    )

    print("Deployed container on network", network, token, caddy_url, container.name)

    progress(90)

    z = create_pod(
        deployment=deployment, instance_id=useInstanceID(), local_id=container.id
    )

    return z


@register(name="Progresso")
def progresso():
    for i in range(10):
        print("Sending progress")
        progress(i * 10)
        time.sleep(1)

    return None
