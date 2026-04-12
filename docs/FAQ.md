# 常见问题 (FAQ)

---

## 安装问题

### Q: 安装依赖失败怎么办？

```bash
pip install PyPDF2 python-docx
```

**A**: 如果安装失败，尝试：

```bash
# 使用国内镜像
pip install PyPDF2 python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或只安装需要的
pip install PyPDF2
```

---

## 生成问题

### Q: 提示 "缺少必填字段" 怎么办？

**A**: 某些模板需要特定字段。检查：

1. 是否提供了 `--name` 参数
2. 配置文件是否包含所有必需字段
3. 模板文档中的 `required_fields`

```bash
# 确保提供 name
python3 skill_generator.py --name "王艺涵" --from-files 简历.pdf
```

### Q: 智能模式 LLM 调用超时？

**A**: 

1. 检查网络连接
2. 检查 API 密钥是否正确
3. 使用非智能模式（传统提取）

```bash
# 不使用 --smart，使用传统规则提取
python3 skill_generator.py --from-files 简历.pdf --name "王艺涵"
```

### Q: 生成的 Skill 目录名不对？

**A**: 目录名根据 `name` 自动生成：

- 中文名 → 转换为拼音风格
- 英文名 → 小写 + 连字符

可以手动指定：

```json
{
  "skill_name": "wang-yihan-digital-twin"
}
```

---

## Wiki 知识库问题

### Q: 如何更新已生成的 Wiki？

**A**: 直接编辑 Markdown 文件：

```bash
# 编辑 Wiki 文件
open ~/.openclaw/skills/wang-yihan-digital-twin/data/wiki/基本介绍.md

# 修改后保存即可生效
```

### Q: 可以添加新的 Wiki 文件吗？

**A**: 可以！直接创建新的 `.md` 文件：

```bash
# 创建新文件
touch data/wiki/项目经验.md

# 编辑内容
# 然后在 tool.py 中添加读取逻辑
```

### Q: Wiki 文件乱码怎么办？

**A**: 确保保存为 UTF-8 编码：

```bash
# 使用 VS Code，右下角选择 UTF-8
# 或使用命令行转换
iconv -f GBK -t UTF-8 文件.md > 文件_utf8.md
```

---

## OpenClaw 集成问题

### Q: Skill 部署后没有生效？

**A**: 

1. 检查 Skill 目录是否在正确位置：
   ```bash
   ls ~/.local/node/lib/node_modules/openclaw/skills/
   ```

2. 重启 OpenClaw 服务：
   ```bash
   oc restart
   # 或
   kill $(lsof -ti:18789); sleep 2; openclaw gateway &
   ```

3. 检查 SKILL.md 语法是否正确

### Q: 触发词不生效？

**A**: 

1. 检查 `SKILL.md` 中的 `triggers` 列表
2. 确认触发词没有特殊字符
3. 尝试更简单的触发词

```yaml
# SKILL.md
---
triggers:
  - "@王艺涵"    # 推荐带 @ 符号
  - "王艺涵"      # 纯名字
  - "产品经理"    # 职位也可以
```

### Q: tool.py 返回错误？

**A**: 测试 tool.py：

```bash
cd ~/.openclaw/skills/wang-yihan-digital-twin
python3 scripts/tool.py query_memory "测试"
```

如果报错，检查：
- Python 版本（需要 3.8+）
- 文件路径是否正确
- data/wiki/ 目录是否存在

---

## 模板开发问题

### Q: 如何创建新模板？

**A**: 参考 [模板开发指南](./TEMPLATE_GUIDE.md)

快速步骤：
1. 创建 `templates/my_template/` 目录
2. 创建 `manifest.json`
3. 创建 `SKILL.md.template`
4. 测试生成

### Q: 模板变量不渲染？

**A**: 检查：

1. 变量名是否匹配（区分大小写）
2. manifest.json 中是否定义了默认值
3. 模板语法是否正确：`{变量名}`

```json
// manifest.json
{
  "defaults": {
    "my_var": "默认值"
  }
}
```

```markdown
<!-- SKILL.md.template -->
{my_var}  <!-- 正确 -->
{My_Var}  <!-- 错误：大小写不匹配 -->
```

---

## 性能问题

### Q: 大 PDF 解析很慢？

**A**: 

1. 提取前几页即可
2. 转换为文本格式
3. 使用 `--smart` 模式，LLM 会自动提取关键信息

### Q: 如何批量生成多个 Skill？

**A**: 使用脚本批量处理：

```bash
#!/bin/bash
for file in ./resumes/*.pdf; do
    name=$(basename "$file" .pdf)
    python3 skill_generator.py \
        --from-files "$file" \
        --name "$name" \
        --output ./skills
done
```

---

## 其他问题

### Q: 如何备份生成的 Skill？

**A**: 

```bash
# 打包备份
tar -czf skills-backup-$(date +%Y%m%d).tar.gz ~/.openclaw/skills/

# 或同步到 Git
cd ~/.openclaw/skills
git init
git add .
git commit -m "backup"
```

### Q: 可以在 Windows 上使用吗？

**A**: 可以，但需要：

1. 安装 Python 3.8+
2. 使用 PowerShell 或 Git Bash
3. 路径使用反斜杠或原始字符串

```powershell
python skill_generator.py --from-files "简历.pdf" --name "王艺涵"
```

### Q: 如何贡献代码？

**A**: 

1. Fork 项目
2. 创建分支：`git checkout -b feature/xxx`
3. 提交 PR

---

## 获取帮助

如果以上无法解决你的问题：

1. 查看 [API 文档](./API.md)
2. 查看 [模板开发指南](./TEMPLATE_GUIDE.md)
3. 在 GitHub 提交 Issue

---

*文档版本: v3.0*
