# Karpathy Style Wiki 使用指南

> 如何手动编辑和维护 Skill 的 Markdown 知识库

---

## 什么是 Karpathy Style Wiki

Karpathy Style 指的是 **Andrej Karpathy** 倡导的一种知识管理方式：

> 使用纯 Markdown 文件作为知识库，而不是数据库或向量存储。

### 核心特点

1. **人可读** - 直接用文本编辑器打开就能读
2. **人可编辑** - 不需要专业工具，任何 Markdown 编辑器都可以
3. **无需 RAG** - AI 直接读取文件，不需要向量化检索
4. **版本控制友好** - Git 可以完美追踪变更

---

## Wiki 目录结构

```
data/
├── wiki/              # Karpathy Style 知识库 ⭐
│   ├── _index.md      # 索引文件
│   ├── 基本介绍.md     # 基本信息
│   ├── 工作经验.md     # 工作经历
│   ├── 教育背景.md     # 教育经历
│   ├── 专业技能.md     # 技能
│   ├── 性格特点.md     # 性格
│   ├── 兴趣爱好.md     # 兴趣
│   └── 联系方式.md     # 联系方式
├── documents/         # 原始文件
└── memory/            # 对话历史
```

---

## 文件格式规范

### 1. _index.md（索引文件）

每个 Wiki 都应该有一个索引文件：

```markdown
# 王艺涵 - 知识库索引

这是一个 Karpathy Style 知识库。

## 文件结构

- [基本介绍](./基本介绍.md)
- [工作经验](./工作经验.md)
- [教育背景](./教育背景.md)

## 使用方式

AI 助手直接读取这些 Markdown 文件。
```

### 2. 内容文件

使用标准 Markdown 格式：

```markdown
# 基本介绍

## 王艺涵

**职位**: 推荐产品经理  
**公司**: 阿里巴巴

## 简介

我是王艺涵，一名产品经理...

## 核心能力

- 搜索推荐策略
- AI/大模型应用
- 增长策略
```

---

## 手动编辑 Wiki

### 编辑工具

任何支持 Markdown 的编辑器都可以：

- **VS Code** - 推荐，有 Markdown 预览
- **Typora** - 所见即所得
- **Obsidian** - 知识库管理
- **记事本** - 最简单

### 编辑示例

假设你要更新王艺涵的工作经验：

1. 打开文件：
   ```bash
   open ~/.openclaw/skills/wang-yihan-digital-twin/data/wiki/工作经验.md
   ```

2. 编辑内容：
   ```markdown
   ## 新的工作经历

   **公司**: 新公司
   **时间**: 2025.01 - 至今

   ### 主要职责

   - 负责 xxx 产品
   - 达成 xxx 业绩
   ```

3. 保存即可生效

---

## AI 如何读取 Wiki

### tool.py 中的读取方式

```python
def get_wiki_file(filename):
    """读取单个 Wiki 文件"""
    wiki_dir = os.path.join(get_skill_dir(), 'data', 'wiki')
    file_path = os.path.join(wiki_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def search_wiki(query):
    """搜索 Wiki 内容"""
    # 1. 获取所有 Wiki 文件
    wiki_files = get_all_wiki_files()
    
    # 2. 根据关键词匹配文件
    for filename, content in wiki_files.items():
        if match(query, filename):
            return content
    
    # 3. 返回匹配的内容
    return best_match_content
```

### 匹配逻辑

| 用户查询 | 匹配文件 |
|---------|---------|
| "你是谁" | 基本介绍.md |
| "工作经验" | 工作经验.md |
| "学历" | 教育背景.md |
| "技能" | 专业技能.md |
| "联系方式" | 联系方式.md |

---

## Wiki 最佳实践

### 1. 文件命名

- 使用中文名称，易读易记
- 避免特殊字符和空格
- 统一使用 `.md` 扩展名

✅ 推荐：`工作经验.md`、`教育背景.md`
❌ 避免：`work exp.md`、`教育 背景.md`

### 2. 内容组织

- 使用 `#` 作为一级标题（文件名对应的内容）
- 使用 `##` 作为二级标题（分类）
- 使用 `###` 作为三级标题（具体条目）

```markdown
# 工作经验          <- 一级：文件主题

## 阿里巴巴         <- 二级：公司

### 主要职责       <- 三级：具体内容
...
```

### 3. 内容更新

定期更新 Wiki 内容：

| 更新时机 | 更新内容 |
|---------|---------|
| 换工作 | 工作经验.md |
| 学新技能 | 专业技能.md |
| 联系方式变更 | 联系方式.md |
| 获得奖项 | 基本介绍.md |

---

## 从 Wiki 生成其他格式

### 导出为 PDF

```bash
# 使用 pandoc
pandoc data/wiki/_index.md data/wiki/*.md -o 王艺涵介绍.pdf
```

### 导出为 HTML

```bash
# 使用 markdown 工具
markdown data/wiki/基本介绍.md > 基本介绍.html
```

---

## 多个 Wiki 管理

如果你有多个 Skill：

```
skills/
├── wang-yihan-digital-twin/
│   └── data/wiki/       # 王艺涵的知识库
├── zhang-san-digital-twin/
│   └── data/wiki/       # 张三的知识库
└── my-company-assistant/
    └── data/wiki/       # 公司助手的知识库
```

每个 Wiki 完全独立，互不影响。

---

## 故障排查

### 问题1：AI 说找不到信息

**检查**:
- Wiki 文件是否存在
- 文件名是否正确
- 文件内容是否为空

### 问题2：内容更新后 AI 还是旧回复

**解决**:
- OpenClaw 可能有缓存，重启服务
- 检查是否编辑了正确的文件

### 问题3：中文乱码

**解决**:
- 确保文件保存为 UTF-8 编码
- 不要用 Windows 记事本编辑

---

*文档版本: v3.0*
