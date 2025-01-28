"""Data Models for Parsing Huawei Response."""

# Standard Library
import typing as t
from datetime import datetime

# Third Party
from pydantic import ConfigDict

# Project
from hyperglass.log import log
from hyperglass.models.data import BGPRouteTable

# Local
from ..main import HyperglassModel

RPKI_STATE_MAP = {
    "invalid": 0,
    "valid": 1,
    "notFound": 2,
    "notValidated": 3,
}


def _alias_generator(field: str) -> str:
    caps = "".join(x for x in field.title() if x.isalnum())
    return caps[0].lower() + caps[1:]


class _HuaweiBase(HyperglassModel):
    """Base Model for Huawei validation."""

    model_config = ConfigDict(extra="ignore", alias_generator=_alias_generator)


class HuaweiRoutePath(_HuaweiBase):
    """Validation model for Huawei bgpRoutePaths."""

    available: int
    best: int
    select: int
    best_external: int
    add_path: int


class HuaweiRouteEntry(_HuaweiBase):
    """Validation model for Huawei bgpRouteEntries."""

    prefix: str
    from_addr: str
    duration: int
    direct_out_interface: str
    original_next_hop: str
    relay_ip_next_hop: str
    relay_ip_out_interface: str
    qos: str
    communities: t.List[str] = []
    ext_communities: t.List[str] = []
    large_communities: t.List[str] = []
    as_path: t.List[int] = []
    origin: str
    metric: int = 0  # med
    local_preference: int
    preference_value: int
    is_valid: bool
    is_external: bool
    is_backup: bool
    is_best: bool
    is_selected: bool
    preference: int


class HuaweiBGPTable(_HuaweiBase):
    """Validation model for Huawei bgpRouteEntries data."""

    local_router_id: str
    local_as_number: int
    paths: HuaweiRoutePath
    routes: t.List[HuaweiRouteEntry] = []

    @staticmethod
    def _get_route_age(timestamp: int) -> int:
        now = datetime.utcnow()
        now_timestamp = int(now.timestamp())
        return now_timestamp - timestamp

    @staticmethod
    def _get_as_path(as_path: str) -> t.List[str]:
        if as_path == "":
            return []
        return [int(p) for p in as_path.split() if p.isdecimal()]

    def bgp_table(self: "HuaweiBGPTable") -> "BGPRouteTable":
        """Convert the Huawei-formatted fields to standard parsed data model."""
        routes = []
        count = 0
        for route in self.routes:
            count += 1
            routes.append(
                {
                    "prefix": route.prefix,
                    "active": route.is_selected,
                    "age": route.duration,
                    "weight": route.preference,
                    "med": route.metric,
                    "local_preference": route.local_preference,
                    "as_path": route.as_path,
                    "communities": route.communities + route.ext_communities + route.large_communities,
                    "next_hop": route.original_next_hop,
                    "source_as": 0,
                    "source_rid": "",
                    "peer_rid": route.from_addr,
                    "rpki_state": RPKI_STATE_MAP.get("valid")
                    if route.is_valid
                    else RPKI_STATE_MAP.get("unknown"),
                }
            )

            print(routes)

        serialized = BGPRouteTable(
            vrf="default",
            count=count,
            routes=routes,
            winning_weight="high",
        )

        log.bind(platform="huawei", response=repr(serialized)).debug("Serialized response")
        return serialized
