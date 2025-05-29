import ast


class ImportCollector(ast.NodeVisitor):
    """收集所有与torch相关的导入别名信息（增强版）"""

    def __init__(self):
        self.import_aliases = {}  # 格式: {别名: 完整模块路径}

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.startswith("torch"):
                key = alias.asname or alias.name
                self.import_aliases[key] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith("torch"):
            base_module = node.module
            for alias in node.names:
                full_name = (
                    f"{base_module}.{alias.name}" if alias.name != "*" else base_module
                )
                key = alias.asname or alias.name
                self.import_aliases[key] = full_name
        self.generic_visit(node)


class OperatorCollector(ast.NodeVisitor):
    """收集forward函数中使用的torch算子（支持torch.ops.aten）"""

    def __init__(self, import_aliases):
        self.import_aliases = import_aliases
        self.operators = set()
        self.aten_operators = set()

    def _resolve_full_path(self, node):
        """递归解析属性调用路径"""
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            return self._resolve_full_path(node.value) + [node.attr]
        return []

    def visit_ClassDef(self, node):
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name == "forward":
                self.visit_forward(child)
        self.generic_visit(node)

    def visit_forward(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            full_path = self._resolve_full_path(node.func)
            self._check_torch_ops(full_path)
        elif isinstance(node.func, ast.Name):
            self._check_direct_call(node.func.id)

        self.generic_visit(node)

    def _check_torch_ops(self, full_path):
        """检查是否属于torch.ops.aten操作符"""
        # 处理可能的别名（如import torch.ops.aten as aten_alias）
        resolved_path = []
        for part in full_path:
            if part in self.import_aliases:
                resolved = self.import_aliases[part].split(".")
                resolved_path.extend(resolved)
            else:
                resolved_path.append(part)

        # 匹配torch.ops.aten模式
        if len(resolved_path) >= 4 and resolved_path[:3] == ["torch", "ops", "aten"]:
            self.aten_operators.add(resolved_path[3])
        elif (
            len(resolved_path) == 3
            and resolved_path[:2] == ["torch", "ops"]
            and resolved_path[2] == "aten"
        ):
            self.aten_operators.add(resolved_path[2])
        else:
            # 处理常规torch操作符
            if resolved_path[0] == "torch" and len(resolved_path) >= 2:
                self.operators.add(".".join(resolved_path[1:]))

    def _check_direct_call(self, func_name):
        """检查直接调用的函数名是否来自torch导入"""
        if func_name in self.import_aliases:
            full_path = self.import_aliases[func_name].split(".")
            if full_path[0] == "torch":
                self.operators.add(".".join(full_path[1:]))


def extract_torch_operators(filename):
    with open(filename, "r") as f:
        tree = ast.parse(f.read())

    import_collector = ImportCollector()
    import_collector.visit(tree)

    operator_collector = OperatorCollector(import_collector.import_aliases)
    operator_collector.visit(tree)

    return {
        "standard_ops": sorted(operator_collector.operators),
        "aten_ops": sorted(operator_collector.aten_operators),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_operators.py [filename]")
        sys.exit(1)

    filename = sys.argv[1]
    operators = extract_torch_operators(filename)

    print("Standard Torch operators:\n")
    for op in operators["standard_ops"]:
        print(f"torch.{op}")

    print("\nAten operators (torch.ops.aten):\n")
    for op in operators["aten_ops"]:
        print(f"torch.ops.aten.{op}")
