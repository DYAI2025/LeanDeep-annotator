"""Pytest configuration — ensure test environment settings."""

import os

# Disable auth for tests (production default is auth=enabled)
os.environ.setdefault("LEANDEEP_REQUIRE_AUTH", "false")
