"""Tests for the deferred Higgsfield integration foundation."""

from __future__ import annotations

import unittest

from tools.media.sakhalin.higgsfield_config import (
    HiggsfieldConfig,
    HiggsfieldConfigError,
)
from tools.media.sakhalin.higgsfield_provider import (
    HiggsfieldDisabledError,
    HiggsfieldProvider,
)
from tools.media.sakhalin.provider import GenerationKind, GenerationRequest


class HiggsfieldConfigTests(unittest.TestCase):
    def test_disabled_without_credentials_is_valid(self) -> None:
        config = HiggsfieldConfig.from_env({})
        self.assertFalse(config.enabled)
        self.assertFalse(config.has_credentials)

    def test_enabled_without_credentials_fails_closed(self) -> None:
        with self.assertRaises(HiggsfieldConfigError):
            HiggsfieldConfig.from_env({"HIGGSFIELD_ENABLED": "true"})

    def test_mixed_credential_forms_are_rejected(self) -> None:
        with self.assertRaises(HiggsfieldConfigError):
            HiggsfieldConfig.from_env(
                {
                    "HF_KEY": "id:secret",
                    "HF_API_KEY": "id",
                    "HF_API_SECRET": "secret",
                }
            )

    def test_partial_key_pair_is_rejected(self) -> None:
        with self.assertRaises(HiggsfieldConfigError):
            HiggsfieldConfig.from_env({"HF_API_KEY": "id"})


class HiggsfieldProviderTests(unittest.TestCase):
    def test_submit_is_blocked_when_disabled(self) -> None:
        provider = HiggsfieldProvider(HiggsfieldConfig.from_env({}))
        request = GenerationRequest(
            request_key="test-shot-001",
            kind=GenerationKind.IMAGE,
            prompt="Sakhalin coast at sunrise",
            model="example/model",
            max_cost_usd=1.0,
        )

        with self.assertRaises(HiggsfieldDisabledError):
            provider.submit(request)


class GenerationRequestTests(unittest.TestCase):
    def test_budget_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            GenerationRequest(
                request_key="test-shot-002",
                kind=GenerationKind.VIDEO,
                prompt="A lighthouse in fog",
                model="example/model",
                max_cost_usd=0,
            )


if __name__ == "__main__":
    unittest.main()
