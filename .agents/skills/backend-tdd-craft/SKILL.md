---
name: backend-tdd-craft
description: Python 后端开发工程纪律规范，强制执行 TDD 红绿循环、pytest 自动化验证与边界防护自检
---

# Backend TDD & Engineering Craft 规范

在修改或实现本项目的 Python 业务逻辑（app/services/、app/main.py）时，严格遵循以下流程：

## 1. 计划与测试先行 (Red 阶段)
- 严禁未经确认直接修改业务核心代码。
- 优先查阅项目根目录下的现有测试用例（如 test_p1.py、test_im_channels.py 等）。
- 若为新增特性或修改 Bug，必须先编写/修改对应测试脚本中的 assert 断言，明确待测逻辑。

## 2. 最小化实现与验证 (Green 阶段)
- 仅编写能让 pytest 对应脚本通过的最简代码。
- 每次改动后，在终端提示执行对应的测试命令（例如：pytest test_p1.py -v）。

## 3. 防御性自检清单 (Verification)
- [ ] 是否处理了空入参、NoneType 异常？
- [ ] 修改是否破坏了已有的渠道兼容逻辑（如 IM 渠道、多语言适配）？
- [ ] 异步/上下文资源是否安全释放？