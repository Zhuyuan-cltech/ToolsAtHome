#! /bin/bash
cd /workspace/iree/tests/e2e/dlc_specific
source ../../../set-env
cmake --build ../../../../iree-build/

echo "Test Instruction: cmake --build ../../../../iree-build/ && python3 -m pytest -vs ./test_set/aten_ops/test_aten_ops.py::test_reciprocal"