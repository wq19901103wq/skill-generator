# Skill Generator 编码规范

> 所有贡献者必须遵守的编码规范，保证代码风格一致、易于维护。

---

## 1. 基础规范

### 1.1 Python 版本

- **最低支持**: Python 3.8+
- **推荐版本**: Python 3.10+

### 1.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `SkillGenerator`, `UniversalExtractor` |
| 函数/方法 | snake_case | `extract_from_files()`, `_parse_pdf()` |
| 私有方法 | 下划线前缀 + snake_case | `_merge_config()`, `_render_string()` |
| 常量 | 全大写 + 下划线 | `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT` |
| 模块名 | 全小写 + 下划线 | `file_parser.py`, `universal_extractor.py` |
| 变量名 | snake_case | `file_path`, `extracted_info` |

### 1.3 文件编码

- 所有 `.py` 文件使用 **UTF-8** 编码
- 文件顶部添加模块 docstring

```python
"""
文件提取模块 - 从各种文件格式中提取个人信息

支持两种模式：
1. 规则提取（PersonaExtractor）- 基于正则，适合简历
2. LLM 提取（UniversalExtractor）- 智能识别任意资料类型
"""
```

---

## 2. 类型注解

### 2.1 强制要求

**所有公共方法的参数和返回值必须添加类型注解。**

```python
# ✅ 正确
def extract(self, content: str, hint: str = None) -> ExtractedInfo:
    pass

# ❌ 错误
def extract(self, content, hint=None):
    pass
```

### 2.2 常用类型

```python
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# 简单类型
name: str
age: int
scores: List[float]

# 复杂类型
config: Dict[str, Any]
file_paths: List[Union[str, Path]]
result: Optional[ExtractedInfo]

# 返回值可能为 None
def parse(self, file_path: Union[str, Path]) -> Optional[Dict]:
    pass
```

### 2.3 自定义类型

如果某个类型在多个地方使用，定义类型别名：

```python
from typing import Dict, Any

# 在模块级别定义
ConfigDict = Dict[str, Any]
FileContents = Dict[str, str]

def process(config: ConfigDict, contents: FileContents) -> ConfigDict:
    pass
```

---

## 3. 文档字符串 (Docstring)

### 3.1 格式

使用 **简洁描述** 风格，包含 Args/Returns/Raises：

```python
# ✅ 推荐
def extract(self, content: str, hint: str = None) -> ExtractedInfo:
    """
    从文本中提取结构化信息。

    Args:
        content: 输入文本内容
        hint: 类型提示，帮助 LLM 更准确地识别文档类型

    Returns:
        ExtractedInfo: 提取的信息结构

    Raises:
        ValueError: 当 content 为空时
    """
    pass
```

### 3.2 要求

- **公共方法**（无下划线前缀）必须有 docstring
- **私有方法**（有下划线前缀）可选，但复杂逻辑建议加
- **简单属性/ getter** 可以省略

---

## 4. 异常处理

### 4.1 基本原则

- **不要裸 except**：永远捕获具体的异常类型
- **不要吞掉异常**：至少记录日志，最好让上层知道
- **异常信息要包含上下文**：说明什么操作失败了

```python
# ✅ 正确
try:
    result = file_parser.parse(path)
except FileNotFoundError:
    print(f"  ⚠️ 文件不存在: {file_path}")
    continue
except PermissionError:
    print(f"  ⚠️ 没有权限读取: {file_path}")
    continue
except Exception as e:
    print(f"  ❌ 解析失败 ({path.name}): {e}")
    continue

# ❌ 错误
try:
    result = file_parser.parse(path)
except:
    pass  # 完全吞掉异常，不知道发生了什么
```

### 4.2 自定义异常

当项目复杂到一定程度，定义自定义异常类：

```python
class SkillGeneratorError(Exception):
    """Skill Generator 基础异常"""
    pass

class ExtractorError(SkillGeneratorError):
    """提取器异常"""
    pass

class TemplateError(SkillGeneratorError):
    """模板异常"""
    pass
```

---

## 5. 日志和输出

### 5.1 输出规范

`skill_generator.py` 作为 CLI 工具，使用 `print()` 向用户展示进度，格式统一：

