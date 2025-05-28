---
title: Renaming columns
description: Renaming columns by replacing the special characters
keywords: [renaming, columns, special characters]
---

# 列名の変更

## 特殊文字を置き換えて列名を変更する

以下の例では、名前に特殊文字を含むダミーソースを作成します。次に、リソースの出力を変更する（つまり、ドイツ語のウムラウトを置き換える）関数「replace_umlauts_in_dict_keys」を記述します。

```py
import dlt

# create a dummy source with umlauts (special characters) in key names (um)
@dlt.source
def dummy_source(prefix: str = None):
    @dlt.resource
    def dummy_data():
        for _ in range(100):
            yield {f'Objekt_{_}': {'Größe': _, 'Äquivalenzprüfung': True}}
    return dummy_data(),

def replace_umlauts_in_dict_keys(d):
    """
    Replaces umlauts in dictionary keys with standard characters.
    """
    umlaut_map =  {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'}
    result = {}
    for k, v in d.items():
        new_key = ''.join(umlaut_map.get(c, c) for c in k)
        if isinstance(v, dict):
            result[new_key] = replace_umlauts_in_dict_keys(v)
        else:
            result[new_key] = v
    return result

# We can add the map function to the resource

# 1. Create an instance of the source so you can edit it.
source_instance = dummy_source()

# 2. Modify this source instance's resource
source_instance.dummy_data().add_map(replace_umlauts_in_dict_keys)

# 3. Inspect your result
for row in source_instance:
    print(row)

# {'Objekt_0': {'Groesse': 0, 'Aequivalenzpruefung': True}}
# ...
```

