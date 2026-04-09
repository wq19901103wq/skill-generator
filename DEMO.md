# Smart Mode 演示

## 1. 环境准备

```bash
# 设置 OpenAI API 密钥
export OPENAI_API_KEY="sk-..."

# 或者设置 Anthropic API 密钥
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 2. 智能模式演示

### 2.1 从产品文档生成 Skill

```bash
# 创建产品文档
cat > /tmp/产品手册.txt << 'EOF'
智能温控器 Pro

产品简介
智能温控器 Pro 是一款专为现代家庭设计的智能温控设备...
[文档内容]
EOF

# 使用智能模式生成 Skill
python3 skill_generator.py \
  --smart \
  --from-files /tmp/产品手册.txt \
  --name "温控器助手"
```

**预期输出**：
```
🚀 启动智能模式：使用 LLM 分析资料类型...
  📄 产品手册.txt

🧠 LLM 正在智能分析资料类型...

📋 分析结果:
   资料类型: 产品文档
   主体名称: 智能温控器 Pro
   标题/职位: 智能家居设备
   建议 Skill 类型: product_assistant
   
   自动选择模板: product_assistant

✅ Skill 生成成功!
   路径: ./skills/温控器助手-assistant
```

### 2.2 从技术文档生成 Skill

```bash
python3 skill_generator.py \
  --smart \
  --from-files API文档.md 架构图.pdf \
  --name "API助手"
```

### 2.3 从 FAQ 生成 Skill

```bash
python3 skill_generator.py \
  --smart \
  --from-files 常见问题.xlsx \
  --name "客服助手"
```

## 3. 提取的信息结构

智能模式会提取以下结构化信息：

```json
{
  "name": "智能温控器 Pro",
  "title": "智能家居设备",
  "description": "一款专为现代家庭设计的智能温控设备...",
  "key_points": [
    "远程控制：通过手机APP随时随地控制家中温度",
    "语音控制：支持小爱同学、天猫精灵等主流语音助手",
    "定时任务：可设置多个时间段自动调节温度"
  ],
  "structured_data": {
    "产品概述": "...",
    "核心功能": "...",
    "使用场景": "...",
    "常见问题": "..."
  },
  "suggested_skill_type": "product_assistant",
  "suggested_triggers": ["温控器", "怎么", "用法", "问题"]
}
```

## 4. 支持的资料类型

| 资料类型 | 自动识别关键词 | 生成的 Skill | 适用场景 |
|---------|---------------|-------------|---------|
| 简历 | 姓名、职位、公司、教育 | 数字分身 | 个人助理 |
| 产品文档 | 产品、功能、使用场景 | 产品助手 | 客服、销售 |
| 技术文档 | API、接口、参数、代码 | 技术助手 | 开发文档 |
| 聊天记录 | 时间、昵称、对话 | 聊天机器人 | 社交 |
| FAQ | 问题、答案、Q&A | 问答助手 | 客服 |
| 论文/报告 | 摘要、结论、关键词 | 学术助手 | 研究 |

## 5. 对比：传统模式 vs 智能模式

### 传统模式（--from-files）
- ✅ 不需要 LLM API
- ❌ 只支持简历类资料
- ❌ 使用规则提取，不够智能
- ❌ 固定字段（教育、工作、技能）

### 智能模式（--smart）
- ✅ 支持任意资料类型
- ✅ LLM 智能识别和提取
- ✅ 自动选择模板类型
- ✅ 动态提取关键信息
- ⚠️ 需要 LLM API 密钥

## 6. 故障排除

### 问题：LLM 提取失败

```
❌ LLM 提取失败: 401 Unauthorized
   尝试使用规则提取...
```

**解决方案**：
1. 检查 API 密钥是否设置正确
2. 检查 API 密钥是否有余额
3. 检查网络连接

### 问题：识别类型不准确

**解决方案**：
使用 `--name` 提供提示

```bash
python3 skill_generator.py \
  --smart \
  --from-files 文档.pdf \
  --name "这是一个产品说明书"  # 帮助 LLM 理解
```

## 7. 自定义 LLM 后端

```bash
# 使用 OpenAI
python3 skill_generator.py --smart --llm-provider openai --from-files doc.pdf

# 使用 Anthropic Claude
python3 skill_generator.py --smart --llm-provider anthropic --from-files doc.pdf

# 使用本地 LLM（通过 OpenAI 兼容 API）
export OPENAI_BASE_URL="http://localhost:8000/v1"
python3 skill_generator.py --smart --from-files doc.pdf
```
