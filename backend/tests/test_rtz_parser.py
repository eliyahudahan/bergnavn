import os
from backend.services.rtz_parser import parse_rtz

def test_parse_oslo_sample():
    sample = os.path.join('backend','assets','routeinfo_routes','oslo','raw','oslo_routes.rtz')
    routes = parse_rtz(sample)
    assert isinstance(routes, list)
    assert len(routes) >= 1
    assert 'legs' in routes[0]
    # legs may be > 0
