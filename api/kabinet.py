from pydantic import Field, ConfigDict, BaseModel
from typing import Tuple, Literal, Optional
from kabinet.rath import KabinetRath
from kabinet.funcs import aexecute, execute
from rath.scalars import ID
from enum import Enum


class GetDetailDefinitionQueryDefinitionFlavours(BaseModel):
    """A user of the bridge server. Maps to an authentikate user"""

    typename: Literal["Flavour"] = Field(
        alias="__typename", default="Flavour", exclude=True
    )
    id: ID
    model_config = ConfigDict(frozen=True)


class GetDetailDefinitionQueryDefinition(BaseModel):
    """Nodes are abstraction of RPC Tasks. They provide a common API to deal with creating tasks.

    See online Documentation"""

    typename: Literal["Definition"] = Field(
        alias="__typename", default="Definition", exclude=True
    )
    id: ID
    flavours: Tuple[GetDetailDefinitionQueryDefinitionFlavours, ...]
    "The flavours this Definition belongs to"
    model_config = ConfigDict(frozen=True)


class GetDetailDefinitionQuery(BaseModel):
    definition: GetDetailDefinitionQueryDefinition
    "Return all dask clusters"

    class Arguments(BaseModel):
        definition: ID

    class Meta:
        document = "query GetDetailDefinition($definition: ID!) {\n  definition(id: $definition) {\n    id\n    flavours {\n      id\n      __typename\n    }\n    __typename\n  }\n}"


async def aget_detail_definition(
    definition: ID, rath: Optional[KabinetRath] = None
) -> GetDetailDefinitionQueryDefinition:
    """GetDetailDefinition

    Return all dask clusters

    Arguments:
        definition (ID): No description
        rath (kabinet.rath.KabinetRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        GetDetailDefinitionQueryDefinition
    """
    return (
        await aexecute(GetDetailDefinitionQuery, {"definition": definition}, rath=rath)
    ).definition


def get_detail_definition(
    definition: ID, rath: Optional[KabinetRath] = None
) -> GetDetailDefinitionQueryDefinition:
    """GetDetailDefinition

    Return all dask clusters

    Arguments:
        definition (ID): No description
        rath (kabinet.rath.KabinetRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        GetDetailDefinitionQueryDefinition
    """
    return execute(
        GetDetailDefinitionQuery, {"definition": definition}, rath=rath
    ).definition
