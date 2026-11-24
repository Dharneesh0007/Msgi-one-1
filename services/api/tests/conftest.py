"""
MSGI One — Pytest Module-Level Isolation Fixtures
Prevents cross-module state pollution across shared in-memory dev stores while preserving
intra-module sequential test workflows (e.g. create -> accept -> list within one test file).
"""

import copy
import pytest

from src.services import mentor_service, alumni_service

_PRISTINE_MENTORS = copy.deepcopy(mentor_service._MENTORS_STORE)
_PRISTINE_MENTOR_REQUESTS = copy.deepcopy(mentor_service._MENTOR_REQUESTS_STORE)
_PRISTINE_ALUMNI = copy.deepcopy(alumni_service._SYNTHETIC_ALUMNI_STORE)


@pytest.fixture(autouse=True, scope="module")
def isolate_shared_stores_per_module():
    mentor_service._MENTORS_STORE[:] = copy.deepcopy(_PRISTINE_MENTORS)
    mentor_service._MENTOR_REQUESTS_STORE.clear()
    mentor_service._MENTOR_REQUESTS_STORE.update(copy.deepcopy(_PRISTINE_MENTOR_REQUESTS))
    alumni_service._SYNTHETIC_ALUMNI_STORE[:] = copy.deepcopy(_PRISTINE_ALUMNI)
    yield
    mentor_service._MENTORS_STORE[:] = copy.deepcopy(_PRISTINE_MENTORS)
    mentor_service._MENTOR_REQUESTS_STORE.clear()
    mentor_service._MENTOR_REQUESTS_STORE.update(copy.deepcopy(_PRISTINE_MENTOR_REQUESTS))
    alumni_service._SYNTHETIC_ALUMNI_STORE[:] = copy.deepcopy(_PRISTINE_ALUMNI)
