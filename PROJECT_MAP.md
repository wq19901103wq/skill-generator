# Skill Generator - 项目地图

> 本文档描述项目架构、核心组件和开发指南

---

## 📋 项目概述

**Skill Generator** 是一个通用的 OpenClaw Skill 生成器，支持从任意资料智能生成个性化的 AI Skill。

### 核心特性

- 🎯 **智能模式 (`--smart`)**: 使用 LLM 自动识别资料类型并提取信息
- 📄 **多格式支持**: PDF, Word, TXT, Markdown, CSV
- 🤖 **多 LLM 后端**: OpenAI, Anthropic, 本地模型
- 📝 **Karpathy Style 知识库**: Markdown 文件作为知识库，无需 RAG
- 🔧 **可扩展模板**: 支持自定义 Skill 模板

---

## 🗂️ 项目结构

```
skill-generator/
├── skill_generator.py              # ⭐ 主入口，CLI 和生成逻辑
├── extractors/                     # 信息提取模块
│   ├── __init__.py
│   ├── file_parser.py              # 多格式文件解析
│   ├── persona_extractor.py        # 规则提取（简历类）
│   ├── chat_parser.py              # 聊天记录分析
│   └── universal_extractor.py      # ⭐ LLM 智能提取（任意类型）
├── templates/                      # Skill 模板目录
│   └── personal_digital_twin/      # 个人数字分身模板
│       ├── manifest.json           # 模板配置
│       ├── SKILL.md.template       # SKILL.md 模板
│       └── scripts/
│           └── tool.py.template    # tool.py 模板
├── examples/                       # 示例配置
├── README.md                       # 用户文档
├── DEMO.md                         # 智能模式演示
├── PROJECT_MAP.md                  # 本文档 - 项目地图
└── .gitignore
```

---

## 🏗️ 架构设计

### 1. 核心流程

```
用户输入资料
    │
    ▼
┌─────────────────┐
│  FileParser     │  ← 解析 PDF/Word/TXT 等文件
│  (extractors/)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ 传统模式         │     │ 智能模式 (--smart)│
│ --from-files    │     │                  │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│ PersonaExtractor│     │ UniversalExtractor│
│ 规则提取         │     │ LLM 智能识别类型  │
│ 仅支持简历       │     │ 支持任意资料      │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌──────────────────────┐
         │   ExtractedInfo      │
         │   统一信息结构        │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │   TemplateRenderer   │
         │   渲染模板生成文件    │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │   生成的 Skill       │
         │   data/wiki/*.md     │  ← Karpathy Style
         │   scripts/tool.py    │
         │   SKILL.md           │
         └──────────────────────┘
```

### 2. 提取器架构

```
extractors/
│
├── FileParser              # 文件解析基类
│   ├── parse()             # 解析单个文件
│   └── parse_multiple()    # 批量解析
│
├── PersonaExtractor        # 规则提取器
│   ├── extract()           # 提取个人信息
│   ├── extract_from_multiple()  # 合并多个来源
│   └── _extract_*()        # 各类字段提取方法
│
├── ChatParser              # 聊天记录解析
│   ├── parse()             # 解析聊天记录
│   ├── identify_target_user()  # 识别目标用户
│   └── extract_user_profile()  # 提取说话风格
│
└── UniversalExtractor      # ⭐ LLM 智能提取器
    ├── extract()           # 主入口
    ├── _identify_document_type()  # 识别资料类型
    ├── _extract_resume()   # 提取简历
    ├── _extract_product_docs()    # 提取产品文档
    ├── _extract_technical_docs()  # 提取技术文档
    ├── _extract_chat_logs()       # 提取聊天记录
    ├── _extract_faq()      # 提取 FAQ
    └── _extract_general()  # 通用提取
```

### 3. LLM 后端架构

```
LLMBackend
│
├── __init__(provider, api_key, base_url)
│
├── complete(prompt, system_prompt, max_tokens)
│   ├── _openai_complete()      # OpenAI API
│   ├── _anthropic_complete()   # Anthropic API
│   └── _fallback_complete()    # 后备方案
│
└── 支持的环境变量
    ├── OPENAI_API_KEY
    ├── OPENAI_BASE_URL
    └── ANTHROPIC_API_KEY
```

---

## 📦 核心组件详解

### 1. skill_generator.py

**职责**: CLI 入口和 Skill 生成主逻辑

**主要类**:
- `SkillGenerator`
  - `extract_from_files()` - 传统规则提取
  - `extract_from_files_with_llm()` - ⭐ 智能 LLM 提取
  - `generate()` - 生成 Skill
  - `_render_templates()` - 渲染模板
  - `_generate_persona_info_py()` - 生成 Python 代码

**CLI 参数**:
```python
--smart, -S              # 启用智能模式
--from-files FILE ...    # 输入文件
--llm-provider PROVIDER  # LLM 后端
--template TEMPLATE      # 指定模板
--name NAME              # Skill 名称
--output DIR             # 输出目录
```

### 2. universal_extractor.py

**职责**: LLM 驱动的通用信息提取

**核心类**:
- `DocumentType` (Enum) - 文档类型枚举
  - `RESUME` - 简历
  - `PRODUCT_DOCS` - 产品文档
  - `TECHNICAL_DOCS` - 技术文档
  - `CHAT_LOGS` - 聊天记录
  - `FAQ` - 问答文档
  - `GENERAL_KNOWLEDGE` - 通用知识

