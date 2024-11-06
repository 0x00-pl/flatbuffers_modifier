import flatbuffers
import importlib
from typing import Any, List, Dict


class FlatbuffersModifier:
    def __init__(self, flatbuffers_data: bytes, root_type_module: str, root_type_name: str):
        """
        初始化 FlatbuffersModifier
        :param flatbuffers_data: FlatBuffers 的二进制数据
        :param root_type_module: 根类型所在模块名（例如 'MyGame.Sample'）
        :param root_type_name: 根类型名称（例如 'Monster'）
        """
        self.flatbuffers_data = flatbuffers_data
        self.root_type_module = root_type_module
        self.root_type_name = root_type_name
        self.builder = flatbuffers.Builder(0)

        # 加载根对象
        module = importlib.import_module(self.root_type_module)
        root_class = getattr(module, self.root_type_name)
        self.root = root_class.GetRootAs(self.flatbuffers_data, 0)

    def get_nested_field(self, path: str) -> Any:
        """
        获取嵌套字段值
        :param path: 用点分隔的字段路径，例如 'monster.weapon.damage'
        :return: 字段值
        """
        fields = path.split('.')
        current = self.root
        for field in fields:
            current = getattr(current, field)()
        return current

    def modify_fields(self, modifications: Dict[str, Any]):
        """
        修改多个嵌套字段值
        :param modifications: 字典，键为字段路径（如 'monster.weapon.damage'），值为新值
        """
        # 清空构建器并依次应用修改
        self.builder.Clear()
        for path, new_value in modifications.items():
            self._rebuild_with_modification(path.split('.'), new_value)

    def _rebuild_with_modification(self, fields: List[str], new_value: Any):
        """
        递归重建对象，并修改指定嵌套字段
        :param fields: 字段路径的分段列表
        :param new_value: 新的字段值
        """
        # 处理多层嵌套路径
        current_field = fields.pop(0)

        # 递归处理子字段
        if fields:
            sub_object = getattr(self.root, current_field)()
            nested_modifier = FlatbuffersModifier(sub_object, self.root_type_module, sub_object.__class__.__name__)
            nested_modifier.modify_fields({'.'.join(fields): new_value})
            sub_object = nested_modifier.output()
        else:
            # 修改最终目标字段
            sub_object = new_value if not isinstance(new_value, str) else self.builder.CreateString(new_value)

        # 重建根对象
        self.root.Start(self.builder)
        for attr in dir(self.root):
            if not attr.startswith('__') and callable(getattr(self.root, attr)):
                value = sub_object if attr == current_field else getattr(self.root, attr)()
                setattr(self.root, attr, value)
        self.root.End(self.builder)

    def output(self) -> bytes:
        """输出修改后的 FlatBuffers 数据"""
        self.builder.Finish(self.root.End(self.builder))
        return self.builder.Output()
