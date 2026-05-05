from pathlib import Path
from ctos_drug_response_networks.config import load_config
from ctos_drug_response_networks.validators import validate_assets
from ctos_drug_response_networks.runner import reproduce


def test_fixture_assets_validate():
    config = load_config('config/fixture.yaml')
    report = validate_assets(config, config_path='config/fixture.yaml')
    assert report['status'] == 'ok'


def test_fixture_reproduce_all(tmp_path):
    config = load_config('config/fixture.yaml')
    validate_assets(config, config_path='config/fixture.yaml')
    outputs = reproduce(config, 'derived', ['fig2','fig3','fig4','fig5','fig6'], tmp_path)
    assert any(str(p).endswith('fig2.png') for p in outputs)
    assert any(str(p).endswith('fig6.png') for p in outputs)


def test_default_assets_validate():
    config = load_config('config/default.yaml')
    report = validate_assets(config, config_path='config/default.yaml')
    assert report['status'] == 'ok'


def test_default_reproduce_all(tmp_path):
    config = load_config('config/default.yaml')
    validate_assets(config, config_path='config/default.yaml')
    outputs = reproduce(config, 'derived', ['fig2','fig3','fig4','fig5','fig6'], tmp_path)
    expected = {'fig2.png', 'fig3.png', 'fig4.png', 'fig5.png', 'fig6.png'}
    produced = {Path(p).name for p in outputs if p.endswith('.png')}
    assert expected.issubset(produced)
