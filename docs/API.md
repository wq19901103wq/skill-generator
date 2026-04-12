# Skill Generator API 文档

> 编程接口参考，用于集成和二次开发

---

## 核心类

### `SkillGenerator`

主生成器类，用于生成 Skill。

```python
from skill_generator import SkillGenerator

gen = SkillGenerator(template_dir="./templates")
```

#### 方法

##### `list_templates() -> List[str]`

列出所有可用模板。

```python
templates = gen.list_templates()
print(templates)  # ['personal_digital_twin']
```

##### `load_template(template_name: str) -> Dict`

加载指定模板的配置。

```python
template = gen.load_template("personal_digital_twin")
print(template['name'])  # personal_digital_twin
print(template['required_fields'])  # ['name']
```

##### `extract_from_files(file_paths: List[str], name_hint: str = None) -> Dict`

从文件中提取信息（传统规则模式）。

```python
config = gen.extract_from_files(
    ["简历.pdf", "聊天记录.txt"],
    name_hint="王艺涵"
)
print(config['name'])  # 王艺涵
print(config['title'])  # 产品经理
```

##### `extract_from_files_with_llm(file_paths: List[str], hint: str = None, llm_provider: str = "openai") -> Dict`

使用 LLM 智能提取（智能模式）。

```python
config = gen.extract_from_files_with_llm(
    ["产品手册.pdf"],
    hint="产品助手",
    llm_provider="openai"
)
print(config['document_type'])  # product_docs
```

##### `generate(template_name: str, config: Dict, output_dir: str = None) -> str`

生成 Skill 并返回路径。

```python
skill_path = gen.generate(
    template_name="personal_digital_twin",
    config={"name": "王艺涵", "title": "产品经理"},
    output_dir="./skills"
)
print(skill_path)  # ./skills/wang-yihan-digital-twin
```

---

### `UniversalExtractor`

LLM 驱动的通用信息提取器。

```python
from extractors import UniversalExtractor, LLMBackend

llm = LLMBackend(provider="openai")
extractor = UniversalExtractor(llm_backend=llm)

info = extractor.extract(content, hint="产品经理")
print(info.name)  # 王艺涵
print(info.document_type)  # DocumentType.RESUME
```

---

### `FileParser`

多格式文件解析器。

```python
from extractors import FileParser

parser = FileParser()
result = parser.parse("简历.pdf")
print(result['content'][:500])
```

---

## CLI 接口

### 命令行参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--smart` | `-S` | 启用智能模式 | `--smart` |
| `--from-files` | | 输入文件 | `--from-files 简历.pdf` |
| `--template` | `-t` | 指定模板 | `--template personal_digital_twin` |
| `--name` | `-n` | Skill 名称 | `--name "王艺涵"` |
| `--output` | `-o` | 输出目录 | `--output ./skills` |
| `--config` | `-c` | 配置文件 | `--config config.json` |
| `--llm-provider` | | LLM 后端 | `--llm-provider openai` |
| `--list` | `-l` | 列出模板 | `--list` |

---

*文档版本: v3.0*
