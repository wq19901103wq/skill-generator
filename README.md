# OpenClaw Skill Generator

通用的 OpenClaw Skill 生成器，支持多种模板，可以快速生成个性化的 Skill。

## 特性

- 🎯 **多模板支持**：个人数字分身、文件助手、FAQ 问答等
- 📝 **变量渲染**：使用占位符动态生成内容
- 🔒 **隐私保护**：敏感文件自动添加到 .gitignore
- 🚀 **一键生成**：命令行或配置文件驱动

## 安装

```bash
git clone https://github.com/wq19901103wq/skill-generator.git
cd skill-generator
```

## 用法

### 1. 列出可用模板

```bash
python3 skill_generator.py --list
```

### 2. 命令行方式生成

```bash
python3 skill_generator.py \
  --template personal_digital_twin \
  --name "王艺涵" \
  --output ./skills
```

### 3. 配置文件方式生成

创建 `config.json`：

```json
{
  "template": "personal_digital_twin",
  "name": "王艺涵",
  "skill_name": "wangyihan-digital-twin",
  "personality_desc": "热情随意",
  "triggers": ["@王艺涵", "王艺涵", "简历", "学历证明"]
}
```

然后运行：

```bash
python3 skill_generator.py --config config.json --output ./skills
```

## 模板说明

### personal_digital_twin（个人数字分身）

适用于创建个人数字分身，响应 @提及，发送简历/资料，查询日程等。

**必填字段**：
- `name`: 分身名称（如：王艺涵）

**可选字段**：
- `skill_name`: Skill 目录名
- `personality_desc`: 性格描述
- `triggers`: 触发词列表
- `particles`: 语气词列表
- `persona_info`: 个人信息字典

## 目录结构

```
skill-generator/
├── skill_generator.py      # 核心生成器代码
├── templates/              # 模板目录
│   └── personal_digital_twin/
│       ├── manifest.json   # 模板配置
│       ├── SKILL.md.template
│       └── scripts/
│           └── tool.py.template
├── examples/               # 生成的示例
│   └── wangyihan-digital-twin/
├── tests/                  # 测试代码
└── README.md
```

## 创建新模板

1. 在 `templates/` 下创建新目录
2. 创建 `manifest.json` 定义模板元数据
3. 创建 `.template` 文件作为模板
4. 使用 `{变量名}` 作为占位符

## 示例

生成王艺涵数字分身：

```bash
python3 skill_generator.py \
  --template personal_digital_twin \
  --name "王艺涵" \
  --skill-name "wangyihan-digital-twin" \
  --output ~/.openclaw/workspace/skills
```

输出：
```
✅ Skill 生成成功: ~/.openclaw/workspace/skills/wangyihan-digital-twin
```

## 许可证

MIT
