"""Safe environment configuration for the Higgsfield adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional


class HiggsfieldConfigError(ValueError):
    """Invalid or unsafe Higgsfield configuration."""


@dataclass(frozen=True)
class HiggsfieldConfig:
    """Validated Higgsfield configuration.

    Generation stays disabled unless HIGGSFIELD_ENABLED is explicitly true.
    """

    enabled: bool
    combined_key: Optional[str]
    api_key: Optional[str]
    api_secret: Optional[str]

    @property
    def has_credentials(self) -> bool:
        return bool(self.combined_key or (self.api_key and self.api_secret))

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> "HiggsfieldConfig":
        source = os.environ if env is None else env
        enabled = source.get("HIGGSFIELD_ENABLED", "false").strip().lower() == "true"

        combined = _clean(source.get("HF_KEY"))
        api_key = _clean(source.get("HF_API_KEY"))
        api_secret = _clean(source.get("HF_API_SECRET"))

        if combined and (api_key or api_secret):
            raise HiggsfieldConfigError(
                "Configure HF_KEY or HF_API_KEY/HF_API_SECRET, not both"
            )

        if bool(api_key) != bool(api_secret):
            raise HiggsfieldConfigError(
                "HF_API_KEY and HF_API_SECRET must be configured together"
            )

        config = cls(
            enabled=enabled,
            combined_key=combined,
            api_key=api_key,
            api_secret=api_secret,
        )

        if config.enabled and not config.has_credentials:
            raise HiggsfieldConfigError(
                "Higgsfield is enabled but credentials are missing"
            )

        return config


def _clean(value: str | None) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
