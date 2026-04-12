# 模板开发指南

> 如何创建自定义 Skill 模板

---

## 快速开始

创建一个最简单的模板只需要 3 个文件：

```
templates/my_template/
├── manifest.json          # 模板配置
├── SKILL.md.template      # Skill 定义文件
└── scripts/
    └── tool.py.template   # 工具脚本（可选）
```

---

## 1. manifest.json

模板的核心配置文件。

```json
{
  "name": "my_template",
  "description": "我的自定义模板",
  "version": "1.0.0",
  "author": "你的名字",
  "defaults": {
    "triggers": ["@{name}", "{name}"],
    "greeting": "你好，我是{name}"
  },
  "required_fields": ["name"],
  "directories": [
    "data/wiki"
  ],
  "files": {
    "SKILL.md": "SKILL.md.template",
    "scripts/tool.py": "scripts/tool.py.template"
  },
  "static_files": {}
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 模板唯一标识 |
| `description` | string | 模板描述 |
| `version` | string | 版本号 |
| `author` | string | 作者 |
| `defaults` | object | 默认配置值 |
| `required_fields` | array | 必填字段列表 |
| `directories` | array | 需要创建的目录 |
| `files` | object | 模板文件映射（目标路径: 模板文件） |
| `static_files` | object | 静态文件复制映射 |

---

## 2. SKILL.md.template

Skill 的核心定义文件，使用 `{变量名}` 作为占位符。

```markdown
---
name: {skill_name}
description: |
  {name}的 Skill。当用户@{name}时，调用 scripts/tool.py。
triggers:
{triggers_yaml}
requires:
  - python3
---

# {name}

## 简介

{name}是一个{title}。

## 使用方法

- 触发词: {triggers_str}

## 知识库

- [基本介绍](./data/wiki/基本介绍.md)
```

### 内置变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `{name}` | 主体名称 | 王艺涵 |
| `{skill_name}` | Skill 目录名 | wang-yihan-digital-twin |
| `{skill_name_underscore}` | 下划线版本 | wang_yihan_digital_twin |
| `{title}` | 职位/标题 | 产品经理 |
| `{created_at}` | 创建日期 | 2026-04-12 |
| `{triggers_yaml}` | 触发词 YAML 格式 | - "@王艺涵"\n- "王艺涵" |

### 自定义变量

在 `manifest.json` 的 `defaults` 中定义：

```json
{
  "defaults": {
    "greeting": "你好",
    "particles": ["呀", "呢", "啦"]
  }
}
```

模板中使用：

```markdown
{greeting}，我是{name}～{particles_str}
```

---

## 3. tool.py.template

工具脚本模板（可选）。

```python
#!/usr/bin/env python3
"""
{name} - Tool 脚本
"""

import json

# Tool 定义
TOOL_DEFINITION = {{
    "name": "{skill_name_underscore}",
    "description": "{name}的工具",
    "parameters": {{
        "type": "object",
        "properties": {{
            "action": {{
                "type": "string",
                "enum": ["query", "greet"]
            }}
        }}
    }}
}}

def query(q: str):
    """查询信息"""
    # 从 data/wiki/ 读取知识库
    with open("data/wiki/基本介绍.md", "r") as f:
        content = f.read()
    
    return {{
        "reply_text": f"根据资料: {{content[:200]}}..."
    }}

def greet():
    """打招呼"""
    return {{
        "reply_text": "{greeting}，我是{name}！"
    }}

if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "greet"
    
    if action == "query":
        result = query(sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        result = greet()
    
    print(json.dumps(result, ensure_ascii=False))
```

---

## Karpathy Style Wiki

推荐在模板中使用 Markdown 知识库：

```
data/wiki/
├── _index.md          # 索引文件
├── 基本介绍.md         # 基本信息
└── ...
```

### 生成 Wiki 的方法

在 `skill_generator.py` 中实现 `_generate_wiki_files()` 方法，根据提取的信息自动生成 Markdown 文件。

---

## 完整示例

### FAQ 助手模板

```
templates/faq_assistant/
├── manifest.json
├── SKILL.md.template
└── data/
    └── faq.md.template
```

**manifest.json**:

```json
{
  "name": "faq_assistant",
  "description": "FAQ 问答助手",
  "defaults": {
    "triggers": ["怎么", "如何", "问题", "{name}"],
    "faq_items": []
  },
  "required_fields": ["name"],
  "files": {
    "SKILL.md": "SKILL.md.template",
    "data/faq.md": "data/faq.md.template"
  }
}
```

**SKILL.md.template**:

```markdown
---
name: {skill_name}
description: |
  {name} FAQ 助手。回答关于{name}的常见问题。
triggers:
{triggers_yaml}
---

# {name} FAQ 助手

## 常见问题

参考 data/faq.md 获取完整 FAQ 列表。
```

---

## 测试模板

```bash
# 使用模板生成测试
python3 skill_generator.py \
  --template my_template \
  --name "测试" \
  --output /tmp/test

# 检查输出
cat /tmp/test/my-skill/SKILL.md
```

---

## 发布模板

1. 在 GitHub 创建模板仓库
2. 提交模板文件
3. 在 README 中添加使用说明

```bash
git init
git add .
git commit -m "feat: 添加 my_template 模板"
git push origin main
```

---

*文档版本: v3.0*
