import importlib
from typing import Any, Dict

import flatbuffers


class FlatbuffersModifier:
    def __init__(self, flatbuffers_data: bytes, flatbuffers_namespace: str, root_type_name: str):
        """
        初始化 FlatbuffersModifier
        :param flatbuffers_data: FlatBuffers 的二进制数据
        :param flatbuffers_namespace: 根类型所在命名空间（例如 'MyGame.Sample'）
        :param root_type_name: 根类型名称（例如 'Monster'）
        """
        self.flatbuffers_data = flatbuffers_data
        self.flatbuffers_namespace = flatbuffers_namespace
        self.root_type_name = root_type_name
        self.root = self.get_class(root_type_name).GetRootAs(self.flatbuffers_data, 0)

    def get_module(self, type_name: str):
        return importlib.import_module(self.flatbuffers_namespace + '.' + type_name)

    def get_class(self, type_name: str):
        return getattr(importlib.import_module(self.flatbuffers_namespace + '.' + type_name), type_name)

    @staticmethod
    def fix_field_name(field_name: str):
        # 自动将首字母大写以匹配生成的属性名称
        return field_name[0].upper() + field_name[1:]

    @staticmethod
    def remove_prefix(string: str, prefix: str, separator: str = '.'):
        return string.removeprefix(prefix + separator)

    def get_nested_field(self, path: str) -> Any:
        """
        获取嵌套字段值
        :param path: 用点分隔的字段路径，例如 'monster.weapon.damage'
        :return: 字段值
        """
        fields = path.split('.')
        current = self.root
        for field in fields:
            current = getattr(current, self.fix_field_name(field))()
        return current

    def recursive_rebuild(self, builder, old_object, modifications: Dict[str, Any]):
        """
        递归重建对象，并修改指定嵌套字段
        :param builder: flatbuffers.Builder 对象
        :param old_object: 旧对象
        :param modifications: 字典，键为字段路径（如 'monster.weapon.damage'），值为新值
        """

        aux_members = ['GetRootAs', f'GetRootAs{old_object.__class__.__name__}', 'Init']
        fields = [i for i in dir(old_object) if not i.startswith('_') and i not in aux_members]
        new_members: Dict[str, Any] = {}
        for field in fields:
            sub_modifications = {
                k[len(field) + 1:]: v
                for k, v in modifications.items()
                if self.fix_field_name(k).startswith(field)
            }
            if len(sub_modifications) == 1 and '' in sub_modifications:
                new_value = sub_modifications['']
                if isinstance(new_value, str):
                    new_value = builder.CreateString(new_value)
                sub_object = new_value
            elif sub_modifications:
                sub_object = self.recursive_rebuild(builder, getattr(old_object, field)(), sub_modifications)
            else:
                sub_object = getattr(old_object, field)()
                if isinstance(sub_object, bytes):
                    sub_object = builder.CreateString(sub_object)

            new_members[field] = sub_object

        object_module = self.get_module(old_object.__class__.__name__)
        object_module.Start(builder)
        for field, sub_object in new_members.items():
            getattr(object_module, 'Add' + field)(builder, sub_object)
        return object_module.End(builder)

    def modify_fields(self, modifications: Dict[str, Any]):
        builder = flatbuffers.Builder(0)
        new_root = self.recursive_rebuild(builder, self.root, modifications)
        builder.Finish(new_root)
        return builder.Output()
