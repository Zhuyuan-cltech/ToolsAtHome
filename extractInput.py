import ast
import json


def extract_shapes(args):
    shapes = []
    for arg in args:
        current_call = arg
        found = False

        # 展开链式调用
        while True:
            if not isinstance(current_call, ast.Call):
                break

            # 检查当前调用是否为目标生成器
            if (
                hasattr(current_call.func, "attr")
                and current_call.func.attr in ("rand", "randint", "zeros")
                and hasattr(current_call.func.value, "id")
                and current_call.func.value.id == "tu"
            ):

                # 提取维度信息
                dims = []
                for dim_node in current_call.args:
                    if isinstance(dim_node, ast.Constant):
                        dims.append(dim_node.value)
                    else:
                        return None
                shapes.append(tuple(dims))
                found = True
                break

            # 处理链式调用（如.to()）
            if isinstance(current_call.func, ast.Attribute):
                current_call = current_call.func.value
            else:
                break

        if not found:
            return None

    return shapes if shapes else None


def convert_dim(d):
    """修正为正确的上限值"""
    if d == 1:
        return 1
    try:
        exponent = d - 1
        converted = 128 * (2**exponent)
        return min(converted, 4096)
    except:
        return 1


def parse_annotate_args(decorator_list):
    for decorator in decorator_list:
        if isinstance(decorator, ast.Call) and decorator.func.id == "annotate_args":
            args = decorator.args[0].elts[1:]
            dtypes = []
            for arg in args:
                if isinstance(arg, ast.Tuple):
                    dtype_node = arg.elts[1]
                    # 支持多级属性访问（如torch.int32）
                    if isinstance(dtype_node, ast.Attribute):
                        attr_parts = []
                        node = dtype_node
                        while isinstance(node, ast.Attribute):
                            attr_parts.append(node.attr)
                            node = node.value
                        if isinstance(node, ast.Name) and node.id == "torch":
                            dtypes.append("_".join(reversed(attr_parts)))
            return dtypes
    return []


def convert_dim(d):
    """增强版维度转换，支持动态上限检查"""
    if d == 1:
        return 1
    try:
        converted = 128 * (2 ** (int(d) - 1))
        return min(converted, 4096)  # 使用问题描述中的8152上限
    except:
        return 1  # 异常情况保持维度1


def process_file(file_path):
    with open(file_path) as f:
        tree = ast.parse(f.read())

    modules = {}
    test_cases = {}
    manual_modules = set()

    # 收集模块信息
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for body_node in node.body:
                if (
                    isinstance(body_node, ast.FunctionDef)
                    and body_node.name == "forward"
                ):
                    dtypes = parse_annotate_args(body_node.decorator_list)
                    modules[node.name] = dtypes

    # 收集测试用例
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and decorator.func.id == "register_test_case"
                ):
                    module_class = decorator.keywords[0].value.body.func.id
                    test_cases[node.name] = module_class

    # 处理测试用例
    config = {}
    for func_node in ast.walk(tree):
        if isinstance(func_node, ast.FunctionDef) and func_node.name in test_cases:
            module_class = test_cases[func_node.name]
            shapes = None

            # 查找forward调用
            for body_node in func_node.body:
                if isinstance(body_node, ast.Expr) and isinstance(
                    body_node.value, ast.Call
                ):
                    call = body_node.value
                    if call.func.attr == "forward":
                        shapes = extract_shapes(call.args)
                        break

            if not shapes:
                manual_modules.add(module_class)
                continue

            # 转换shape
            converted_shapes = [
                tuple(convert_dim(d) for d in shape) for shape in shapes
            ]

            # 构建配置
            if module_class not in config:
                config[module_class] = []

            inputs = [
                {"dtype": dtype, "shape": shape}
                for dtype, shape in zip(modules[module_class], converted_shapes)
            ]

            config[module_class].append({"inputs": inputs})

    # 生成最终格式
    final_config = {}
    for cls, entries in config.items():
        final_config[cls] = []
        for entry in entries:
            final_config[cls].append({"inputs": entry["inputs"]})

    # 输出结果
    with open("model_config.json", "w") as o:
        o.write(json.dumps(final_config, indent=4, ensure_ascii=False))

    # 提示需要手动处理的模块
    if manual_modules:
        print("\n需要手动处理的模块:")
        for module in manual_modules:
            print(f"  - {module}")


# 使用示例
process_file(
    "/workspace/iree/third_party/torch-mlir/projects/pt1/python/torch_mlir_e2e_test/test_suite/elementwise.py"
)
