"""Built-in hyperglass plugins."""

# Local
from .remove_command import RemoveCommand
from .bgp_route_arista import BGPRoutePluginArista
from .bgp_route_juniper import BGPRoutePluginJuniper
from .bgp_route_huawei import BGPRoutePluginHuawei
from .mikrotik_garbage_output import MikrotikGarbageOutput

__all__ = (
    "BGPRoutePluginArista",
    "BGPRoutePluginJuniper",
    "BGPRoutePluginHuawei",
    "MikrotikGarbageOutput",
    "RemoveCommand",
)
