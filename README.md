flatbuffers modifier
===================

usage
-----
reference from `tests/test_flatbuffers_modifier.py`

```python
from flatbuffers_modifier import FlatbuffersModifier

with open("tests/data/output/monster.bin", "rb") as f:
    data = f.read()

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
