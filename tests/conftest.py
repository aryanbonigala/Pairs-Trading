import importlib.util

import pytest


def pytest_configure(config: pytest.Config) -> None:
	# Register custom markers
	config.addinivalue_line("markers", "slow: marks tests as slow (deselect with -m 'not slow')")


@pytest.fixture(scope="session")
def internet_and_yfinance() -> bool:
	"""Skip tests cleanly if yfinance is missing or there is no internet.

	Returns True if environment looks OK for integration tests.
	"""
	if importlib.util.find_spec("yfinance") is None:
		pytest.skip("yfinance not installed; skipping integration test")
	try:
		import requests  # type: ignore
		requests.get("https://query1.finance.yahoo.com", timeout=3)
	except Exception:
		pytest.skip("No internet connectivity; skipping integration test")
	return True
