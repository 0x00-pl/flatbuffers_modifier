import os

import flatbuffers

from flatbuffers_modifier import FlatbuffersModifier
from tests.data.MyGame.Sample import Monster, Weapon


def test_modify_single_member():
    # 初始化原始数据
    builder = flatbuffers.Builder(0)

    # 构建 Weapon 对象
    weapon_type = builder.CreateString("Sword")
    Weapon.WeaponStart(builder)
    Weapon.WeaponAddDamage(builder, 50)
    Weapon.WeaponAddType(builder, weapon_type)
    weapon_offset = Weapon.WeaponEnd(builder)

    # 构建 Inventory.Weapon 对象
    weapon_type = builder.CreateString("Axe")
    Weapon.WeaponStart(builder)
    Weapon.WeaponAddDamage(builder, 80)
    Weapon.WeaponAddType(builder, weapon_type)
    inventory_weapon_offset = Weapon.WeaponEnd(builder)

    # 构建 Inventory 对象
    Monster.StartInventoryVector(builder, 1)
    builder.PrependSOffsetTRelative(inventory_weapon_offset)
    inventory_offset = builder.EndVector()

    # 构建 Monster 对象
    monster_name = builder.CreateString("Orc")
    Monster.MonsterStart(builder)
    Monster.MonsterAddHp(builder, 300)
    Monster.MonsterAddName(builder, monster_name)
    Monster.MonsterAddWeapon(builder, weapon_offset)  # 将 Weapon 对象添加到 Monster 中
    Monster.MonsterAddInventory(builder, inventory_offset)  # 添加一个空的 Inventory
    monster_offset = Monster.MonsterEnd(builder)

    builder.Finish(monster_offset)

    # 保存初始数据
    os.makedirs("tests/data/output", exist_ok=True)
    original_data = builder.Output()
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
