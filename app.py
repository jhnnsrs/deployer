from arkitekt_next import easy, register, startup, background
from kabinet.api.schema import (
    create_github_repo,
    match_flavour,
    EnvironmentInput,
    ContainerType,
    Pod,
    aupdate_pod,
    create_deployment,
    adeclare_backend,
    Deployment,
    Definition,
    create_pod,
    PodStatus,
    adump_logs,
    Release,
    Pod,
)
from rekuest_next.actors.reactive.api import aprogress, progress
from unlok_next.api.schema import (
    create_client,
    DevelopmentClientInput,
    ManifestInput,
    Requirement,
)
from docker import from_env, DockerClient
from rekuest_next.actors.reactive.api import useContext, useInstanceID
import datetime
import asyncio
from typing import Dict, AsyncGenerator
import os
# Connect to local Docker

ME = os.getenv("INSTANCE_ID", "inside_docker")


async def in_container_startup_hook():
    print(
        "Should inspect if container id and push this to the kabinet server, that it is active.. Maybe for longer"
    )
    return {}


@startup
async def on_startup(state):
    print("Starting up")
    print("Check for containers that are no longer pods?")

    x = await adeclare_backend(
        instance_id=state.get("instance_id"), name="Docker", kind="apptainer"
    )

    return {
        "docker": from_env(),
        "backend": x,
        "gateway": os.getenv("ARKITEKT_GATEWAY"),
        "network": os.getenv("ARKITEKT_NETWORK"),
    }


@background
async def container_checker(context):
    print("Starting up")
    print("Check for containers that are no longer pods?")

    pod_status: Dict[str, PodStatus] = {}

    while True:
        docker: DockerClient = context["docker"]

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
                        instance_id=context["instance_id"],
                    )

                    pod_status[container.id] = container.status
                    print("Updated Container Status")

                    logs = container.logs(tail=60)
                    await adump_logs(p.id, logs.decode("utf-8"))
            except:
                container.stop()
                container.remove()

        await asyncio.sleep(5)


@register(name="Install node")
def install_node(node_hash: str) -> Pod:
    env = EnvironmentInput(
        containerType=ContainerType.DOCKER
    )  # TODO: Retrieve this from the environment

    x = match_flavour([node_hash], env)

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

    print("Deployed container on network", network, token, caddy_url)

    progress(90)

    z = create_pod(
        deployment=deployment, instance_id=useInstanceID(), local_id=container.id
    )

    return z


@register(name="Install definition")
def install_definition(defi: Definition) -> Pod:
    """Install definition

    Installs a definition and returns the pod that is running it.


    """
    env = EnvironmentInput(
        containerType=ContainerType.DOCKER
    )  # TODO: Retrieve this from the environment

    x = match_flavour([node_hash], env)

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

    print("Deployed container on network", network, token, caddy_url)

    progress(90)

    z = create_pod(
        deployment=deployment, instance_id=useInstanceID(), local_id=container.id
    )

    return z


@register(name="Runner")
def run(deployment: Deployment) -> Pod:
    print(deployment)
    docker: DockerClient = useContext("docker")

    print("Running")
    container = docker.containers.run(
        deployment.local_id, detach=True, labels={"arkitekt.live.kabinet": ME}
    )

    z = create_pod(
        deployment=deployment, instance_id=useInstanceID(), local_id=container.id
    )

    print(z)
    return z


@register(name="Restart")
def restart(pod: Pod) -> Pod:
    """Restart

    Restarts a pod by stopping and starting it again.


    """
    docker: DockerClient = useContext("docker")

    print("Running")
    container = docker.containers.get(pod.pod_id)

    container.restart()

    return pod


@register(name="Move")
def move(pod: Pod) -> Pod:
    """Move"""
    print("Moving node")

    return pod


@register(name="Stop")
def stop(pod: Pod) -> Pod:
    """Stop

    Stops a pod by stopping and does not start it again.


    """
    docker: DockerClient = useContext("docker")

    print("Running")
    container = docker.containers.get(pod.pod_id)

    container.stop()

    return pod


@register(name="Remove")
def remove(pod: Pod) -> Pod:
    """Remove

    Remove a pod by stopping and removing it.


    """
    docker: DockerClient = useContext("docker")

    print("Running")
    container = docker.containers.get(pod.pod_id)

    container.remove()

    return pod


@register(name="Deploy")
def deploy(release: Release) -> Pod:
    print(release)
    docker: DockerClient = useContext("docker")
    caddy_url = useContext("gateway")
    network = useContext("network")

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

    print("Deployed container on network", network, token, caddy_url)

    progress(90)

    z = create_pod(
        deployment=deployment, instance_id=useInstanceID(), local_id=container.id
    )

    return z


@register(name="Yielder")
async def yielder(number: int) -> AsyncGenerator[int, None]:
    while True:
        print("yielding")
        yield 4
        await asyncio.sleep(2)


@register(name="Installer")
async def installer(number: int) -> AsyncGenerator[int, None]:
    for i in range(10):
        await aprogress(0.1 * i)
        await asyncio.sleep(1)

    return 10
