# 踩坑记录 (Lessons Learned)

> 记录开发过程中踩过的坑，避免重复踩坑。
>
> 规则：每踩一个新坑，24 小时内必须补充到此文档。

---

## 一、LLM 提取相关

### 1. LLM 返回的 JSON 格式不稳定

**现象**: LLM 有时在 JSON 外面包了一层 markdown 代码块（```json ... ```），有时在 JSON 后面加了额外解释文字，导致 `json.loads()` 失败。

**根因**: Prompt 中虽然要求"返回 JSON"，但 LLM 不总是严格遵守。

**解决方案**:
- 实现了 `_parse_json_fuzzy()` 方法，用正则提取 JSON 块
- 添加了多轮 fallback：先尝试直接解析 → 尝试提取代码块 → 尝试提取第一个 `{...}` → 返回空 dict

**代码位置**: `extractors/universal_extractor.py` `_parse_json_fuzzy()`

---

### 2. LLM 识别文档类型时的歧义

**现象**: 一份同时包含产品介绍和 API 说明的文档，LLM 有时识别为 `product_docs`，有时识别为 `technical_docs`。

**根因**: 文档本身跨类型，prompt 中的类型描述有重叠。

**解决方案**:
- 在 prompt 中明确要求 LLM "选择最匹配的一个类型"
- 添加 `hint` 参数，让用户可以提供类型提示

**代码位置**: `extractors/universal_extractor.py` `_identify_document_type()`

---

### 3. LLM API 超时导致整个生成流程中断

**现象**: 网络不稳定时，`complete()` 抛出异常，整个 `generate()` 流程中断，没有生成任何文件。

**根因**: 没有异常隔离，LLM 调用失败直接导致主流程崩溃。

**解决方案**:
- `LLMBackend.complete()` 中捕获异常，返回 fallback 内容
- `UniversalExtractor.extract()` 中如果 LLM 失败，回退到通用提取模式

**代码位置**: `extractors/universal_extractor.py` `complete()`, `extract()`

---

## 二、模板渲染相关

### 4. 模板变量大小写不匹配导致渲染为空

**现象**: 模板中写了 `{Name}`，但 config 中只有 `name`（小写），渲染后为空。

**根因**: Python 的字符串替换是区分大小写的。

**解决方案**:
- 在文档中强调变量名区分大小写
- `_prepare_render_vars()` 中统一使用小写 key

**代码位置**: `skill_generator.py` `_prepare_render_vars()`

---

### 5. 模板中的大括号与 Python f-string 冲突

**现象**: 模板文件中有 `{variable}`，但 `skill_generator.py` 中也用了 f-string，导致变量被提前解析。

**根因**: Python f-string 和模板变量都使用 `{}` 语法。

**解决方案**:
- 模板文件中使用双大括号 `{{}}` 来转义（jinja2 风格），或使用 `_render_string()` 自定义替换逻辑
- 目前使用自定义的 `_render_string()`，直接字符串替换，不走 f-string

**代码位置**: `skill_generator.py` `_render_string()`

---

## 三、文件解析相关

### 6. PDF 解析中文乱码

**现象**: 某些 PDF 文件解析出来的中文是乱码。

**根因**: PDF 编码问题，PyPDF2 对某些中文字体支持不好。

**解决方案**:
- 尝试多个 PDF 解析库（PyPDF2, pdfplumber）
- 如果解析失败，提示用户转换为文本格式

**代码位置**: `extractors/file_parser.py` `_parse_pdf()`

---

### 7. 大文件导致内存占用过高

**现象**: 解析 100MB+ 的 PDF 时，程序内存占用飙升。

**根因**: `FileParser` 一次性读取整个文件内容到内存。

**解决方案**:
- 添加文件大小限制（>50MB 的文件跳过或截断）
- 对于文本文件，只读取前 N 行/字符

**代码位置**: `extractors/file_parser.py` `parse()`

---

## 四、OpenClaw 集成相关

### 8. 生成的 Skill 目录名含特殊字符导致 OpenClaw 无法加载

**现象**: 用户输入的名字包含 emoji 或特殊符号，生成的目录名 OpenClaw 识别不了。

**根因**: `_name_to_pinyin_slug()` 没有处理所有特殊字符。

**解决方案**:
- 增加字符过滤，只保留字母、数字、连字符、下划线
- 中文字符转拼音

**代码位置**: `skill_generator.py` `_name_to_pinyin_slug()`

---

### 9. 生成的 tool.py 路径硬编码

**现象**: 模板中硬编码了 `data/wiki/基本介绍.md`，但如果用户修改了 `name`，路径就对不上了。

**根因**: 早期版本模板中使用了固定路径。

**解决方案**:
- 所有路径使用相对路径或模板变量
- `tool.py.template` 中通过 `__file__` 获取脚本所在目录，再拼接相对路径

**代码位置**: `templates/personal_digital_twin/scripts/tool.py.template`

---

## 五、待补充

> 以下坑位预留，后续踩到后补充。

### [待补充] 新坑记录模板

**现象**:

**根因**:

**解决方案**:

**代码位置**:

---

*最后更新: 2026-04-21*
