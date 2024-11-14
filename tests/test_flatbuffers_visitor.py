import flatbuffers

from flatbuffers_modifier import FlatbuffersVisitor, FlatbuffersRebuildVisitor
from tests.data.MyGame.Sample import Monster, Weapon
from tests.flatbuffers_pool import get_buffer_data


def test_flatbuffers_visitor():
    origin_data = get_buffer_data()

    visitor = FlatbuffersVisitor("MyGame.Sample")

    root_object = Monster.Monster.GetRootAs(origin_data, 0)
    visitor.visit(root_object, '')


def test_flatbuffers_rebuild():
    origin_data = get_buffer_data()

    builder = flatbuffers.Builder(0)
    visitor = FlatbuffersRebuildVisitor("MyGame.Sample", builder)

    root_object = Monster.Monster.GetRootAs(origin_data, 0)
    result = visitor.visit(root_object, '')
    builder.Finish(result)
    new_data = builder.Output()

    new_object = Monster.Monster.GetRootAs(new_data, 0)

    assert root_object.Name() == new_object.Name()
    assert root_object.Hp() == new_object.Hp()
    assert root_object.Weapon().Damage() == new_object.Weapon().Damage()
    assert root_object.Weapon().Type() == new_object.Weapon().Type()
    assert root_object.Inventory(0).Type() == new_object.Inventory(0).Type()
    assert root_object.Inventory(0).Damage() == new_object.Inventory(0).Damage()
    assert len(root_object.Inventory(0).Type()) == len(new_object.Inventory(0).Type())
    assert root_object.Inventory(0).Damage() == new_object.Inventory(0).Damage()
    assert len(root_object.Name()) == len(new_object.Name())
    assert root_object.Hp() == new_object.Hp()
    assert root_object.Weapon().Damage() == new_object.Weapon().Damage()
    assert len(root_object.Weapon().Type()) == len(new_object.Weapon().Type())
