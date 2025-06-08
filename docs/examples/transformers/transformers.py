"""
---
title: Pokemon details in parallel using transformers
description: Learn how to use dlt transformers and how to speed up your loads with parallelism
keywords: [transformers, parallelism, example]
---

この例では、ポケモンの詳細情報を並列にロードするために、トランスフォーマーを利用して [PokeAPI](https://pokeapi.co/) からポケモンデータをロードします。

以下の方法を学習します。
- 2 つの [トランスフォーマー](../general-usage/resource.md#process-resources-with-dlttransformer) を作成し、パイプ演算子 `|` を使用してリソースに接続します。
- `@dlt.defer` デコレータを使用して [これらのトランスフォーマーを並列にロード](../reference/performance.md#parallelism-within-a-pipeline) します。
- `config.toml` ファイルで [並列処理を設定](../reference/performance.md#parallel-pipeline-config-example) します。
- メインリソースの選択を解除して、データベースにロードされないようにします。
- 自動再試行機能付きの事前構成済みの `requests` ライブラリをインポートして使用します (`from dlt.sources.helpers import requests`)。

"""

import dlt
from dlt.sources.helpers import requests


@dlt.source(max_table_nesting=2)
def source(pokemon_api_url: str):
    # note that we deselect `pokemon_list` - we do not want it to be loaded
    @dlt.resource(write_disposition="replace", selected=False)
    def pokemon_list():
        """Retrieve a first page of Pokemons and yield it. We do not retrieve all the pages in this example"""
        yield requests.get(pokemon_api_url).json()["results"]

    # transformer that retrieves a list of objects in parallel
    @dlt.transformer
    def pokemon(pokemons):
        """Yields details for a list of `pokemons`"""

        # @dlt.defer marks a function to be executed in parallel
        # in a thread pool
        @dlt.defer
        def _get_pokemon(_pokemon):
            return requests.get(_pokemon["url"]).json()

        # call and yield the function result normally, the @dlt.defer takes care of parallelism
        for _pokemon in pokemons:
            yield _get_pokemon(_pokemon)

    # a special case where just one item is retrieved in transformer
    # a whole transformer may be marked for parallel execution
    @dlt.transformer(parallelized=True)
    def species(pokemon_details):
        """Yields species details for a pokemon"""
        species_data = requests.get(pokemon_details["species"]["url"]).json()
        # link back to pokemon so we have a relation in loaded data
        species_data["pokemon_id"] = pokemon_details["id"]
        # You can return the result instead of yield since the transformer only generates one result
        return species_data

    # create two simple pipelines with | operator
    # 1. send list of pokemons into `pokemon` transformer to get pokemon details
    # 2. send pokemon details into `species` transformer to get species details
    # NOTE: dlt is smart enough to get data from pokemon_list and pokemon details once

    return (pokemon_list | pokemon, pokemon_list | pokemon | species)


if __name__ == "__main__":
    # build duck db pipeline
    pipeline = dlt.pipeline(
        pipeline_name="pokemon", destination="duckdb", dataset_name="pokemon_data"
    )

    # the pokemon_list resource does not need to be loaded
    load_info = pipeline.run(source("https://pokeapi.co/api/v2/pokemon"))
    print(load_info)

    # verify that all went well
    row_counts = pipeline.last_trace.last_normalize_info.row_counts
    assert row_counts["pokemon"] == 20
    assert row_counts["species"] == 20
    assert "pokemon_list" not in row_counts
