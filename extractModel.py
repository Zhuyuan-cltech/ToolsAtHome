import ast
import textwrap


class CodeCleaner(ast.NodeTransformer):
    """深度清理代码，只保留核心模型类"""

    def __init__(self):
        super().__init__()
        self.keep_import_torch = False

    def visit_Module(self, node):
        # 先处理子节点，再过滤结果
        new_body = []
        for stmt in node.body:
            result = self.visit(stmt)
            if result is not None:
                # 将保留的语句包装成单独节点
                if not isinstance(result, list):
                    result = [result]
                new_body.extend(result)

        # 确保包含必要的torch导入
        if self.keep_import_torch and not any(
            isinstance(n, ast.Import) for n in new_body
        ):
            new_body.insert(
                0,
                ast.Import(names=[ast.alias(name="torch", asname=None)]),
            )
        return ast.Module(body=new_body, type_ignores=[])

    def is_torch_nn_module(self, node):
        """递归检测是否为torch.nn.Module基类"""
        if isinstance(node, ast.Name):
            return node.id == "Module"  # 当基类直接写Module时
        elif isinstance(node, ast.Attribute):
            # 解析属性链如torch.nn.Module
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            parts.reverse()
            return ".".join(parts) == "torch.nn.Module"
        return False

    def visit_ClassDef(self, node):
        # 检查是否继承自torch.nn.Module
        has_module_base = any(self.is_torch_nn_module(base) for base in node.bases)

        if not has_module_base:
            return None

        # 清理类体
        node.body = [
            self.clean_method(stmt)
            for stmt in node.body
            if isinstance(stmt, ast.FunctionDef)
            and stmt.name in ("__init__", "forward")
        ]
        return node

    def clean_method(self, node):
        """清理方法定义"""
        # 移除所有装饰器
        node.decorator_list = []

        # 确保__init__有super调用
        if node.name == "__init__":
            if not any(
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Attribute)
                and stmt.value.func.attr == "__init__"
                for stmt in node.body
            ):
                super_call = ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Call(
                                func=ast.Name(id="super", ctx=ast.Load()),
                                args=[],
                                keywords=[],
                            ),
                            attr="__init__",
                            ctx=ast.Load(),
                        ),
                        args=[],
                        keywords=[],
                    )
                )
                node.body.insert(0, super_call)
        return node

    def visit_Import(self, node):
        # 标记需要保留torch导入
        if any(alias.name == "torch" for alias in node.names):
            self.keep_import_torch = True
            return node
        return None

    def visit_ImportFrom(self, node):
        # 完全移除所有from...import语句
        return None

    def visit_FunctionDef(self, node):
        # 删除所有顶层函数
        return None


def purify_code(source):
    """主清洗函数"""
    tree = ast.parse(source)
    cleaner = CodeCleaner()
    cleaned_tree = cleaner.visit(tree)

    # 生成规范化的代码
    return ast.unparse(cleaned_tree)


# 使用示例
if __name__ == "__main__":
    with open(
        "/workspace/iree/third_party/torch-mlir/projects/pt1/python/torch_mlir_e2e_test/test_suite/elementwise.py",
        "r",
    ) as f:
        source = f.read()

    purified = purify_code(source)

    with open("./output.py", "w", encoding="utf-8") as op:
        op.write(purified)

# # 示例用法
# if __name__ == "__main__":
#     with open(
#         "/workspace/iree/third_party/torch-mlir/projects/pt1/python/torch_mlir_e2e_test/test_suite/elementwise.py",
#         "r",
#     ) as f:
#         source = f.read()

#     cleaned_code = extract_pure_modules(source)

#     # 添加必要的头部和编译代码
#     final_code = (
#         "import torch\n\n"
#         f"{cleaned_code}\n\n"
#         "# 使用示例\n"
#         "device = 'dlc'\n"
#         "# 选择要编译的模型\n"
#         "model = ElementwiseSinhModule().to(device)\n"
#         "# 配置DLC后端编译\n"
#         "compiled_model = torch.compile(model, backend='turbine_dlc')\n"
#     )

#     with open("./output.py", "w", encoding="utf-8") as op:
#         op.write(final_code)
