"""
---
title: Use custom yaml file for config and secrets
description: We show how to keep configuration in yaml file with switchable profiles and simple templates
keywords: [config, yaml config, profiles]
---

この例では、シークレット/設定 toml ファイルを、複数のプロファイル（prod と dev）と、対応する環境変数に置き換えられる jinja 風のプレースホルダーを含む yaml ファイルに置き換える方法を示します。
`dlt` は、いわゆる設定プロバイダー（つまり、環境変数または toml ファイルの内容を照会する）を照会することで設定を解決します。
ここでは、カスタムローダーを使用してプロバイダーをインスタンス化し、照会できるように登録します。最後に、`dlt` が他の（標準）プロバイダーとともにそれを使用して設定を解決する様子を（モック github ソースを使用して）示します。

この例では、次のことを学習します。

* yaml ファイルを解析、操作し、最終的な Python 辞書を返すカスタム設定ローダーを実装する
* ローダーからカスタムプロバイダー（CustomLoaderDocProvider）をインスタンス化する
* 照会できるようにプロバイダーインスタンスを登録する

"""

import os
import re
import dlt
import yaml
import functools

from dlt.common.configuration.providers import CustomLoaderDocProvider
from dlt.common.utils import map_nested_values_in_place


# config for all resources found in this file will be grouped in this source level config section
__source_name__ = "github_api"


def eval_placeholder(value):
    """Replaces jinja placeholders {{ PLACEHOLDER }} with environment variables"""
    if isinstance(value, str):

        def replacer(match):
            return os.environ[match.group(1)]

        return re.sub(r"\{\{\s*(\w+)\s*\}\}", replacer, value)
    return value


def loader(profile_name: str):
    """Loads yaml file from profiles.yaml in current working folder, selects profile, replaces
    placeholders with env variables and returns Python dict with final config
    """
    path = os.path.abspath("profiles.yaml")
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # get the requested environment
    config = config.get(profile_name, None)
    if config is None:
        raise RuntimeError(f"Profile with name {profile_name} not found in {os.path.abspath(path)}")
    # evaluate all placeholders
    # NOTE: this method only works with placeholders wrapped as strings in yaml. use jinja lib for real templating
    return map_nested_values_in_place(eval_placeholder, config)


@dlt.resource
def github(url: str = dlt.config.value, api_key=dlt.secrets.value):
    # just return the injected config and secret
    yield url, api_key


if __name__ == "__main__":
    # mock env variables to fill placeholders in profiles.yaml
    os.environ["GITHUB_API_KEY"] = "secret_key"  # mock expected var

    # dlt standard providers work at this point (we have profile name in config.toml)
    profile_name = dlt.config["dlt_config_profile_name"]

    # instantiate custom provider using `prod` profile
    # NOTE: all placeholders (ie. GITHUB_API_KEY) will be evaluated in next line!
    provider = CustomLoaderDocProvider("profiles", functools.partial(loader, profile_name))
    # register provider, it will be added as the last one in chain
    dlt.config.register_provider(provider)

    # your pipeline will now be able to use your yaml provider
    # p = Pipeline(...)
    # p.run(...)

    # show the final config
    print(provider.to_yaml())
    # or if you like toml
    print(provider.to_toml())

    # inject && evaluate resource
    config_vals = list(github())
    print(config_vals)
    assert config_vals[0] == ("https://github.com/api", "secret_key")
