import re

if __name__ == "__main__":
    file_path = "/workspace/iree/tests/e2e/dlc_specific/sim_xys0_debug_info.txt"
    output_file = "/workspace/iree/tests/e2e/dlc_specific/compressed_debug_info.txt"
    pattern = r"INFO: "
    filtered_log = []

    with open(file_path, "r", encoding="utf-8") as dbf:
        context = dbf.read()

        cols = [str(x) for x in range(128)]

        blocks = re.split(pattern, context)
        blocks = [block.strip() for block in blocks if block.strip()]

        isCols = False
        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            i = 0
            while i < len(lines):
                l = lines[i]
                i += 1
                if l.endswith("information ends, info as above."):
                    continue
                if re.match(r"\d{1,2}", l):
                    l = l.split()
                    if l == cols:
                        isCols = True
                        continue
                    if isCols:
                        pattern = re.compile(r'-?\d+\.\d+\(-?\d+\)')
                        match = pattern.search(l[0])
                        if match:
                            filtered_log += [match.group(0)]
                        else:
                            filtered_log += [l[1]]
                        i += 7
                        isCols = False
                        continue
                filtered_log += [l]
            
    with open(output_file, "w", encoding="utf-8") as outf:
            for line in filtered_log:
                outf.write(line + "\n") 
        
    print(f"Filtered log has been written to {output_file}")