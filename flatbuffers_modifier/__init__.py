import importlib

import flatbuffers


class FlatbuffersVisitor:
    def __init__(self, flatbuffers_namespace: str):
        """
        初始化 FlatbuffersVisitor
        :param flatbuffers_namespace: 根类型所在命名空间（例如 'MyGame.Sample'）
        """
        self.flatbuffers_namespace = flatbuffers_namespace

    def get_module(self, type_name: str):
        """
        获取指定定类型的模块

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

    def visit(self, obj, current_path: str):
        if hasattr(obj, '_tab'):
            return self.visit_object(obj, current_path)
        else:
            return self.visit_value(obj, current_path)

    def visit_object(self, obj, current_path: str):
        """
        访问对象
        :param obj: 对象
        :param current_path: 当前路径
        """
        assert hasattr(obj, '_tab')
        aux_members = ['GetRootAs', f'GetRootAs{obj.__class__.__name__}', 'Init',
                       f'{obj.__class__.__name__}BufferHasIdentifier']
        results = {}
        # 获取对象的所有字段名称
        fields = dir(obj)
        for field in fields:
            if field.startswith('_'):
                continue
            if field in aux_members:
                continue
            if field.endswith('AsNumpy') or (
                    field.endswith('Length') and field[:-len('Length')] in fields) or field.endswith('IsNone'):
                continue

            if field + 'Length' in fields:
                results[field] = self.visit_list(obj, field, current_path)
            else:
                results[field] = self.visit(getattr(obj, field)(), f'{current_path}.{field}')

        return results

    def visit_list(self, obj, field: str, current_path: str):
        """
        访问列表
        :param obj: 对象
        :param field: 字段名称
        :param current_path: 当前路径
        """
        results = []
        length = getattr(obj, field + 'Length')()
        for i in range(length):
            results.append(self.visit(getattr(obj, field)(i), f'{current_path}.{field}.{i}'))
        return results

    def visit_value(self, value, current_path: str):
        """
        访问值
        :param value: 值
        :param current_path: 当前路径
        """
        assert not hasattr(value, '_tab')
        return value


class FlatbuffersRebuildVisitor(FlatbuffersVisitor):
    def __init__(self, flatbuffers_namespace: str, builder: flatbuffers.Builder):
        """
        初始化 FlatbuffersRebuildVisitor
        :param flatbuffers_namespace: 根类型所在命名空间（例如 'MyGame.Sample'）
        :param builder: flatbuffers.Builder 对象
        """
        super().__init__(flatbuffers_namespace)
        self.builder = builder

    def visit_object(self, obj, current_path: str):
        """
        访问对象并重建它

        :param obj: 要访问的对象
        :param current_path: 当前路径
        :return: 重建后的对象偏移量
        """
        result = super().visit_object(obj, current_path)
        obj_module = self.get_module(obj.__class__.__name__)
        obj_module.Start(self.builder)
        for field, value in result.items():
            getattr(obj_module, 'Add' + field)(self.builder, value)
        return obj_module.End(self.builder)

    def visit_list(self, obj, field: str, current_path: str):
        """
        访问列表并重建它

        :param obj: 对象
        :param field: 字段名称
        :param current_path: 当前路径
        :return: 重建后的列表偏移量
        """
        obj_module = self.get_module(obj.__class__.__name__)
        results = super().visit_list(obj, field, current_path)
        assert isinstance(results, list)

        # 开始构建列表
        getattr(obj_module, f'Start{field}Vector')(self.builder, len(results))

        element_type = None
        if len(results) != 0 and hasattr(obj, f'{field}AsNumpy'):
            element_type = getattr(obj, f'{field}AsNumpy')().dtype

        # 反向遍历列表并添加元素
        for idx, value in reversed(list(enumerate(results))):
            old_member = getattr(obj, field)(idx)
            if hasattr(old_member, '_tab'):
                self.builder.PrependUOffsetTRelative(value)
            elif isinstance(old_member, (str, bytes)):
                self.builder.PrependUOffsetTRelative(value)
            elif element_type == 'int64':
                self.builder.PrependInt64(value)
            elif element_type == 'int32':
                self.builder.PrependInt32(value)
            elif element_type == 'uint8':
                self.builder.PrependUint8(value)
            else:
                raise NotImplementedError(f'Unsupported type at {current_path=}: {type(value)=} or {element_type=}')

        # 结束列表构建并返回偏移量
        return self.builder.EndVector()

    def visit_value(self, value, current_path: str):
        """
        访问值并处理字符串和字节类型

        :param value: 值
        :param current_path: 当前路径
        :return: 处理后的值
        """
        if isinstance(value, (str, bytes)):
            return self.builder.CreateString(value)
        else:
            return value


class FlatbuffersModifyVisitor(FlatbuffersRebuildVisitor):
    def __init__(self, root_type_module: str, builder: flatbuffers.Builder):
        """
        初始化 FlatbuffersModifyVisitor
        :param root_type_module: 根类型所在命名空间（例如 'MyGame.Sample'）
        :param builder: flatbuffers.Builder 对象
        """
        super().__init__(root_type_module, builder)
        self.modifications = {}

    def modify_fields(self, key, value):
        """
        修改指定字段的值, 如果是vector, 请填这个包含这个vector的flatbuffers object.
        :param key: 字段路径（例如 'monster.weapon.damage'）
        :param value: 新值
        """
        fields = key.split('.')
        path = '.' + '.'.join([self.fix_field_name(i) for i in fields])
        self.modifications[path] = value

    def visit(self, obj, current_path):
        """
        访问对象并应用修改
        :param obj: 要访问的对象
        :param current_path: 字段名称
        :return: 修改后的对象
        """
        updated_obj = obj
        if current_path in self.modifications:
            updated_obj = self.modifications[current_path]
        return super().visit(updated_obj, current_path)

    def visit_list(self, obj, field: str, current_path: str):
        """
        访问列表并应用修改

        :param obj: 对象
        :param field: 字段名称
        :param current_path: 当前路径
        :return: 修改后的列表
        """
        updated_obj = obj
        if current_path + '.' + field in self.modifications:
            updated_obj = self.modifications[current_path + '.' + field]
        return super().visit_list(updated_obj, field, current_path)
