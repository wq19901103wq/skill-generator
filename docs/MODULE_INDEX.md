# 模块索引 (Module Index)

> AI 开发时的快速导航页。
>
> 规则：如果你不知道该改哪个文件，先查此表。

---

## 按问题类型索引

### "文件解析失败"

| 现象 | 可能原因 | 修改文件 |
|------|---------|---------|
| PDF 解析报错 | PyPDF2 版本不兼容或 PDF 加密 | `extractors/file_parser.py` `_parse_pdf()` |
| Word 解析报错 | python-docx 未安装或文件损坏 | `extractors/file_parser.py` `_parse_docx()` |
| CSV 解析乱码 | 编码不是 UTF-8 | `extractors/file_parser.py` `_parse_csv()`，加编码检测 |
| 不支持的文件格式 | `detect_file_type()` 没识别到扩展名 | `extractors/file_parser.py` `detect_file_type()` |
| 大文件解析很慢 | 全文读取导致内存占用高 | `extractors/file_parser.py` 添加分页/截断逻辑 |

### "LLM 提取结果不对"

| 现象 | 可能原因 | 修改文件 |
|------|---------|---------|
| 文档类型识别错误 | `_identify_document_type()` 的 prompt 不够明确 | `extractors/universal_extractor.py` |
| 提取字段为空 | LLM 返回的 JSON 格式不规范，`_parse_json_fuzzy()` 没解析到 | `extractors/universal_extractor.py` `_parse_json_fuzzy()` |
| 提取内容不完整 | prompt 中的示例不够，或 max_tokens 太小 | `extractors/universal_extractor.py` 对应 `_extract_*()` 方法 |
| LLM 调用超时 | 网络问题或 API 响应慢 | `extractors/universal_extractor.py` `LLMBackend.complete()`，加 timeout |
| LLM 返回非 JSON | prompt 中没有强调"必须返回 JSON" | `extractors/universal_extractor.py` 修改 system prompt |
| API Key 无效 | 环境变量未设置或 Key 过期 | 检查 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` |

### "生成的 Skill 结构不对"

| 现象 | 可能原因 | 修改文件 |
|------|---------|---------|
| 缺少某个文件 | `manifest.json` 的 `files` 映射不完整 | `templates/personal_digital_twin/manifest.json` |
| 目录没创建 | `manifest.json` 的 `directories` 没包含 | `templates/personal_digital_twin/manifest.json` |
| 模板变量没渲染 | 变量名大小写不匹配或 config 中没有该字段 | `templates/personal_digital_twin/*.template` / `manifest.json` `defaults` |
| 变量渲染为空 | `config` 中没有该字段，且 `defaults` 也没默认值 | `manifest.json` `defaults` |
| 生成的目录名乱码 | 中文名转拼音失败 | `skill_generator.py` `_name_to_pinyin_slug()` |
| Wiki 文件缺失 | `_generate_wiki_files()` 中某类信息为空 | `skill_generator.py` 对应 `_generate_wiki_*()` 方法 |

### "生成的 Skill 在 OpenClaw 中不生效"

| 现象 | 可能原因 | 修改文件 |
|------|---------|---------|
| 触发词不响应 | `SKILL.md` 中 triggers 配置错误 | `templates/personal_digital_twin/SKILL.md.template` |
| tool.py 执行报错 | 路径硬编码或依赖缺失 | `templates/personal_digital_twin/scripts/tool.py.template` |
| OpenClaw 没有加载 Skill | Skill 目录不在 `~/.openclaw/skills/` 下 | 检查 `--output` 参数 |
| Skill 语法错误 | `SKILL.md` 格式不符合 OpenClaw 规范 | 参考 OpenClaw 官方文档 |
| 回复内容不对 | Wiki 文件内容为空或路径错误 | `templates/personal_digital_twin/scripts/tool.py.template` 中读取逻辑 |

### "说话风格不像"

| 现象 | 可能原因 | 修改文件 |
|------|---------|---------|
| 没有语气词 | `particles` 为空或模板没使用 | `templates/personal_digital_twin/manifest.json` `defaults` |
| 回复太正式 | `tone_examples` 和 `reply_examples` 不够口语化 | `templates/personal_digital_twin/manifest.json` `defaults` |
| 没有使用聊天记录风格 | 没有提供 `--chat-files` 或 `ChatParser` 没提取到 | 检查输入文件 / `extractors/chat_parser.py` |

---

## 按文件索引

### `skill_generator.py`
- **定位**: CLI 入口 + 生成主逻辑
- **改什么**: 主流程、Wiki 生成逻辑、命令行参数
- **不改什么**: 文件解析（在 extractors/）、LLM 调用（在 extractors/）
- **排查必读**: 终端输出会直接打印生成进度

### `extractors/file_parser.py`
- **定位**: 多格式文件解析
- **改什么**: 支持新文件格式、编码处理、大文件优化
- **不改什么**: 信息提取逻辑（那是 UniversalExtractor 的事）
- **关键方法**: `parse()`, `detect_file_type()`, `_parse_*()`

### `extractors/universal_extractor.py`
- **定位**: ⭐ LLM 智能提取核心
- **改什么**: 
  - 新资料类型的 `_extract_*()` 方法
  - `_identify_document_type()` 的识别 prompt
  - `LLMBackend` 的新后端支持
- **不改什么**: 文件读取（FileParser 负责）
- **关键类**: `UniversalExtractor`, `LLMBackend`, `ExtractedInfo`, `DocumentType`
- **排查必读**: 打印 `ExtractedInfo` 看字段是否完整

### `extractors/persona_extractor.py`
- **定位**: 传统规则提取（仅简历类）
- **改什么**: 一般不修改，新功能加到 UniversalExtractor
- **状态**: 遗留代码，为传统模式保留

### `extractors/chat_parser.py`
- **定位**: 聊天记录分析和说话风格提取
- **改什么**: 支持新聊天记录格式、改进风格分析算法
- **不改什么**: 通用信息提取

### `templates/personal_digital_twin/manifest.json`
- **定位**: 模板配置中心
- **改什么**: 
  - `defaults` 中的默认值
  - `required_fields` 必填字段
  - `directories` 需要创建的目录
  - `files` 模板文件映射
- **注意**: 改 `defaults` 会影响所有新生成的 Skill，不影响已生成的

### `templates/personal_digital_twin/SKILL.md.template`
- **定位**: OpenClaw Skill 定义模板
- **改什么**: Skill 的触发词、描述、requires 等
- **语法**: `{变量名}` 占位符，变量在 `manifest.json` 的 `defaults` 或用户 config 中提供

### `templates/personal_digital_twin/scripts/tool.py.template`
- **定位**: 生成的 Skill 的工具脚本模板
- **改什么**: Skill 的功能逻辑（查询、发送文件等）
- **注意**: 这是**模板**，不是直接运行的脚本。运行的是生成后的 `scripts/tool.py`

### `templates/personal_digital_twin/AGENTS_RULE.md.template`
- **定位**: AI Agent 行为规则模板
- **改什么**: 让 AI 如何回复的约束规则

---

## 依赖图

```
extractors/file_parser.py
    ↑
    ├── extractors/universal_extractor.py  ← LLMBackend, ExtractedInfo
    │       ↑
    │   skill_generator.py  ← SkillGenerator.generate()
    │       ↑
    │   templates/personal_digital_twin/*.template
    │
    └── extractors/persona_extractor.py  ← 遗留，传统模式用
    └── extractors/chat_parser.py      ← 聊天记录分析
```

**新增文件的正确位置**:
- 新文件格式解析 → `extractors/file_parser.py` 的新方法
- 新资料类型提取 → `extractors/universal_extractor.py` 的新 `_extract_*()` 方法
- 新模板 → `templates/{模板名}/` 新目录
- 新 LLM 后端 → `extractors/universal_extractor.py` `LLMBackend` 的新方法

---

*最后更新: 2026-04-21*
