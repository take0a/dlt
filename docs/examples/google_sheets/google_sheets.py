"""
---
title: Google Sheets minimal example
description: Learn how work with Google services
keywords: [google sheets, credentials, example]
---

この例では、`dlt` ライブラリを使用して Google スプレッドシートのデータを読み込む方法を示す Python スクリプトを紹介します。

以下の方法を学習します。
- [組み込み認証情報](../general-usage/credentials/complex_types#gcp-credentials);
- [認証情報の結合](../general-usage/credentials/complex_types#working-with-alternatives-of-credentials-union-types);
- [動的に生成されるリソース](../general-usage/source#create-resources-dynamically);

:::tip
この例は教育目的です。ベストプラクティスとして、[Google スプレッドシートの検証済みソース](../dlt-ecosystem/verified-sources/google_sheets.md) の使用をお勧めします。
:::

"""

# NOTE: this line is only for dlt CI purposes, you may delete it if you are using this example
__source_name__ = "google_sheets"

from typing import Any, Iterator, Sequence, Union, cast

from googleapiclient.discovery import build

import dlt
from dlt.common.configuration.specs import (
    GcpOAuthCredentials,
    GcpServiceAccountCredentials,
)
from dlt.common.typing import DictStrAny, StrAny


def _initialize_sheets(
    credentials: Union[GcpOAuthCredentials, GcpServiceAccountCredentials]
) -> Any:
    # Build the service object.
    service = build("sheets", "v4", credentials=credentials.to_native_credentials())
    return service


@dlt.source
def google_spreadsheet(
    spreadsheet_id: str,
    sheet_names: Sequence[str],
    credentials: Union[
        GcpServiceAccountCredentials, GcpOAuthCredentials, str, StrAny
    ] = dlt.secrets.value,
) -> Any:
    sheets = _initialize_sheets(cast(GcpServiceAccountCredentials, credentials))

    def get_sheet(sheet_name: str) -> Iterator[DictStrAny]:
        # get list of list of typed values
        result = (
            sheets.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name,
                # unformatted returns typed values
                valueRenderOption="UNFORMATTED_VALUE",
                # will return formatted dates
                dateTimeRenderOption="FORMATTED_STRING",
            )
            .execute()
        )

        # pprint.pprint(result)
        values = result.get("values")

        # yield dicts assuming row 0 contains headers and following rows values and all rows have identical length
        for v in values[1:]:
            yield {h: v for h, v in zip(values[0], v)}

    # create resources from supplied sheet names
    return [
        dlt.resource(get_sheet(name), name=name, write_disposition="replace")
        for name in sheet_names
    ]


if __name__ == "__main__":
    pipeline = dlt.pipeline(destination="duckdb")
    # see example.secrets.toml to where to put credentials
    sheet_id = "1HhWHjqouQnnCIZAFa2rL6vT91YRN8aIhts22SUUR580"
    range_names = ["hidden_columns_merged_cells", "Blank Columns"]
    # "2022-05", "model_metadata"
    load_info = pipeline.run(
        google_spreadsheet(
            spreadsheet_id=sheet_id,
            sheet_names=range_names,
        )
    )

    print(load_info)

    row_counts = pipeline.last_trace.last_normalize_info.row_counts
    print(row_counts.keys())
    assert row_counts["hidden_columns_merged_cells"] == 7
    assert row_counts["blank_columns"] == 21
