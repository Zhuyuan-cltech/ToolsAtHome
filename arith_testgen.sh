#!/bin/bash

# 参数检查
if [ $# -ne 2 ]; then
  echo "用法：$0 <操作名称> <mode>"
  echo "有效mode: i, f, ii, ff, if, fi"
  echo "示例：$0 Trunc i"
  exit 1
fi

OP_NAME="$1"
MODE="$2"

# 验证mode参数合法性
valid_modes=("i" "f" "ii" "ff" "if" "fi" "iii")
if [[ ! " ${valid_modes[*]} " =~ " ${MODE} " ]]; then
  echo "错误：无效的mode参数，支持的mode为: ${valid_modes[*]}"
  exit 1
fi

# 定义模板目录（根据实际路径调整）
# TEMPLATE_DIR_I32="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/Sin"
TEMPLATE_DIR_F32="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/NegF"
TEMPLATE_DIR_F32_F32="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/AddF"
TEMPLATE_DIR_I32_I32="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/AddI"
# TEMPLATE_DIR_I32_F32="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/Pow"
TEMPLATE_DIR_F32_I32="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/FPowi"
TEMPLATE_DIR_I32_I32_I32="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/AddUIExtended"

# 根据mode选择模板目录
case "$MODE" in
# "i") TEMPLATE_DIR="$TEMPLATE_DIR_I32" ;;
"f") TEMPLATE_DIR="$TEMPLATE_DIR_F32" ;;
"ii") TEMPLATE_DIR="$TEMPLATE_DIR_I32_I32" ;;
"ff") TEMPLATE_DIR="$TEMPLATE_DIR_F32_F32" ;;
# "if") TEMPLATE_DIR="$TEMPLATE_DIR_I32_F32" ;;
# "fi") TEMPLATE_DIR="$TEMPLATE_DIR_F32_I32" ;;
"iii") TEMPLATE_DIR="$TEMPLATE_DIR_I32_I32_I32" ;;
*)
  echo "错误：未配置的mode参数"
  exit 1
  ;;
esac

# 检查模板目录是否存在
if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "错误：模板目录不存在 - $TEMPLATE_DIR"
  exit 1
fi

# 提取模板目录的基名（确保路径正确）
TEMPLATE_BASE=$(basename "$TEMPLATE_DIR")
# 转换为小写（处理空值）
TEMPLATE_OP_LOWER=$(echo "$TEMPLATE_BASE" | tr '[:upper:]' '[:lower:]')

TARGET_DIR="/workspace/iree/tests/e2e/dlc_specific/test_set/aten_ops/${OP_NAME}"

# 创建目标目录（确保权限）
mkdir -p "${TARGET_DIR}" || {
  echo "无法创建目录: ${TARGET_DIR}"
  exit 1
}

# 复制文件（确保模板文件存在）
MLIR_FILE="${TEMPLATE_DIR}/${TEMPLATE_BASE}.mlir"
if [ ! -f "$MLIR_FILE" ]; then
  echo "错误：模板文件不存在 - $MLIR_FILE"
  exit 1
fi
cp "$MLIR_FILE" "${TARGET_DIR}/${OP_NAME}.mlir" || exit 1

# 替换操作符和标识符（修复换行符和变量）
sed -i.bak \
  -e "s/arith\.${TEMPLATE_OP_LOWER}/arith.${OP_NAME,,}/g" \
  -e "s/${TEMPLATE_BASE}/${OP_NAME}/g" \
  "${TARGET_DIR}/${OP_NAME}.mlir"

# 清理备份文件
rm -f "${TARGET_DIR}/${OP_NAME}.mlir.bak"

# 修复权限（可选）
chmod 644 "${TARGET_DIR}/${OP_NAME}.mlir"

echo "生成成功： ${TARGET_DIR}/${OP_NAME}.mlir"
