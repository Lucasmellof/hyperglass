"""Validate SSH proxy configuration variables."""

# Standard Library
from typing import Any, Dict, Union
from ipaddress import IPv4Address, IPv6Address

# Third Party
from pydantic import StrictInt, StrictStr, validator

# Project
from hyperglass.util import resolve_hostname
from hyperglass.exceptions.private import ConfigError, UnsupportedDevice

# Local
from ..main import HyperglassModel
from ..util import check_legacy_fields
from .credential import Credential


class Proxy(HyperglassModel):
    """Validation model for per-proxy config in devices.yaml."""

    name: StrictStr
    address: Union[IPv4Address, IPv6Address, StrictStr]
    port: StrictInt = 22
    credential: Credential
    type: StrictStr = "linux_ssh"

    def __init__(self: "Proxy", **kwargs: Any) -> None:
        """Check for legacy fields."""
        kwargs = check_legacy_fields("Proxy", **kwargs)
        super().__init__(**kwargs)

    @property
    def _target(self):
        return str(self.address)

    @validator("address")
    def validate_address(cls, value, values):
        """Ensure a hostname is resolvable."""

        if not isinstance(value, (IPv4Address, IPv6Address)):
            if not any(resolve_hostname(value)):
                raise ConfigError(
                    "Device '{d}' has an address of '{a}', which is not resolvable.",
                    d=values["name"],
                    a=value,
                )
        return value

    @validator("type", pre=True, always=True)
    def validate_type(cls: "Proxy", value: Any, values: Dict[str, Any]) -> str:
        """Validate device type."""

        if value != "linux_ssh":
            raise UnsupportedDevice(
                "Proxy '{p}' uses type '{t}', which is currently unsupported.",
                p=values["name"],
                t=value,
            )
        return value
