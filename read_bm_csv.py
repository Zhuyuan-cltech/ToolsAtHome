import csv


def process_row(row):
    inputs = []
    for i in range(1, 4):
        dtype = row.get(f"input{i}_dtype", "").strip()
        shape = row.get(f"input{i}_shape", "").strip()
        if dtype and shape:
            dtype_abbr = "f32" if dtype == "float32" else dtype
            inputs.append(f"{shape}.{dtype_abbr}")
    input_part = ";".join(inputs)

    output_dtype = row.get("output0_dtype", "").strip()
    output_shape = (
        row.get("output0_shape", "").strip().replace("[", "").replace("]", "")
    )
    output_abbr = "f32" if output_dtype == "float32" else output_dtype
    output_part = f"{output_shape}.{output_abbr}"

    xys0 = row.get("xys0_cycle", "").strip()
    xys1 = row.get("xys1_cycle", "").strip()

    module = row["module"].strip()
    return f"{module}||{input_part}||{output_part}||{xys0}||{xys1}"


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python process_csv.py input.csv")
        sys.exit(1)

    with open(sys.argv[1], "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(process_row(row))


if __name__ == "__main__":
    main()
