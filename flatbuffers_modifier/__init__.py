import importlib
import re
from typing import Any, Dict

import flatbuffers
import numpy


class FlatbuffersModifier:
    def __init__(self, flatbuffers_data: bytes, flatbuffers_namespace: str, root_type_name: str, offset=0):
        """
        初始化 FlatbuffersModifier
        :param flatbuffers_data: FlatBuffers 的二进制数据
        :param flatbuffers_namespace: 根类型所在命名空间（例如 'MyGame.Sample'）
        :param root_type_name: 根类型名称（例如 'Monster'）
        """
        self.flatbuffers_data = flatbuffers_data
        self.flatbuffers_namespace = flatbuffers_namespace
        self.root_type_name = root_type_name
        self.root = getattr(self.get_module(root_type_name), self.root_type_name).GetRootAs(self.flatbuffers_data, offset)
        self.identifier = None
        identifier_attr = f'{self.root.__class__.__name__}BufferHasIdentifier'
        if hasattr(self.root, identifier_attr) and getattr(self.root, identifier_attr)(self.flatbuffers_data, offset):
            self.identifier = self.flatbuffers_data[offset + 4:offset + 8]

    def get_module(self, type_name: str):
        """
        获取指定类型的模块

        :param type_name: 类型名称
        :return: 模块对象
        """
        return importlib.import_module(self.flatbuffers_namespace + '.' + type_name)

    @staticmethod
    def fix_field_name(field_name: str):
        """
        将字符串按下划线分隔，然后将每个单词首字母大写，再拼接
        """
        return ''.join(word.capitalize() for word in field_name.split('_'))

    def get_nested_field(self, path: str) -> Any:
        """
        获取嵌套字段值
        :param path: 用点分隔的字段路径，例如 'monster.weapon.damage'
        :return: 字段值
        """
        fields = re.split(r'\.(?!\d)', path)
        current = self.root
        for field in fields:
            if '.' in field:
                field, index = field.split('.')
                index = int(index)
                current = getattr(current, self.fix_field_name(field))(index)
            else:
                current = getattr(current, self.fix_field_name(field))()
        return current

    def recursive_rebuild(self, builder, old_object, modifications: Dict[str, Any]):
        """
        递归重建对象，并修改指定嵌套字段
        :param builder: flatbuffers.Builder 对象
        :param old_object: 旧对象
        :param modifications: 字典，键为字段路径（如 'monster.weapon.damage'），值为新值
        """
        assert hasattr(old_object, '_tab')

        object_module = self.get_module(old_object.__class__.__name__)
        # 辅助成员方法名称列表
        aux_members = ['GetRootAs', f'GetRootAs{old_object.__class__.__name__}', 'Init', f'{old_object.__class__.__name__}BufferHasIdentifier']
        # 获取旧对象的所有字段名称，排除辅助成员方法
        fields = dir(old_object)
        new_members: Dict[str, Any] = {}
        for field in fields:
            if field.startswith('_'):
                continue
            if field in aux_members:
                continue
            if field.endswith('AsNumpy') or (field.endswith('Length') and field[:-len('Length')] in fields) or field.endswith('IsNone'):
                continue

            # 获取与当前字段相关的所有修改
            sub_modifications = {
                k[len(field) + 1:]: v
                for k, v in modifications.items()
                if self.fix_field_name(k).startswith(field + '.') or self.fix_field_name(k) == field
            }
            if field + 'Length' in fields:
                member = [getattr(old_object, field)(i) for i in range(getattr(old_object, field + 'Length')())]
            else:
                member = getattr(old_object, field)()

            if len(sub_modifications) == 1 and '' in sub_modifications:
                # 如果只有一个修改且键为空字符串，则直接使用该值
                new_value = sub_modifications['']
                if isinstance(new_value, str):
                    new_value = builder.CreateString(new_value)
                elif isinstance(new_value, bytes):
                    new_value = builder.CreateByteVector(new_value)
                sub_object = new_value
            elif hasattr(member, '_tab'):
                # 如果是flatbuffers对象，则递归重建子对象
                sub_object = self.recursive_rebuild(builder, getattr(old_object, field)(), sub_modifications)
            elif isinstance(member, list):
                # 如果是flatbuffers对象，则递归重建子对象
                sub_object_list = []
                if len(member) == 0:
                    item_type = None
                elif hasattr(old_object, f'{field}AsNumpy'):
                    item_type = getattr(old_object, f'{field}AsNumpy')().dtype
                elif type(member[0]) == bytes:
                    item_type = 'bytes'
                else:
                    item_type = type(member[0])

                for idx, item in enumerate(member):
                    idx_str = str(idx)
                    list_sub_modifications = {
                        k[len(idx_str) + 1:]: v
                        for k, v in sub_modifications.items()
                        if self.fix_field_name(k).startswith(idx_str + '.') or self.fix_field_name(k) == field
                    }
                    if item_type == 'bytes':
                        sub_object_list.append(builder.CreateString(item))
                    elif isinstance(item_type, numpy.dtype):
                        sub_object_list.append(item)
                    else:
                        sub_object_list.append(self.recursive_rebuild(builder, item, list_sub_modifications))

                getattr(object_module, f'Start{field}Vector')(builder, len(member))
                if isinstance(item_type, numpy.dtype):
                    if item_type == 'int32':
                        for item in reversed(sub_object_list):
                            builder.PrependInt32(item)
                    elif item_type == 'uint8':
                        for item in reversed(sub_object_list):
                            builder.PrependUint8(item)
                    else:
                        raise NotImplementedError(f'Unsupported numpy dtype: {item_type}. Please add to above.')
                else:
                    for item in reversed(sub_object_list):
                        builder.PrependUOffsetTRelative(item)
                sub_object = builder.EndVector()
            else:
                # 如果不是flatbuffers对象, 则直接使用新值
                sub_object = getattr(old_object, field)()
                if isinstance(sub_object, bytes):
                    sub_object = builder.CreateString(sub_object)

            new_members[field] = sub_object

        # 获取对象模块并开始构建新对象
        object_module.Start(builder)
        for field, sub_object in new_members.items():
            # 添加字段到新对象
            getattr(object_module, 'Add' + field)(builder, sub_object)
        # 结束对象构建并返回新对象
        return object_module.End(builder)

    def modify_fields(self, modifications: Dict[str, Any], identifier=None) -> bytes:
        """
        修改指定的嵌套字段

        :param modifications: 字典，键为字段路径（如 'monster.weapon.damage'），值为新值
        :return: 修改后的二进制数据
        """
        builder = flatbuffers.Builder(0)
        new_root = self.recursive_rebuild(builder, self.root, modifications)
        builder.Finish(new_root, identifier if identifier is not None else self.identifier)
        return builder.Output()
