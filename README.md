# OpenClaw Skill Generator

通用的 OpenClaw Skill 生成器，支持多种模板，可以快速生成个性化的 Skill。

**🌟 新特性：智能文件提取** — 自动从简历、聊天记录等文件中提取个人信息，无需手动配置！

## 特性

- 🎯 **多模板支持**：个人数字分身、文件助手、FAQ 问答等
- 📄 **智能文件提取**：从 PDF/Word/TXT/聊天记录自动提取个人信息 ⭐
- 💬 **说话风格学习**：分析聊天记录，学习用户的说话方式 ⭐
- 📝 **变量渲染**：使用占位符动态生成内容
- 🔒 **隐私保护**：敏感文件自动添加到 .gitignore
- 🚀 **一键生成**：命令行或配置文件驱动

## 安装

```bash
git clone https://github.com/wq19901103wq/skill-generator.git
cd skill-generator

# 安装可选依赖（用于PDF/Word解析）
pip install PyPDF2 python-docx
```

## 用法

### 🌟 推荐：从文件自动提取（全新功能！）

只需提供简历或聊天记录，自动生成数字分身：

```bash
# 从简历生成
python3 skill_generator.py --from-files 简历.pdf --name "王艺涵"

# 从多个文件生成（简历 + 聊天记录）
python3 skill_generator.py \
  --from-files 简历.docx 微信聊天记录.txt \
  --name "王艺涵" \
  --output ./skills

# 从聊天记录学习说话风格
python3 skill_generator.py \
  --from-files 简历.pdf \
  --chat-files 聊天记录.txt \
  --name "王艺涵"
```

**支持的文件格式**:
- 📄 PDF (简历)
- 📝 Word (.docx)
- 📃 文本 (.txt, .md)
- 📊 CSV (聊天记录导出)
- 💬 聊天记录 (微信/飞书/QQ 导出)

### 传统方式：手动配置

#### 命令行方式

```bash
python3 skill_generator.py \
  --template personal_digital_twin \
  --name "王艺涵" \
  --output ./skills
```

#### 配置文件方式

创建 `config.json`：

```json
{
  "template": "personal_digital_twin",
  "name": "王艺涵",
  "skill_name": "wangyihan-digital-twin",
  "title": "产品经理",
  "company": "某科技公司",
  "basic_intro": "我是王艺涵，产品经理，5年经验",
  "triggers": ["@王艺涵", "王艺涵", "简历"]
}
```

然后运行：

```bash
python3 skill_generator.py --config config.json --output ./skills
```

## 自动提取的信息

从文件中可以自动提取：

| 字段 | 来源 | 说明 |
|------|------|------|
| 姓名 | 简历/聊天记录 | 从文件开头或聊天记录昵称识别 |
| 职位 | 简历 | 产品经理、工程师等 |
| 公司 | 简历 | 当前就职公司 |
| 教育背景 | 简历 | 学校、专业、学历 |
| 工作经验 | 简历 | 工作经历摘要 |
| 技能 | 简历 | 专业技能列表 |
| 联系方式 | 简历 | 邮箱、手机、微信 |
| 说话风格 | 聊天记录 | 语气词、常用语、回复长度 |

## 模板说明

### personal_digital_twin（个人数字分身）

适用于创建个人数字分身，响应 @提及，发送简历/资料，查询日程等。

**必填字段**（使用 `--from-files` 时自动提取）：
- `name`: 分身名称

**可选字段**：
- `skill_name`: Skill 目录名
- `title`: 职位
- `company`: 公司
- `basic_intro`: 基本介绍
- `work_experience`: 工作经验
- `education`: 教育背景
- `skills`: 技能
- `contact`: 联系方式
- `triggers`: 触发词列表
- `tone_style`: 说话风格描述

## 目录结构

```
skill-generator/
├── skill_generator.py           # 核心生成器代码
├── extractors/                  # 文件提取模块 ⭐
│   ├── __init__.py
│   ├── file_parser.py           # 多格式文件解析
│   ├── persona_extractor.py     # 个人信息提取
│   └── chat_parser.py           # 聊天记录分析
├── templates/                   # 模板目录
│   └── personal_digital_twin/
│       ├── manifest.json
│       ├── SKILL.md.template
│       └── scripts/
│           └── tool.py.template
├── examples/                    # 示例配置
└── README.md
```

## 完整示例

### 场景1：从简历生成

假设你有一个 `王艺涵_简历.pdf`：

```bash
python3 skill_generator.py \
  --from-files "王艺涵_简历.pdf" \
  --name "王艺涵" \
  --output ~/.openclaw/workspace/skills
```

输出：
```
🔍 正在分析文件...
  📄 王艺涵_简历.pdf

🧠 正在提取个人信息...
  👤 识别到姓名: 王艺涵
  💼 识别到职位: 产品经理
  🏢 识别到公司: 某科技公司
  🎓 识别到教育: 某某大学 计算机科学 本科

✅ 提取完成！
   姓名: 王艺涵
   职位: 产品经理
   公司: 某科技公司
   教育: 某某大学...

✅ Skill 生成成功!
   路径: ~/.openclaw/workspace/skills/wangyihan-digital-twin
```

### 场景2：从聊天记录学习说话风格

```bash
python3 skill_generator.py \
  --from-files 简历.pdf \
  --chat-files 微信聊天记录.txt \
  --name "王艺涵"
```

生成的数字分身会：
- 使用同样的语气词（如"呢"、"呀"、"啦"）
- 模仿回复长度（简洁或详细）
- 使用类似的表情符号

## 混合配置

文件提取 + 手动覆盖：

```bash
# 1. 先从文件提取
python3 skill_generator.py \
  --from-files 简历.pdf \
  --config override.json \
  --name "王艺涵"
```

`override.json`：
```json
{
  "personality": "比较外向，喜欢直接沟通",
  "interests": "摄影、旅行、美食"
}
```

## 创建新模板

1. 在 `templates/` 下创建新目录
2. 创建 `manifest.json` 定义模板元数据
3. 创建 `.template` 文件作为模板
4. 使用 `{变量名}` 作为占位符

## 许可证

MIT
