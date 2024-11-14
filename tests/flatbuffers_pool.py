import flatbuffers

from tests.data.MyGame.Sample import Monster, Weapon


def get_buffer_data():
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
    Monster.MonsterAddInventory(builder, inventory_offset)
    monster_offset = Monster.MonsterEnd(builder)

    builder.Finish(monster_offset)

    # 保存初始数据
    original_data = builder.Output()
    return original_data
