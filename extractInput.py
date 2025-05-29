import ast
import json


def convert_dim(d):
    if d == 1:
        return 1
    converted = 128 * (2 ** (d - 1))
    return min(converted, 4096)


def parse_annotate_args(decorator_list):
    for decorator in decorator_list:
        if isinstance(decorator, ast.Call) and decorator.func.id == "annotate_args":
            args = decorator.args[0].elts[1:]  # 跳过第一个None
            dtypes = []
            for arg in args:
                if isinstance(arg, ast.Tuple):
                    dtype_node = arg.elts[1]
                    if (
                        isinstance(dtype_node, ast.Attribute)
                        and dtype_node.value.id == "torch"
                    ):
                        dtypes.append(dtype_node.attr)
            return dtypes
    return []


def extract_shapes(args):
    shapes = []
    for arg in args:
        if (
            isinstance(arg, ast.Call)
            and arg.func.attr == "rand"
            and arg.func.value.id == "tu"
        ):
            dims = []
            for dim in arg.args[:2]:
                if isinstance(dim, ast.Constant):
                    dims.append(dim.value)
                else:
                    return None
            shapes.append(tuple(dims))
        else:
            return None
    return shapes


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