```python
# 阶段标题
print("🔍 正在分析文件...")

# 成功
print(f"  📄 {path.name}")
print(f"  ✅ 提取完成！")

# 警告
print(f"  ⚠️ 文件不存在: {file_path}")

# 错误
print(f"  ❌ 解析失败: {e}")

# 结果汇总
print(f"\n✅ Skill 生成成功!")
print(f"   路径: {skill_path}")
```

### 5.2 日志规范

非 CLI 的模块（如 extractors/）建议使用 `logging`：

```python
import logging

logger = logging.getLogger(__name__)

def parse(self, file_path):
    logger.debug(f"开始解析文件: {file_path}")
    # ...
    logger.info(f"文件解析成功: {file_path}, 大小: {len(content)} 字符")
```

---

## 6. 代码组织

### 6.1 模块职责

| 模块 | 职责 | 禁止做的事 |
|------|------|-----------|
| `extractors/` | 文件解析和信息提取 | 不处理模板渲染 |
| `templates/` | Skill 模板定义 | 不包含业务逻辑 |
| `skill_generator.py` | 生成主逻辑和 CLI | 不直接操作文件解析细节 |
| `tests/` | 测试用例 | 不包含生产代码 |

### 6.2 导入顺序

```python
# 1. 标准库
import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# 2. 第三方库
import PyPDF2

# 3. 本项目模块
from extractors import (
    FileParser, PersonaExtractor, ChatParser,
    UniversalExtractor, LLMBackend
)
```

---

## 7. 向后兼容

### 7.1 核心原则

**不删除已有功能，不修改已有接口。**

### 7.2 新增字段

```python
# ✅ 正确：新增字段用 Optional，提供默认值
@dataclass
class ExtractedInfo:
    document_type: DocumentType
    name: Optional[str] = None
    title: Optional[str] = None
    # 新增字段 ✅
    industry: Optional[str] = None  # 老模板不填也没问题

# ❌ 错误：修改现有字段名
@dataclass
class ExtractedInfo:
    document_type: DocumentType
    # person_name 改为 name ❌ 会破坏所有调用方
    person_name: Optional[str] = None
```

### 7.3 废弃接口

如果要废弃某个接口，使用 `warnings`：

```python
import warnings

def old_method(self):
    """已废弃，请使用 new_method()"""
    warnings.warn(
        "old_method() 已废弃，请使用 new_method()",
        DeprecationWarning,
        stacklevel=2
    )
    return self.new_method()
```

---

## 8. 测试规范

### 8.1 测试文件命名

```
tests/
├── test_extractors.py          # 测试 extractors/ 模块
├── test_skill_generator.py     # 测试主生成器
├── test_templates.py           # 测试模板渲染
└── fixtures/                   # 测试数据
    ├── sample_resume.pdf
    ├── sample_chat.txt
    └── README.md
```

### 8.2 测试基本要求

- 所有公共方法必须有对应的单元测试
- 测试使用 `pytest`
- 测试函数命名：`test_被测方法名_场景描述`

```python
def test_file_parser_pdf():
    """测试 PDF 文件解析"""
    parser = FileParser()
    result = parser.parse("tests/fixtures/sample_resume.pdf")
    assert result is not None
    assert len(result['content']) > 0

def test_universal_extractor_resume():
    """测试 UniversalExtractor 识别简历类型"""
    extractor = UniversalExtractor()
    info = extractor.extract("张三，产品经理，5年经验...")
    assert info.document_type == DocumentType.RESUME
    assert info.name == "张三"
```

---

## 9. 提交规范

使用 **Conventional Commits** 风格：

```
feat: 添加新功能
docs: 更新文档
fix: 修复 bug
refactor: 重构代码（不是修复 bug 也不是添加功能）
test: 添加测试
chore: 构建/工具链变更
```

示例：
```bash
git commit -m "feat: 添加 medical_records 文档类型支持"
git commit -m "fix: 修复 PDF 解析中文乱码问题"
git commit -m "docs: 更新 AI_QUICKSTART.md 模块速查表"
```

---

## 10. 代码审查清单

提交 PR 前自查：

- [ ] 代码符合本规范
- [ ] 所有公共方法有类型注解
- [ ] 所有公共方法有 docstring
- [ ] 没有裸 `except:`
- [ ] 没有 `print()` 调试语句（CLI 输出除外）
- [ ] 新增功能有对应的测试
- [ ] 没有破坏向后兼容
- [ ] 文档已更新（README/API/MODULE_INDEX）

---

*最后更新: 2026-04-21*
