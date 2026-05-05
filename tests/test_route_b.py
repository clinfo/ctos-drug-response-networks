import pytest
from ctos_drug_response_networks.config import load_config
from ctos_drug_response_networks.route_b import describe_route_b, handle_raw_route
from ctos_drug_response_networks.errors import UnsupportedRouteError


def test_route_b_description_mentions_documented_boundary():
    config = load_config('config/default.yaml')
    text = describe_route_b(config)
    assert 'optional' in text.lower()
    assert 'does not promise' in text.lower()


def test_route_b_execution_fails_explicitly():
    config = load_config('config/default.yaml')
    with pytest.raises(UnsupportedRouteError):
        handle_raw_route(config)
