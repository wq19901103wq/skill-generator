# AI Quickstart: Skill Generator

> 如果你是一名 AI Agent / 开发者，第一次接触这个项目，请从这里开始。

---

## 30 秒看懂项目

**Skill Generator** 是一个从任意资料（PDF/Word/TXT/聊天记录）自动生成 [OpenClaw Skill](https://github.com/wq19901103wq/skill-generator) 的工具。

核心流程：

```
用户资料 → FileParser 解析 → UniversalExtractor LLM提取 → TemplateRenderer 渲染 → 生成 Skill
```

**当前稳定版本**: v3.0（Karpathy Style Wiki）
**唯一入口**: `python3 skill_generator.py`

---

## 5 分钟上手

### 1. 读三个文件

按顺序读：
1. [../README.md](../README.md) — 用户视角的用法说明
2. [../PROJECT_MAP.md](../PROJECT_MAP.md) — 系统架构和组件说明
3. 本文档的「模块速查表」和「关键禁忌」

### 2. 修改代码前必读

- **所有模板文件**在 `templates/` 下，不要改 `skill_generator.py` 里的硬编码模板
- **LLM Prompt** 在 `extractors/universal_extractor.py` 里，修改时注意保持 JSON 输出格式
- **提取字段**由 `ExtractedInfo` dataclass 定义，增删字段会影响所有模板
- **模板变量**使用 `{snake_case}`，区分大小写

### 3. 排查问题看日志

```bash
# 运行生成器，观察输出
python3 skill_generator.py --smart --from-files 测试.pdf --name "测试"

# 检查生成的 Skill 结构
tree ~/.openclaw/skills/测试-digital-twin/

# 验证 tool.py 是否能运行
python3 ~/.openclaw/skills/测试-digital-twin/scripts/tool.py query "测试"
```

### 4. 测试

```bash
cd ~/.openclaw/workspace/skill-generator

# 测试文件解析
python3 -c "from extractors import FileParser; p = FileParser(); print(p.parse('examples/xxx.pdf'))"

# 测试 LLM 提取
python3 -c "from extractors import extract_with_llm; info = extract_with_llm('这是测试内容'); print(info.document_type)"

# 完整生成测试
python3 skill_generator.py --smart --from-files 测试文件 --name "测试" --output /tmp/test_output
```

---

## 模块速查表

| 如果你要改... | 读这个文件 | 注意 |
|--------------|-----------|------|
| 支持的文件格式 | `extractors/file_parser.py` | 添加新的 `_parse_xxx` 方法，并在 `parse()` 中注册 |
| LLM 提取逻辑 / Prompt | `extractors/universal_extractor.py` | 修改 `_extract_*()` 方法中的 prompt，保持返回 `ExtractedInfo` |
| 文档类型识别 | `extractors/universal_extractor.py` `_identify_document_type()` | 修改 system prompt，枚举值必须在 `DocumentType` 中 |
| 模板变量 / 默认值 | `templates/personal_digital_twin/manifest.json` | `defaults` 中定义默认值，`required_fields` 中声明必填 |
| SKILL.md 内容 | `templates/personal_digital_twin/SKILL.md.template` | 使用 `{变量名}` 占位符 |
| tool.py 逻辑 | `templates/personal_digital_twin/scripts/tool.py.template` | 这是生成的 Skill 的脚本模板 |
| Wiki 文件生成 | `skill_generator.py` `_generate_wiki_*()` | 根据 `config` 字典生成 Markdown 内容 |
| 目录结构 | `skill_generator.py` `_create_structure()` | 从 `manifest.json` 的 `directories` 读取 |
| 添加新模板 | 参考 [TEMPLATE_GUIDE.md](./TEMPLATE_GUIDE.md) | 创建 `templates/新模板名/` 目录 |
| 添加新 LLM 后端 | `extractors/universal_extractor.py` `LLMBackend` | 添加 `_xxx_complete()` 方法 |

---

## 关键数据流

```
[FileParser]        原始文本
    ↓
[UniversalExtractor]  ExtractedInfo (document_type, name, title...)
    ↓
[SkillGenerator.generate()]  验证 + 渲染
    ↓
[TemplateRenderer]  替换 {变量}
    ↓
[_generate_wiki_files()]  data/wiki/*.md
    ↓
生成的 Skill 目录
```

---

## 关键禁忌（会直接导致 bug）

❌ **不要修改 `ExtractedInfo` 的现有字段名**

原因：所有模板和 `_generate_wiki_*` 方法都依赖这些字段名，改名会导致模板渲染失败或生成空内容。

✅ 正确做法：新增字段用 `Optional`，老代码不填时提供默认值。

```python
@dataclass
class ExtractedInfo:
    document_type: DocumentType
    name: Optional[str] = None
    title: Optional[str] = None
    # 新增字段 ✅
    industry: Optional[str] = None  # 老模板不填也没问题
```

---

❌ **不要在模板里硬编码路径**

原因：生成的 Skill 目录名是根据 `name` 自动生成的（拼音/连字符），硬编码路径会指向不存在的目录。

✅ 正确做法：使用 `{skill_name}` 或 `{skill_name_underscore}` 变量。

```markdown
<!-- 错误 ❌ -->
import data/persona/王艺涵.py

<!-- 正确 ✅ -->
import data/persona/{name}.py
```

---

❌ **不要修改 `DocumentType` 枚举值的字符串值**

原因：`_identify_document_type()` 的 prompt 中让 LLM 返回特定的字符串来匹配枚举，改了字符串 LLM 就匹配不上了。

✅ 正确做法：新增类型时，在 Enum 中加新成员，同时在 `_identify_document_type()` 和对应 `_extract_xxx()` 中处理。

---

❌ **不要在 `complete()` 中吞掉所有异常**

原因：LLM API 失败时如果没有抛异常，会返回空字符串或 fallback 内容，导致提取结果为空，生成错误的 Skill。

✅ 正确做法：在 `LLMBackend.complete()` 中记录错误日志，让上层知道 API 调用失败了。

---

## FAQ

**Q: 为什么旧版本有 `persona_extractor.py` 和 `chat_parser.py`？**

A: 历史原因。v1.0 使用基于规则的正则提取（仅支持简历），v2.0 引入了 `UniversalExtractor` 用 LLM 智能提取任意类型资料。旧的 `PersonaExtractor` 仍保留作为传统模式的后备，但**新功能应该在 `UniversalExtractor` 中实现**。

**Q: 改了模板后怎么验证？**

A: 三步验证法：
1. `python3 skill_generator.py --template personal_digital_twin --name "测试" --output /tmp/test`
2. `cat /tmp/test/测试-digital-twin/SKILL.md` 检查变量是否渲染正确
3. `python3 /tmp/test/测试-digital-twin/scripts/tool.py query "测试"` 验证 tool.py 能运行

**Q: 出了问题怎么排查？**

A: 按这个顺序：
1. 看终端输出 — 文件解析是否成功？LLM 提取返回了什么？
2. 检查生成的 `config` 字典 — `print(config)` 看字段是否完整
3. 检查模板变量名 — 大小写是否匹配？`manifest.json` 的 `defaults` 中是否有默认值？
4. 查看 [MODULE_INDEX.md](./MODULE_INDEX.md) — 按现象查修改位置

**Q: 新功能加在哪里？**

A: 先看它属于哪个环节：
- 支持新文件格式 → `extractors/file_parser.py`
- 支持新资料类型 → `extractors/universal_extractor.py`
- 改生成内容 → `templates/personal_digital_twin/*.template`
- 改 Wiki 结构 → `skill_generator.py` 的 `_generate_wiki_*` 方法
- 改生成目录 → `manifest.json` 的 `directories` 和 `files`

---

*最后更新: 2026-04-21*
