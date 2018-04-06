from baka_tenshi.config import CONFIG as tenshi
from baka_armor.config import CONFIG as armor


def includeme(config):
    # untuk config env baka-tenshi
    config.add_config_validator(yaml=armor)
    config.add_config_validator(yaml=tenshi)
