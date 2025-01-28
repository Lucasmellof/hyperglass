"""Coerce a Juniper route table in XML format to a standard BGP Table structure."""

# Standard Library
from typing import TYPE_CHECKING, List, Sequence, Dict

# Third Party
from pydantic import PrivateAttr

# Project
from hyperglass.log import log
from hyperglass.exceptions.private import ParsingError
from hyperglass.models.parsing.huawei import HuaweiBGPTable

# Local
from .._output import OutputPlugin

if TYPE_CHECKING:
    # Project
    from hyperglass.models.data import OutputDataModel
    from hyperglass.models.api.query import Query

    # Local
    from .._output import OutputType


REMOVE_PATTERNS = (
    # The XML response can a CLI banner appended to the end of the XML
    # string. For example:
    # ```
    # <rpc-reply>
    # ...
    # <cli>
    #   <banner>{master}</banner>
    # </cli>
    # </rpc-reply>
    #
    # {master} noqa: E800
    # ```
    #
    # This pattern will remove anything inside braces, including the braces.
    r"\{.+\}",
)


def _parse_paths(line: str) -> Dict:
    """Paths:   5 available, 1 best, 1 select, 0 best-external, 0 add-path."""
    if not line.startswith(" Paths:   "):
        return None

    available = 0
    best = 0
    select = 0
    best_external = 0
    add_path = 0

    values = line[len(" Paths:   ") :].split(",")
    for value in values:
        value, path_type = value.strip().split(" ")
        if "available" in path_type:
            available = int(value)
        if "best" in path_type:
            best = int(value)
        if "select" in path_type:
            select = int(value)
        if "best-external" in path_type:
            best_external = int(value)
        if "add-path" in path_type:
            add_path = int(value)

    return {
        "available": available,
        "best": best,
        "select": select,
        "best_external": best_external,
        "add_path": add_path,
    }


def remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def _parse_routes(lines: List[str]) -> Dict:
    """example:
    BGP routing table entry information of 1.1.1.0/24:
    From: 0.0.0.0 (0.0.0.0)
    Route Duration: 9d22h50m28s
    Direct Out-interface: 100GE0/1/48.510
    Original nexthop: 0.0.0.0
    Qos information : 0x0
    Community: <13335:10097>, <13335:19010>, <13335:20050>, <13335:20500>, <13335:20530>, <65444:4000>
    AS-path 263444 13335, origin igp, pref-val 0, valid, external, pre 100, not preferred for router ID
    Aggregator: AS 13335, Aggregator ID 10.34.36.100
    Not advertised to any peer yet (or Advertised to such 3 peers:)
       0.0.0.0
    """

    # if not line.startswith(" BGP routing table entry information of "):
    # return None

    for i, l in enumerate(lines):
        print(i, l)

    routes = []
    try:

        size = lines.__len__()
        idx_list = [idx + 1 for idx, val in enumerate(lines) if val == ""]
        entries = (
            [
                lines[i:j]
                for i, j in zip([0] + idx_list, idx_list + ([size] if idx_list[-1] != size else []))
            ]
            if idx_list
            else [lines]
        )

        for route_entry in entries:
            prefix = ""  # BGP routing table entry information of
            from_addr = ""  # From:
            duration = 0  # Route Duration:
            direct_out_interface = ""
            original_next_hop = ""
            relay_ip_next_hop = ""
            relay_ip_out_interface = ""
            qos = ""
            communities = []
            large_communities = []
            ext_communities = []
            as_path = []
            origin = ""
            metric = 0  # MED
            local_preference = 0
            preference_value = 0
            is_valid = False
            is_external = False
            is_backup = False
            is_best = False
            is_selected = False
            preference = 0

            for info in route_entry:
                info = info.strip()
                if info.startswith("BGP routing table entry information of"):
                    prefix = remove_prefix(info, "BGP routing table entry information of ")[:-1]
                elif info.startswith("From:"):
                    from_addr = remove_prefix(info, "From: ").split(" (")[0]
                elif info.startswith("Route Duration:"):
                    d = (
                        remove_prefix(info, "Route Duration: ")
                        .replace("d", " ")
                        .replace("h", " ")
                        .replace(
                            "m",
                            " ",
                        )
                        .replace("s", "")
                        .split(" ")
                    )
                    duration = (
                        int(d[0]) * 24 * 60 * 60 + int(d[1]) * 60 * 60 + int(d[2]) + 60 + int(d[3])
                    )
                elif info.startswith("Direct Out-interface:"):
                    direct_out_interface = remove_prefix(info, "Direct Out-interface: ")
                elif info.startswith("Original nexthop:"):
                    original_next_hop = remove_prefix(info, "Original nexthop: ")
                elif info.startswith("Relay IP Nexthop:"):
                    relay_ip_next_hop = remove_prefix(info, "Relay IP Nexthop: ")
                elif info.startswith("Relay IP Out-Interface:"):
                    relay_ip_out_interface = remove_prefix(info, "Relay IP Out-Interface: ")
                elif info.startswith("Qos information :"):
                    qos = remove_prefix(info, "Qos information : ")
                elif info.startswith("Community:"):
                    communities = remove_prefix(info, "Community: ").split(", ")
                    for i in range(len(communities)):
                        communities[i] = communities[i].replace("<", "").replace(">", "")
                elif info.startswith("Large-Community:"):
                    large_communities = remove_prefix(info, "Large-Community: ").split(", ")
                    for i in range(len(large_communities)):
                        large_communities[i] = large_communities[i].replace("<", "").replace(">", "")
                elif info.startswith("Ext-Community:"):
                    ext_communities = remove_prefix(info, "Ext-Community: ").split(", ")
                    for i in range(len(ext_communities)):
                        ext_communities[i] = ext_communities[i].replace("<", "").replace(">", "")
                elif info.startswith("AS-path"):
                    values = info.split(",")
                    for v in values:
                        v = v.strip()
                        if v.startswith("AS-path"):
                            as_path_raw = remove_prefix(v, "AS-path ")
                            if as_path_raw == "Nil":
                                as_path = []
                            else:
                                as_path = [int(a) for a in as_path_raw.split(" ")]
                        elif v.startswith("origin"):
                            origin = remove_prefix(v, "origin ")
                        elif v.startswith("MED"):
                            metric = int(remove_prefix(v, "MED "))
                        elif v.startswith("localpref"):
                            local_preference = int(remove_prefix(v, "localpref "))
                        elif v.startswith("pref-val"):
                            preference_value = int(remove_prefix(v, "pref-val "))
                        elif v.startswith("valid"):
                            is_valid = True
                        elif v.startswith("external"):
                            is_external = True
                        elif v.startswith("backup"):
                            is_backup = True
                        elif v.startswith("best"):
                            is_best = True
                        elif v.startswith("select"):
                            is_selected = True
                        elif v.startswith("pre"):
                            preference = int(remove_prefix(v, "pre "))

                #  Advertised to such 1 peers:
                #     0.0.0.0

            routes.append(
                {
                    "prefix": prefix,
                    "from_addr": from_addr,
                    "duration": duration,
                    "direct_out_interface": direct_out_interface,
                    "original_next_hop": original_next_hop,
                    "relay_ip_next_hop": relay_ip_next_hop,
                    "relay_ip_out_interface": relay_ip_out_interface,
                    "qos": qos,
                    "communities": communities,
                    "large_communities": large_communities,
                    "ext_communities": ext_communities,
                    "as_path": as_path,
                    "origin": origin,
                    "metric": metric,
                    "local_preference": local_preference,
                    "preference_value": preference_value,
                    "is_valid": is_valid,
                    "is_external": is_external,
                    "is_backup": is_backup,
                    "is_best": is_best,
                    "is_selected": is_selected,
                    "preference": preference,
                }
            )
    except Exception as err:
            print(err)
            routes = None

    return routes


