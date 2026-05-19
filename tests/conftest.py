"""Shared test fixtures and helpers for the salesforce-fastmcp test suite."""

import pytest


class MockSF:
    """
    Lightweight in-process Salesforce mock.

    Supply a dict of {keyword: response} where keyword is a substring that
    will be searched in the SOQL string.  The first matching key wins.

    If no key matches, a ValueError is raised to make test failures obvious.
    """

    def __init__(self, handlers: dict[str, dict]):
        self._handlers = handlers
        self.call_log: list[str] = []

    async def query(self, soql: str) -> dict:
        self.call_log.append(soql)
        for keyword, response in self._handlers.items():
            if keyword in soql:
                return response
        raise ValueError(
            f"MockSF: no handler matched SOQL.\nQuery: {soql!r}\n"
            f"Available keywords: {list(self._handlers.keys())}"
        )


def soql_response(records: list[dict], *, done: bool = True) -> dict:
    """Build a minimal SOQL query response envelope."""
    return {"totalSize": len(records), "done": done, "records": records}


def agg_response(row: dict) -> dict:
    """Convenience wrapper for single-row aggregate queries."""
    return soql_response([row])
