import json
from pathlib import Path

import pytest

from betka import config


class TestConfig:
    def test_dict_merge(self):
        dct = {"a": 1, "b": {"b1": 2, "b2": 3}}
        merge_dct = {"a": 1, "b": {"b1": 4}}

        config.dict_merge(dct, merge_dct)
        assert dct["a"] == 1
        assert dct["b"]["b1"] == 4
        assert dct["b"]["b2"] == 3

        merge_dct = {"a": 1, "b": {"b1": 4, "b3": 5}, "c": 6}

        config.dict_merge(dct, merge_dct)
        assert dct["a"] == 1
        assert dct["b"]["b1"] == 4
        assert dct["b"]["b2"] == 3
        assert dct["b"]["b3"] == 5
        assert dct["c"] == 6

    @pytest.mark.parametrize(
        "bot_cfg_path",
        [
            Path(__file__).parent.parent / "data/bot-configs/bot-cfg.yml",
            Path(__file__).parent.parent / "data/bot-configs/bot-cfg-old-keys.yml",
        ],
    )
    def test_load_configuration(self, bot_cfg_path):
        from_file = config.load_configuration(conf_path=bot_cfg_path)
        from_string = config.load_configuration(conf_str=bot_cfg_path.read_text())
        assert from_file == from_string

        # no arguments -> default config
        assert config.load_configuration()

        with pytest.raises(AttributeError):
            config.load_configuration("both args", "specified")

        with pytest.raises(AttributeError):
            config.load_configuration(conf_path="/does/not/exist")

    def test_load_configuration_with_aliases(self):
        my = {"version": "2", "betka": {"enabled": False}}
        conf = config.load_configuration(conf_str=json.dumps(my))
        # our 'betka' key has been merged into default's 'upstream-to-downstream' key
        assert conf["upstream-to-downstream"]["enabled"] is False

    @pytest.mark.parametrize(
        "cfg_url",
        ["https://github.com/sclorg/betka/raw/master/examples/cfg/bot-cfg.yml"],
    )
    def test_fetch_config(self, cfg_url):
        c1 = config.fetch_config("betka", cfg_url)
        c2 = config.fetch_config("upstream-to-downstream", cfg_url)
        assert c1 == c2
        # make sure the 'global' key has been merged into all bots` keys
        assert "notifications" in c1

    def test_get_from_bot_config(self):
        assert config.get_from_bot_config("emails", "sender")
        assert config.get_from_bot_config("pagure", "host")

    def test_betka_config_ok(self):
        path = Path(__file__).parent.parent / "data/configs/ok-config"
        conf = config.bot_config(path)
        assert conf["emails"]["smtp_server"] == "elm.street"
        assert conf["pagure"]["host"] == "test"

    @pytest.mark.parametrize(
        "data_path", ["no-config/", "empty-config/", "list-but-no-deployment/"]
    )
    def test_betka_config_not_ok(self, data_path):
        path = Path(__file__).parent.parent / "data/configs/" / data_path
        with pytest.raises(Exception):
            config.bot_config(path)
