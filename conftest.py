import pytest
import config

# global tweaks for all pytesting
@pytest.fixture(scope="session", autouse=True)
def tweak_global_config():
    config.disable_signature_checking = False
    
