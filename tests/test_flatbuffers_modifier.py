import flatbuffers
from flatbuffers_modifier import FlatbuffersModifier
from tests.data.MyGame.Sample import Monster


def test_modify_single_member():
    # 初始化原始数据
    builder = flatbuffers.Builder(0)

    # 构建武器和怪物
    weapon_name = builder.CreateString("Sword")
    Monster.MonsterStart(builder)
    Monster.MonsterAddHp(builder, 300)
    Monster.MonsterAddName(builder, weapon_name)
    weapon = Monster.MonsterEnd(builder)
    builder.Finish(weapon)

    # 保存初始数据
    original_data = builder.Output()
    with open("monster.bin", "wb") as f:
        f.write(original_data)

    # 从文件读取数据并修改多个嵌套属性
    with open("monster.bin", "rb") as f:
        data = f.read()

    modifier = FlatbuffersModifier(data, "tests.data.MyGame.Sample", "Monster")
    print("Original HP:", modifier.get_nested_field("hp"))
    print("Original Weapon Damage:", modifier.get_nested_field("weapon.damage"))

    modifications = {
        "hp": 500,
        "weapon.damage": 50,
        "weapon.type": "Bow"
    }
    modifier.modify_fields(modifications)

    # 验证修改后的值
    print("Modified HP:", modifier.get_nested_field("hp"))
    print("Modified Weapon Damage:", modifier.get_nested_field("weapon.damage"))

    # 输出修改后的数据并保存
    updated_data = modifier.output()
    with open("updated_monster.bin", "wb") as f:
        f.write(updated_data)