def parse_huawei(raw_ouput: tuple[str, str]) -> "OutputDataModel":  # noqa: C901
    """Parse a Huawei BGP response."""
    result = None

    output = raw_ouput[0]

    parsed = {}

    _log = log.bind(plugin=BGPRoutePluginHuawei.__name__)

    try:
        lines: List[str] = output.splitlines()
        if lines.__len__() < 5:
            raise ParsingError("Failed to parse Huawei BGP route table.")

        if lines[1].startswith(" BGP local router ID"):
            parsed["local_router_id"] = lines[1].split(":")[1].strip()
        if lines[2].startswith(" Local AS number"):
            parsed["local_as_number"] = lines[2].split(":")[1].strip()

        paths = _parse_paths(lines[3])
        if paths is not None:
            parsed["paths"] = paths

        routes = _parse_routes(lines[4:])
        if routes is not None:
            parsed["routes"] = routes

        print(parsed)
        validated = HuaweiBGPTable(**parsed)
        result = validated.bgp_table()
    except Exception as err:
        print(err)
        _log.bind(error=str(err)).critical("Failed to parse Huawei BGP route table.")

    return result


class BGPRoutePluginHuawei(OutputPlugin):
    """Coerce a Juniper route table in XML format to a standard BGP Table structure."""

    _hyperglass_builtin: bool = PrivateAttr(True)
    platforms: Sequence[str] = ("huawei",)
    directives: Sequence[str] = (
        "__hyperglass_huawei_bgp_route_table__",
        "__hyperglass_huawei_bgp_aspath_table__",
        "__hyperglass_huawei_bgp_community_table__",
    )

    def process(self, *, output: "OutputType", query: "Query") -> "OutputType":
        """Parse Huawei response if data is a string (and is therefore unparsed)."""
        should_process = all(
            (
                isinstance(output, (list, tuple)),
                query.device.platform in self.platforms,
                query.device.structured_output is True,
                query.device.has_directives(*self.directives),
            )
        )
        if should_process:
            return parse_huawei(output)
        return output
