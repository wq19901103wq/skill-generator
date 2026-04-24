# Skill Generator 测试套件

> 测试覆盖说明和运行指南

---

## 运行测试

### 安装依赖

```bash
pip install pytest pytest-cov
```

### 运行全部测试

```bash
cd ~/.openclaw/workspace/skill-generator
python -m pytest tests/ -v
```

### 运行指定测试文件

```bash
# 只测提取器
python -m pytest tests/test_extractors.py -v

# 只测主生成器
python -m pytest tests/test_skill_generator.py -v
```

### 生成覆盖率报告

```bash
python -m pytest tests/ --cov=extractors --cov=skill_generator --cov-report=html
# 报告在 htmlcov/index.html
```

---

## 测试数据

测试数据放在 `tests/fixtures/` 目录下：

```
fixtures/
├── sample_resume.pdf      # 测试简历 PDF
├── sample_resume.docx     # 测试简历 Word
├── sample_chat.txt        # 测试聊天记录
├── sample_product.md      # 测试产品文档
└── sample_tech_doc.md     # 测试技术文档
```

> ⚠️ 注意：不要提交包含真实个人信息的测试文件到 GitHub。

---

## 测试分类

| 测试文件 | 覆盖范围 |
|---------|---------|
| `test_extractors.py` | FileParser, PersonaExtractor, UniversalExtractor |
| `test_skill_generator.py` | SkillGenerator 主流程 |
| `test_templates.py` | 模板渲染 |

---

*最后更新: 2026-04-21*
