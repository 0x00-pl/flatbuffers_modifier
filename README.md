flatbuffers modifier
===================
![CI status](https://github.com/0x00-pl/flatbuffers_modifier/actions/workflows/ci.yml/badge.svg?branch=master)

download flatc using poetry
--------------
```bash
poetry run install-flatc
```

download flatc using python
--------------

```python
from scripts.install_flatc import download_and_extract_flatc

download_and_extract_flatc()
```

generate flatbuffers python code
--------------
```bash
flatc --python -o <output_path> <fbs_file>
```

usage
-----
reference from `tests/test_flatbuffers_modifier.py`

```python
from flatbuffers_modifier import FlatbuffersModifier

with open("tests/data/output/monster.bin", "rb") as f:
    data = f.read()

# add compiled flatbuffers schema to sys.path
modifier = FlatbuffersModifier(data, "MyGame.Sample", "Monster")
modifications = {
    "hp": 500,
    "weapon.damage": 10,
    "weapon.type": "Bow"
}
updated_data = modifier.modify_fields(modifications)

with open("tests/data/output/updated_monster.bin", "wb") as f:
    f.write(updated_data)
```
