#!/bin/bash

# 参数检查
if [ $# -ne 1 ]; then
    echo "用法：$0 <操作名称>"
    exit 1
fi

OP_NAME="$1"
LOG_FILE="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/${OP_NAME}/${OP_NAME}/${OP_NAME}_dlc_log.txt"

# 调试：打印日志文件路径
echo "检查日志文件路径：$LOG_FILE"

# 检查日志文件是否存在
if [ ! -f "$LOG_FILE" ]; then
    echo "错误：日志文件不存在 - $LOG_FILE"
    exit 1
fi

# 提取周期数
declare -A CYCLES
# echo "开始处理日志内容..."
grep "Program executed" "$LOG_FILE" | while IFS= read -r line; do
    # echo "正在处理行：$line"
    if [[ $line =~ \[xys([0-9]+)\].*Program\ executed\ ([0-9]+)\ cycles\. ]]; then
        xys_num="${BASH_REMATCH[1]}"
        cycles="${BASH_REMATCH[2]}"
        echo "匹配成功：xys${xys_num} cycles=$cycles"
        CYCLES["xys${xys_num}"]="$cycles"
    else
        echo "未匹配到有效数据"
    fi
done < <(grep "Program executed" "$LOG_FILE")  # 使用进程替换（Process Substitution）

# 检查是否找到数据
if [ ${#CYCLES[@]} -eq 0 ]; then
    echo "错误：未找到任何周期数据"
    exit 1
fi

# 输出结果
output=""
for key in xys0 xys1; do
    if [ -n "${CYCLES[$key]}" ]; then
        output+="${key}:${CYCLES[$key]} cycle, "
    else
        output+="${key}:N/A cycle, "
    fi
done

echo "${output%, }"