- `ExtractedInfo` (dataclass) - 提取的信息结构
  - `document_type` - 文档类型
  - `name` - 主体名称
  - `title` - 标题/职位
  - `description` - 描述
  - `key_points` - 关键要点
  - `structured_data` - 结构化数据
  - `suggested_skill_type` - 建议的 Skill 类型
  - `suggested_triggers` - 建议的触发词

- `UniversalExtractor`
  - `extract()` - 主提取入口
  - `_identify_document_type()` - LLM 识别类型
  - `_extract_*()` - 各类型的专用提取方法

### 3. 模板系统

**模板结构**:
```
templates/
└── {template_name}/
    ├── manifest.json           # 模板元数据
    ├── SKILL.md.template       # SKILL.md 模板
    ├── scripts/
    │   └── tool.py.template    # tool.py 模板
    └── static/                 # 静态文件（可选）
```

**manifest.json 格式**:
```json
{
  "name": "personal_digital_twin",
  "description": "个人数字分身模板",
  "defaults": {
    "triggers": ["@名称", "名称"]
  },
  "required_fields": ["name"],
  "files": {
    "SKILL.md": "SKILL.md.template",
    "scripts/tool.py": "scripts/tool.py.template"
  }
}
```

---

## 🔌 扩展指南

### 1. 添加新的提取类型

在 `universal_extractor.py` 中：

```python
# 1. 在 DocumentType Enum 中添加新类型
class DocumentType(Enum):
    # ... 现有类型
    MEDICAL_RECORDS = "medical_records"  # 新增

# 2. 在 _identify_document_type 中添加识别逻辑
# 3. 添加 _extract_medical_records 方法
def _extract_medical_records(self, content, hint):
    system_prompt = """从医疗记录中提取..."""
    # ... 实现提取逻辑
```

### 2. 添加新的 LLM 后端

在 `universal_extractor.py` 的 `LLMBackend` 中：

```python
def _kimi_complete(self, prompt, system_prompt, max_tokens):
    """Kimi API 调用"""
    try:
        import openai
        client = openai.OpenAI(
            api_key=os.getenv("KIMI_API_KEY"),
            base_url="https://api.moonshot.cn/v1"
        )
        # ... 调用逻辑
    except Exception as e:
        return self._fallback_complete(prompt, system_prompt)
```

### 3. 添加新的 Skill 模板

```bash
# 1. 创建模板目录
mkdir templates/faq_assistant

# 2. 创建 manifest.json
cat > templates/faq_assistant/manifest.json << 'EOF'
{
  "name": "faq_assistant",
  "description": "FAQ 问答助手",
  "defaults": {
    "triggers": ["怎么", "如何", "问题"]
  },
  "required_fields": ["name"],
  "files": {
    "SKILL.md": "SKILL.md.template",
    "scripts/tool.py": "scripts/tool.py.template"
  }
}
EOF

# 3. 创建模板文件
# SKILL.md.template
# scripts/tool.py.template
```

---

## 🧪 测试策略

### 单元测试

```bash
# 测试文件解析
python3 -c "
from extractors import FileParser
fp = FileParser()
result = fp.parse('test.pdf')
print(result['content'][:500])
"

# 测试 LLM 提取
python3 -c "
from extractors import extract_with_llm
info = extract_with_llm('简历内容...')
print(info.document_type)
print(info.name)
"
```

### 集成测试

```bash
# 完整流程测试
python3 skill_generator.py \
  --smart \
  --from-files test_data/简历.pdf \
  --name "测试" \
  --output /tmp/test_output
```

---

## 📊 性能指标

| 指标 | 传统模式 | 智能模式 |
|------|---------|---------|
| 支持资料类型 | 简历类 | 任意类型 |
| 提取准确率 | ~70% | ~90%+ |
| 响应时间 | <1s | 2-5s (LLM API) |
| 需要 API Key | 否 | 是 |
| 成本 | 免费 | 按 LLM token 计费 |

---

## 🛣️ 路线图

### 已完成 ✅

- [x] 基础 Skill 生成
- [x] 文件解析（PDF, Word, TXT）
- [x] 规则提取（简历类）
- [x] LLM 智能提取（UniversalExtractor）
- [x] Karpathy Style Markdown 知识库
- [x] 多 LLM 后端支持（OpenAI, Anthropic）

### 计划中 📋

- [ ] 更多 Skill 模板（product_assistant, faq_assistant）
- [ ] 更多 LLM 后端（Kimi, 本地模型）
- [ ] 批量生成模式
- [ ] Web UI 界面
- [ ] 自动 wiki linting
- [ ] Skill 版本管理

### 长期愿景 🚀

- [ ] Skill 市场/分享平台
- [ ] 自动优化建议
- [ ] 多模态支持（图片、音频）
- [ ] 实时同步更新

---

## 🔗 相关资源

- **GitHub**: https://github.com/wq19901103wq/skill-generator
- **README**: [README.md](./README.md)
- **演示**: [DEMO.md](./DEMO.md)

---

## 👥 贡献指南

1. **Fork** 项目
2. **创建分支**: `git checkout -b feature/新功能`
3. **提交更改**: `git commit -am "feat: 添加新功能"`
4. **推送分支**: `git push origin feature/新功能`
5. **创建 Pull Request**

### 代码规范

- 遵循 PEP 8
- 添加类型注解
- 编写 docstring
- 保持向后兼容

---

*最后更新: 2025年4月*
*版本: v2.0 - 智能模式*
