import os
import logging
from typing import Any, Dict, Optional, Union, NoReturn

import yaml

from cornea.constants import CONFIG_LOCATION

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = \
f"""
# This is the default model directory. Changing this will alter where Cornea
# models are outputted to.
model_default_path: "./models"

# Uncomment this section if you are using PostgreSQL as a database
postgres:
    POSTGRES_DATABASE: "cornea"
    POSTGRES_USER: "cornea"
    POSTGRES_PASSWORD: "welcome"
    POSTGRES_HOST: "127.0.0.1"
    POSTGRES_PORT: 5432
"""


def _format_config_warning(config_path: str) -> str:
    return (f"\n\nNo config was found at: {config_path} so a new config "
            "file was created there.\nPlease open the config file and "
            "configure Cornea as needed before running again.\nThis warning "
            "will also appear if this is your first time running Cornea, as "
            "a\nconfiguration file will need to be generated for future "
            "launches.\n\nIf this message persists please visit: "
            "https://github.com/euab/cornea/issues")


def ensure_config_exists(config_path: str) -> Union[bool, NoReturn]:
    """
    Ensure the configuration file exists in the correct location.
    Create a new one if needed.

    Returns whether the configuration file is ready.
    """
    
    if os.path.isfile(config_path):
        return True
    
    logger.info("Unable to find configuration, creating a new file.")
    if not _write_default_config(config_path):
        logger.critical("Could not create default confiuration file.")
        exit(1)

    print(_format_config_warning(config_path))
    exit(1)


def _write_default_config(config_path: str) -> bool:
    try:
        with open(config_path, 'w') as config_file:
            config_file.write(DEFAULT_CONFIG)
    except OSError as e:
        logger.error(f"Could not write default configuration:\n{e}")
        return False
    
    return True


def load_config_file(config_path: Optional[str]) -> Dict[Any, Any]:
    if config_path is None:
        config_path = CONFIG_LOCATION

    if not ensure_config_exists(config_path):
        raise RuntimeError

    with open(config_path, "r") as config_file:    
        config_dict = yaml.safe_load(config_file)

    if not isinstance(config_dict, dict):
        msg = (
            f'The configuration file at {os.path.basename(config_path)}'
            ' does not contain a Python dictionary.'
        )
        logger.error(msg)
        raise RuntimeError(msg)
    
    for k, v in config_dict.items():
        config_dict[k] = v or {}
    
    return config_dict
