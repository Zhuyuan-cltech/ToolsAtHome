import csv


def process_row(row):
    # 处理输入部分
    inputs = []
    for i in range(1, 4):
        dtype = row.get(f"input{i}_dtype", "").strip()
        shape = row.get(f"input{i}_shape", "").strip()
        if dtype and shape:
            # 统一输入格式为 [dim1,dim2]
            clean_shape = shape.strip('[]"').replace(" ", "")
            formatted_shape = f"[{clean_shape}]"
            # 数据类型缩写
            dtype_abbr = (
                "f32" if dtype == "float32" else ("i32" if dtype == "int32" else dtype)
            )
            inputs.append(f"{formatted_shape}.{dtype_abbr}")
    input_part = ";".join(inputs)

    # 处理输出部分（动态检测多个输出）
    outputs = []
    output_idx = 0
    while True:
        dtype = row.get(f"output{output_idx}_dtype", "").strip()
        shape = row.get(f"output{output_idx}_shape", "").strip()
        if not dtype or not shape:
            break
        # 统一输出格式为 (dim1,dim2)
        clean_shape = shape.strip('[]()"').replace(" ", "")
        formatted_shape = f"({clean_shape})"
        dtype_abbr = (
            "f32" if dtype == "float32" else ("i32" if dtype == "int32" else dtype)
        )
        outputs.append(f"{formatted_shape}.{dtype_abbr}")
        output_idx += 1
    output_part = ";".join(outputs)

    # 提取性能指标
    xys0 = row.get("xys0_cycle", "").strip()
    xys1 = row.get("xys1_cycle", "").strip()

    return f"{row['module'].strip()}\t{input_part}\t{output_part}\t{xys0}\t{xys1}"


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python process.py input.csv")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(process_row(row))


if __name__ == "__main__":
    main()
