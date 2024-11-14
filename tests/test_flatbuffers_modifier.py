import os

from flatbuffers_modifier import FlatbuffersModifier
from tests.data.MyGame.Sample import Monster
from tests.flatbuffers_pool import get_buffer_data


def test_modify_single_member():
    # 获取原始数据
    original_data = get_buffer_data()

    # 保存初始数据
    os.makedirs("tests/data/output", exist_ok=True)
    with open("tests/data/output/monster.bin", "wb") as f:
        f.write(original_data)

    # 从文件读取数据并修改多个嵌套属性
    with open("tests/data/output/monster.bin", "rb") as f:
        data = f.read()

    modifier = FlatbuffersModifier(data, "MyGame.Sample", "Monster")
    assert modifier.get_nested_field("hp") == 300
    assert modifier.get_nested_field("weapon.damage") == 50
    assert modifier.get_nested_field("weapon.type").decode() == "Sword"

    modifications = {
        "hp": 500,
        "weapon.damage": 10,
        "weapon.type": "Bow",
        "inventory.0.damage": 100
    }
    updated_data = modifier.modify_fields(modifications)
    modified_monster = Monster.Monster.GetRootAs(updated_data, 0)

    # 验证修改后的值
    assert modified_monster.Hp() == 500
    assert modified_monster.Weapon().Damage() == 10
    assert modified_monster.Weapon().Type().decode() == "Bow"
    assert modified_monster.Inventory(0).Damage() == 100

    # 输出修改后的数据并保存
    with open("tests/data/output/updated_monster.bin", "wb") as f:
        f.write(updated_data)
