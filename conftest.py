import pytest
import config
import gnupg
import logging

logging.basicConfig(level = logging.DEBUG)

# global tweaks for all pytesting
@pytest.fixture(scope="session", autouse=True)
def tweak_global_config():
    config.disable_signature_checking = False
    gnupg.logger.setLevel(logging.INFO)

    #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
