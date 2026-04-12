#!/usr/bin/env python3
"""
OpenClaw Skill Generator
通用 Skill 生成器 - 支持多种 Skill 模板
支持从文件自动提取个人信息（简历、聊天记录等）

用法:
    # 方式1: 基础生成（需要手动配置）
    python3 skill_generator.py --template personal_digital_twin --name "张三" --output ./skills
    
    # 方式2: 从文件自动提取（推荐）⭐
    python3 skill_generator.py --from-files 简历.pdf 聊天记录.txt --name "张三" --output ./skills
    
    # 方式3: 使用配置文件
    python3 skill_generator.py --config config.json
    
    # 方式4: 混合方式（文件提取 + 手动覆盖）
    python3 skill_generator.py --from-files 简历.pdf --config override.json
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 导入提取器
from extractors import (
    FileParser, PersonaExtractor, ChatParser,
    UniversalExtractor, LLMBackend, extract_with_llm
)


class SkillGenerator:
    """OpenClaw Skill 生成器"""
    
    def __init__(self, template_dir: str = None):
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / "templates"
        self.output_dir = Path(".")
        
    def list_templates(self) -> List[str]:
        """列出可用模板"""
        templates = []
        if self.template_dir.exists():
            for item in self.template_dir.iterdir():
                if item.is_dir() and (item / "manifest.json").exists():
                    templates.append(item.name)
        return templates
    
    def load_template(self, template_name: str) -> Dict[str, Any]:
        """加载模板配置"""
        template_path = self.template_dir / template_name
        manifest_path = template_path / "manifest.json"
        
        if not manifest_path.exists():
            raise ValueError(f"模板 '{template_name}' 不存在或缺少 manifest.json")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        manifest['_template_path'] = str(template_path)
        return manifest
    
    def extract_from_files(self, file_paths: List[str], name_hint: str = None) -> Dict[str, Any]:
        """
        从文件中提取个人信息
        
        Args:
            file_paths: 文件路径列表（简历、聊天记录等）
            name_hint: 姓名提示
        
        Returns:
            提取的配置字典
        """
        print("🔍 正在分析文件...")
        
        file_parser = FileParser()
        persona_extractor = PersonaExtractor()
        
        # 解析所有文件
        file_contents = {}
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                print(f"  ⚠️ 文件不存在: {file_path}")
                continue
            
            print(f"  📄 {path.name}")
            
            try:
                result = file_parser.parse(path)
                file_contents[path.name] = result['content']
            except Exception as e:
                print(f"  ❌ 解析失败: {e}")
        
        if not file_contents:
            raise ValueError("没有成功解析任何文件")
        
        print(f"\n🧠 正在提取个人信息...")
        
        # 提取个人信息
        persona = persona_extractor.extract_from_multiple(file_contents)
        
        # 处理聊天记录（如果有）
        chat_profile = None
        for filename, content in file_contents.items():
            if 'chat' in filename.lower() or '聊天' in filename or '对话' in filename:
                print(f"  💬 检测到聊天记录: {filename}")
                chat_parser = ChatParser()
                chat_parser.parse(content)
                
                # 识别目标用户
                target = chat_parser.identify_target_user(hint=name_hint)
                if target:
                    print(f"  👤 识别到用户: {target}")
                    chat_profile = chat_parser.extract_user_profile(target)
                break
        
        # 构建配置
        config = {
            'name': persona_extractor.persona.name or name_hint or "用户",
            'title': persona_extractor.persona.title or "",
            'company': persona_extractor.persona.company or "",
            'basic_intro': persona_extractor.persona.basic_intro or "",
            'work_experience': persona_extractor.persona.work_experience or "",
            'education': persona_extractor.persona.education or "",
            'skills': persona_extractor.persona.skills or "",
            'personality': persona_extractor.persona.personality or "",
            'interests': persona_extractor.persona.interests or "",
            'contact': persona_extractor.persona.contact or "",
        }
        
        # 添加聊天分析结果
        if chat_profile:
            config['chat_profile'] = chat_profile
            config['tone_style'] = chat_profile.get('reply_style', '说话自然')
            config['common_phrases'] = chat_profile.get('common_phrases', [])
        
        print(f"\n✅ 提取完成！")
        print(f"   姓名: {config['name']}")
        print(f"   职位: {config['title'] or '未识别'}")
        print(f"   公司: {config['company'] or '未识别'}")
        print(f"   教育: {config['education'][:30] + '...' if len(config['education']) > 30 else config['education'] or '未识别'}")
        
        return config
    
    def extract_from_files_with_llm(
        self, 
        file_paths: List[str], 
        hint: str = None,
        llm_provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        使用 LLM 从文件中智能提取信息（支持任意资料类型）
        
        Args:
            file_paths: 文件路径列表（任意类型资料）
            hint: 用户提示，帮助 LLM 理解资料类型
            llm_provider: LLM 提供商 (openai, anthropic)
        
        Returns:
            提取的配置字典
        """
        print("🔍 正在使用 LLM 分析文件...")
        
        # 检查 LLM 配置
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
            print("⚠️ 警告: 未配置 LLM API 密钥")
            print("   请设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY")
            print("   将使用规则提取作为后备方案...")
            return self.extract_from_files(file_paths, hint)
        
        file_parser = FileParser()
        
        # 解析所有文件
        all_content = []
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                print(f"  ⚠️ 文件不存在: {file_path}")
                continue
            
            print(f"  📄 {path.name}")
            
            try:
                result = file_parser.parse(path)
                all_content.append(f"## {path.name}\n{result['content']}")
            except Exception as e:
                print(f"  ❌ 解析失败: {e}")
        
        if not all_content:
            raise ValueError("没有成功解析任何文件")
        
        # 合并内容
        combined_content = "\n\n".join(all_content)
        
        print(f"\n🧠 LLM 正在智能分析资料类型...")
        
        # 使用 LLM 提取
        llm = LLMBackend(provider=llm_provider)
        extractor = UniversalExtractor(llm_backend=llm)
        extracted = extractor.extract(combined_content, hint)
        
        print(f"\n📋 分析结果:")
        print(f"   资料类型: {extracted.document_type_name}")
        print(f"   主体名称: {extracted.name or '未识别'}")
        print(f"   标题/职位: {extracted.title or '未识别'}")
        print(f"   建议 Skill 类型: {extracted.suggested_skill_type}")
        
        # 构建配置
        config = {
            'name': extracted.name or hint or "助手",
            'title': extracted.title or "",
            'description': extracted.description or "",
            'document_type': extracted.document_type.value,
            'key_points': extracted.key_points,
            'structured_data': extracted.structured_data,
            'suggested_skill_type': extracted.suggested_skill_type,
            'suggested_triggers': extracted.suggested_triggers,
            'persona_info': extracted.persona_info,
            '_source_files': file_paths,
            '_extraction_method': 'llm'
        }
        
        # 兼容旧的 PERSONA_INFO 格式
        if extracted.persona_info:
            for key, value in extracted.persona_info.items():
                if key not in config:
                    config[key] = value
        
        return config
    
    def generate(self, template_name: str, config: Dict[str, Any], output_dir: str = None) -> str:
        """
        生成 Skill
        
        Args:
            template_name: 模板名称
            config: 生成配置
            output_dir: 输出目录
            
        Returns:
            生成的 skill 路径
        """
        # 加载模板
        template = self.load_template(template_name)
        
        # 合并配置
        final_config = self._merge_config(template.get('defaults', {}), config)
        
        # 验证必填字段
        self._validate_config(template, final_config)
        
        # 确定输出路径
        name = final_config.get('name', 'skill')
        skill_name = final_config.get('skill_name')
        
        if not skill_name:
            # 生成 skill_name：如果是中文，使用 pinyin 风格；否则使用原名
            import re
            if re.search(r'[\u4e00-\u9fa5]', name):
                # 中文名，尝试转换为拼音风格
                skill_name = self._name_to_pinyin_slug(name)
            else:
                skill_name = f"{name.lower().replace(' ', '-')}-digital-twin"
        
        final_config['skill_name'] = skill_name
        output_path = Path(output_dir) if output_dir else self.output_dir
        skill_path = output_path / skill_name
        
        # 创建目录结构
        self._create_structure(skill_path, template)
        
        # 渲染模板文件
        self._render_templates(skill_path, template, final_config)
        
        # 复制静态文件
        self._copy_static_files(skill_path, template)
        
        # 复制源文件到 data/documents（用于参考）
        self._copy_source_files(skill_path, config.get('_source_files', []))
        
        # 生成 Karpathy Style Wiki 文件
        self._generate_wiki_files(skill_path, config)
        
        return str(skill_path)
    
    def _merge_config(self, defaults: Dict, user_config: Dict) -> Dict:
        """合并默认配置和用户配置"""
        result = defaults.copy()
        result.update(user_config)
        return result
    
    def _validate_config(self, template: Dict, config: Dict):
        """验证配置"""
        required = template.get('required_fields', [])
        missing = [field for field in required if field not in config or not config[field]]
        if missing:
            raise ValueError(f"缺少必填字段: {', '.join(missing)}")
    
    def _create_structure(self, skill_path: Path, template: Dict):
        """创建目录结构"""
        # 创建基础目录
        directories = [
            skill_path / "scripts",
            skill_path / "data" / "documents",
            skill_path / "data" / "memory",
            skill_path / "data" / "wiki",  # Karpathy Style 知识库目录
        ]
        
        # 添加模板自定义目录
        custom_dirs = template.get('directories', [])
        for dir_path in custom_dirs:
            directories.append(skill_path / dir_path)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _render_templates(self, skill_path: Path, template: Dict, config: Dict):
        """渲染模板文件"""
        template_path = Path(template['_template_path'])
        
        # 准备渲染变量
        render_vars = self._prepare_render_vars(config)
        
        # 渲染每个文件
        files_to_render = template.get('files', {})
        for dest_path, template_file in files_to_render.items():
            template_file_path = template_path / template_file
            if template_file_path.exists():
                with open(template_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换变量
                rendered = self._render_string(content, render_vars)
                
                # 写入目标文件
                dest_file = skill_path / dest_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_file, 'w', encoding='utf-8') as f:
                    f.write(rendered)
    
    def _copy_static_files(self, skill_path: Path, template: Dict):
        """复制静态文件"""
        template_path = Path(template['_template_path'])
        static_files = template.get('static_files', {})
        
        for src, dest in static_files.items():
            src_path = template_path / src
            dest_path = skill_path / dest
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
    
    def _copy_source_files(self, skill_path: Path, source_files: List[str]):
        """复制源文件到 data/documents"""
        if not source_files:
            return
        
        doc_dir = skill_path / "data" / "documents"
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in source_files:
            path = Path(file_path)
            if path.exists():
                dest = doc_dir / path.name
                shutil.copy2(path, dest)
    
    def _generate_wiki_files(self, skill_path: Path, config: Dict):
        """
        生成 Karpathy Style Markdown 知识库文件
        
        将提取的 persona_info 写入 data/wiki/*.md 文件
        这是真正的 Karpathy Style - Markdown 文件作为知识库，无需 RAG
        """
        wiki_dir = skill_path / "data" / "wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        
        name = config.get('name', '助手')
        
        # 定义要生成的 wiki 文件
        wiki_files = {
            '基本介绍.md': self._generate_wiki_basic_intro(config, name),
            '工作经验.md': self._generate_wiki_work_experience(config, name),
            '教育背景.md': self._generate_wiki_education(config, name),
            '专业技能.md': self._generate_wiki_skills(config, name),
            '性格特点.md': self._generate_wiki_personality(config, name),
            '兴趣爱好.md': self._generate_wiki_interests(config, name),
            '联系方式.md': self._generate_wiki_contact(config, name),
        }
        
        # 写入文件
        for filename, content in wiki_files.items():
            if content:  # 只写入有内容的文件
                file_path = wiki_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # 生成索引文件
        index_content = self._generate_wiki_index(config, name)
        with open(wiki_dir / '_index.md', 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"   📚 生成 Wiki 知识库: {wiki_dir} ({len([c for c in wiki_files.values() if c])} 个文件)")
    
    def _generate_wiki_basic_intro(self, config: Dict, name: str) -> str:
        """生成基本介绍 wiki 文件"""
        title = config.get('title', '')
        company = config.get('company', '')
        description = config.get('description', '')
        
        content = f"""# 基本介绍

## {name}
"""
        if title:
            content += f"\n**职位**: {title}"
        if company:
            content += f"\n**公司**: {company}"
        
        content += f"\n\n## 简介\n\n"
        
        if description:
            content += description
        else:
            content += f"我是{name}"
            if title:
                content += f"，{title}"
            if company:
                content += f"，目前在{company}工作"
            content += "。"
        
        # 添加关键要点
        key_points = config.get('key_points', [])
        if key_points:
            content += "\n\n## 关键要点\n\n"
            for point in key_points[:5]:
                content += f"- {point}\n"
        
        content += "\n"
        return content
    
    def _generate_wiki_work_experience(self, config: Dict, name: str) -> str:
        """生成工作经验 wiki 文件"""
        work_exp = config.get('work_experience', '')
        structured_data = config.get('structured_data', {})
        
        # 尝试从 structured_data 获取工作经历
        experiences = structured_data.get('work_experience', []) if isinstance(structured_data, dict) else []
        
        if not work_exp and not experiences:
            return ""
        
        content = f"""# 工作经验

## 工作经历

"""
        if experiences:
            for exp in experiences:
                if isinstance(exp, dict):
                    company = exp.get('company', '')
                    title = exp.get('title', '')
                    period = exp.get('period', '')
                    desc = exp.get('description', '')
                    
                    if company or title:
                        content += f"### {title or '职位'}"
                        if company:
                            content += f" @ {company}"
                        content += "\n"
                        if period:
                            content += f"**时间**: {period}\n\n"
                        if desc:
                            content += f"{desc}\n\n"
        elif work_exp:
            content += f"{work_exp}\n\n"
        
        return content
    
    def _generate_wiki_education(self, config: Dict, name: str) -> str:
        """生成教育背景 wiki 文件"""
        education = config.get('education', '')
        structured_data = config.get('structured_data', {})
        
        educations = structured_data.get('education', []) if isinstance(structured_data, dict) else []
        
        if not education and not educations:
            return ""
        
        content = "# 教育背景\n\n"
        
        if educations:
            for edu in educations:
                if isinstance(edu, dict):
                    school = edu.get('school', '')
                    degree = edu.get('degree', '')
                    major = edu.get('major', '')
                    period = edu.get('period', '')
                    
                    if school:
                        content += f"## {school}\n\n"
                        if degree:
                            content += f"**学位**: {degree}\n\n"
                        if major:
                            content += f"**专业**: {major}\n\n"
                        if period:
                            content += f"**时间**: {period}\n\n"
        elif education:
            content += f"{education}\n\n"
        
        return content
    
    def _generate_wiki_skills(self, config: Dict, name: str) -> str:
        """生成专业技能 wiki 文件"""
        skills = config.get('skills', '')
        structured_data = config.get('structured_data', {})
        
        skill_list = structured_data.get('skills', []) if isinstance(structured_data, dict) else []
        
        if not skills and not skill_list:
            return ""
        
        content = "# 专业技能\n\n"
        
        if skill_list:
            content += "## 技能列表\n\n"
            for skill in skill_list:
                if isinstance(skill, dict):
                    name_skill = skill.get('name', '')
                    level = skill.get('level', '')
                    desc = skill.get('description', '')
                    if name_skill:
                        content += f"- **{name_skill}**"
                        if level:
                            content += f" ({level})"
                        if desc:
                            content += f": {desc}"
                        content += "\n"
                elif isinstance(skill, str):
                    content += f"- {skill}\n"
        elif skills:
            content += f"{skills}\n"
        
        content += "\n"
        return content
    
    def _generate_wiki_personality(self, config: Dict, name: str) -> str:
        """生成性格特点 wiki 文件"""
        personality = config.get('personality', '')
        tone_style = config.get('tone_style', {})
        
        if not personality and not tone_style:
            return ""
        
        content = f"""# 性格特点

## 性格描述

"""
        if personality:
            content += f"{personality}\n\n"
        
        # 添加说话风格分析
        if tone_style and isinstance(tone_style, dict):
            content += "## 说话风格\n\n"
            
            common_phrases = tone_style.get('common_phrases', [])
            if common_phrases:
                content += "### 常用语\n\n"
                for phrase in common_phrases[:10]:
                    content += f"- \"{phrase}\"\n"
                content += "\n"
            
            emojis = tone_style.get('emojis', [])
            if emojis:
                content += f"**常用表情**: {' '.join(emojis[:10])}\n\n"
            
            avg_length = tone_style.get('avg_message_length')
            if avg_length:
                content += f"**平均消息长度**: {avg_length:.0f} 字\n\n"
        
        return content
    
    def _generate_wiki_interests(self, config: Dict, name: str) -> str:
        """生成兴趣爱好 wiki 文件"""
        interests = config.get('interests', '')
        
        if not interests:
            return ""
        
        return f"""# 兴趣爱好

{interests}

"""
    
    def _generate_wiki_contact(self, config: Dict, name: str) -> str:
        """生成联系方式 wiki 文件"""
        contact = config.get('contact', '')
        
        if not contact:
            return ""
        
        return f"""# 联系方式

{contact}

"""
    
    def _generate_wiki_index(self, config: Dict, name: str) -> str:
        """生成 Wiki 索引文件"""
        content = f"""# {name} - 知识库索引

这是一个 Karpathy Style 知识库 - 使用 Markdown 文件组织信息，无需 RAG。

## 文件结构

- [基本介绍](./基本介绍.md) - 基本信息和简介
- [工作经验](./工作经验.md) - 工作经历和项目经验
- [教育背景](./教育背景.md) - 教育经历
- [专业技能](./专业技能.md) - 技能和专长
- [性格特点](./性格特点.md) - 性格和说话风格
- [兴趣爱好](./兴趣爱好.md) - 个人兴趣
- [联系方式](./联系方式.md) - 联系信息

## 使用方式

AI 助手直接读取这些 Markdown 文件来获取关于 {name} 的信息。

---

*由 Skill Generator 自动生成*
"""
        return content
    
    def _prepare_render_vars(self, config: Dict) -> Dict:
        """准备渲染变量"""
        vars_dict = config.copy()
        vars_dict['created_at'] = datetime.now().strftime("%Y-%m-%d")
        vars_dict['created_year'] = datetime.now().year
        
        # 自动生成的变量
        name = config.get('name', '')
        vars_dict['skill_name_underscore'] = config.get('skill_name', name).replace('-', '_')
        vars_dict['skill_name_slug'] = config.get('skill_name', name).replace('_', '-').lower()
        vars_dict['persona_class'] = name.replace(' ', '').replace('-', '') if name else 'Person'
        
        # 处理列表为 YAML 格式
        if 'triggers' in vars_dict:
            vars_dict['triggers_yaml'] = '\n'.join(f'  - "{t}"' for t in vars_dict['triggers'])
        
        if 'particles' in vars_dict:
            vars_dict['particles_str'] = '/'.join(vars_dict['particles'])
        
        if 'tone_examples' in vars_dict:
            vars_dict['tone_examples_str'] = '\n'.join(f"✅ {ex}" for ex in vars_dict['tone_examples'])
        
        if 'reply_examples' in vars_dict:
            vars_dict['reply_examples_str'] = '\n'.join(f'   - "{ex}"' for ex in vars_dict['reply_examples'])
        
        # 处理源文件列表显示
        source_files = config.get('_source_files', [])
        vars_dict['_source_files_display'] = ', '.join(source_files) if source_files else '手动配置'
        
        # 生成 PERSONA_INFO Python 代码
        vars_dict['persona_info_py'] = self._generate_persona_info_py(config)
        
        # 生成 REPLY_TEMPLATES
        vars_dict['reply_templates_py'] = self._generate_reply_templates_py(config)
        
        return vars_dict
    
    def _generate_persona_info_py(self, config: Dict) -> str:
        """生成 PERSONA_INFO Python 字典代码"""
        persona_items = []
        
        # 基本信息
        name = config.get('name', '用户')
        title = config.get('title', '')
        
        basic_intro = config.get('basic_intro', '')
        if not basic_intro and name:
            basic_intro = f"我是{name}"
            if title:
                basic_intro += f"，{title}"
            basic_intro += "。"
        
        if basic_intro:
            persona_items.append(f'    "基本介绍": "{basic_intro}"')
        
        if config.get('work_experience'):
            persona_items.append(f'    "工作经验": "{config["work_experience"]}"')
        
        if config.get('education'):
            persona_items.append(f'    "教育背景": "{config["education"]}"')
        
        if config.get('skills'):
            persona_items.append(f'    "技能": "{config["skills"]}"')
        
        if config.get('company'):
            persona_items.append(f'    "所在公司": "{config["company"]}"')
        
        if config.get('title'):
            persona_items.append(f'    "职位": "{config["title"]}"')
        
        if config.get('personality'):
            persona_items.append(f'    "性格": "{config["personality"]}"')
        
        if config.get('interests'):
            persona_items.append(f'    "兴趣爱好": "{config["interests"]}"')
        
        if config.get('contact'):
            persona_items.append(f'    "联系方式": "{config["contact"]}"')
        
        # 如果没有提取到任何信息，添加默认值
        if not persona_items:
            persona_items = [
                f'    "基本介绍": "我是{name}。"',
            ]
        
        return ',\n'.join(persona_items)
    
    def _generate_reply_templates_py(self, config: Dict) -> str:
        """生成 REPLY_TEMPLATES Python 代码"""
        templates = []
        name = config.get('name', '')
        
        # 个人信息回复
        if config.get('tone_style'):
            # 有聊天记录分析，使用学习到的风格
            templates.append('    "个人信息": [')
            templates.append(f'        "{{answer}} 还有啥想了解的可以直接问我～",')
            templates.append(f'        "{{answer}} 😊",')
            templates.append('    ],')
        else:
            templates.append('    "个人信息": [')
            templates.append(f'        "{{answer}} 还有什么想了解的可以直接问我呀～",')
            templates.append(f'        "{{answer}} 😊",')
            templates.append('    ],')
        
        # 其他模板
        templates.append('    "找到文件": [')
        templates.append('        "好呀～{filename}发给你啦！看看收到没～😊",')
        templates.append('        "发过去啦～用的是{filename}，内容比较全呢！",')
        templates.append('    ],')
        
        templates.append('    "日程": [')
        templates.append('        "我看了一下，{schedule_desc} 你要约哪个时间段呀～",')
        templates.append('        "{schedule_desc} 你有啥安排想跟我碰的？",')
        templates.append('    ],')
        
        templates.append('    "转人工": [')
        templates.append(f'        "这个问题比较重要，我直接转给{name}本人回复你哈～",')
        templates.append(f'        "这个得让{name}亲自回你，已经通知她/他啦～",')
        templates.append('    ],')
        
        return '\n'.join(templates)
    
    def _name_to_pinyin_slug(self, name: str) -> str:
        """将中文名转换为拼音风格的 slug"""
        # 常见姓氏映射
        surname_map = {
            '王': 'wang', '李': 'li', '张': 'zhang', '刘': 'liu', '陈': 'chen',
            '杨': 'yang', '黄': 'huang', '赵': 'zhao', '吴': 'wu', '周': 'zhou',
            '徐': 'xu', '孙': 'sun', '马': 'ma', '朱': 'zhu', '胡': 'hu',
            '郭': 'guo', '林': 'lin', '何': 'he', '高': 'gao', '罗': 'luo',
            '郑': 'zheng', '梁': 'liang', '谢': 'xie', '宋': 'song', '唐': 'tang',
            '许': 'xu', '韩': 'han', '冯': 'feng', '邓': 'deng', '曹': 'cao',
            '彭': 'peng', '曾': 'zeng', '肖': 'xiao', '田': 'tian', '董': 'dong',
            '潘': 'pan', '袁': 'yuan', '蔡': 'cai', '蒋': 'jiang', '余': 'yu',
            '于': 'yu', '杜': 'du', '叶': 'ye', '程': 'cheng', '魏': 'wei',
            '苏': 'su', '吕': 'lv', '丁': 'ding', '任': 'ren', '沈': 'shen',
            '姚': 'yao', '卢': 'lu', '姜': 'jiang', '崔': 'cui', '钟': 'zhong',
            '谭': 'tan', '陆': 'lu', '汪': 'wang', '范': 'fan', '金': 'jin',
            '石': 'shi', '廖': 'liao', '贾': 'jia', '夏': 'xia', '韦': 'wei',
            '傅': 'fu', '方': 'fang', '白': 'bai', '邹': 'zou', '孟': 'meng',
            '熊': 'xiong', '秦': 'qin', '邱': 'qiu', '江': 'jiang', '尹': 'yin',
            '薛': 'xue', '闫': 'yan', '段': 'duan', '雷': 'lei', '侯': 'hou',
            '龙': 'long', '史': 'shi', '黎': 'li', '贺': 'he', '顾': 'gu',
            '毛': 'mao', '郝': 'hao', '龚': 'gong', '邵': 'shao', '万': 'wan',
            '钱': 'qian', '严': 'yan', '覃': 'qin', '武': 'wu', '戴': 'dai',
            '莫': 'mo', '孔': 'kong', '向': 'xiang', '汤': 'tang',
        }
        
        # 尝试匹配姓氏
        for cn, py in surname_map.items():
            if name.startswith(cn):
                # 剩余部分直接转小写（简化处理）
                remainder = name[len(cn):]
                # 使用 unicode 编码作为备选
                import hashlib
                if remainder:
                    # 取剩余部分的前两个字符的 hash
                    short_hash = hashlib.md5(remainder.encode()).hexdigest()[:6]
                    return f"{py}-{short_hash}-digital-twin"
                else:
                    return f"{py}-digital-twin"
        
        # 无法识别的中文名，使用 hash
        import hashlib
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"persona-{name_hash}-digital-twin"

    def _render_string(self, template: str, vars_dict: Dict) -> str:
        """渲染字符串模板"""
        result = template
        for key, value in vars_dict.items():
            placeholder = '{' + key + '}'
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        # 将 {{ 和 }} 转换为单个大括号（这些是 Python 代码中的字面量）
        result = result.replace('{{', '{').replace('}}', '}')
        
        return result


def main():
    parser = argparse.ArgumentParser(
        description='OpenClaw Skill Generator - 智能从任意资料生成 Skill',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 智能模式：自动识别资料类型（推荐）⭐
  python3 skill_generator.py --smart --from-files 资料.pdf --name "产品名"
  
  # 从简历生成
  python3 skill_generator.py --from-files 简历.pdf --name "王艺涵"
  
  # 从产品文档生成
  python3 skill_generator.py --smart --from-files 产品手册.docx --name "产品助手"
  
  # 基础生成（手动配置）
  python3 skill_generator.py --template personal_digital_twin --name "张三"

环境变量:
  OPENAI_API_KEY      - OpenAI API 密钥（智能模式需要）
  ANTHROPIC_API_KEY   - Anthropic API 密钥（可选）
        """
    )
    
    parser.add_argument('--template', '-t', default='personal_digital_twin',
                       help='模板名称（默认: personal_digital_twin）')
    parser.add_argument('--name', '-n', help='分身名称（如：王艺涵）')
    parser.add_argument('--skill-name', '-s', help='Skill 目录名')
    parser.add_argument('--output', '-o', default='./skills', help='输出目录（默认: ./skills）')
    parser.add_argument('--config', '-c', help='配置文件路径（JSON格式）')
    parser.add_argument('--list', '-l', action='store_true', help='列出可用模板')
    
    # 文件提取相关参数
    parser.add_argument('--from-files', '-f', nargs='+', metavar='FILE',
                       help='从文件自动提取信息（支持: pdf, docx, txt, md, json, csv）')
    parser.add_argument('--chat-files', nargs='+', metavar='FILE',
                       help='指定聊天记录文件（用于分析说话风格）')
    parser.add_argument('--smart', '-S', action='store_true',
                       help='使用 LLM 智能分析资料类型（自动识别简历、产品文档、技术文档等）')
    parser.add_argument('--llm-provider', default='openai',
                       help='LLM 提供商 (openai, anthropic)，默认: openai')
    
    args = parser.parse_args()
    
    generator = SkillGenerator()
    
    # 列出模板
    if args.list:
        templates = generator.list_templates()
        print("可用模板:")
        for t in templates:
            print(f"  - {t}")
        return
    
    # 收集源文件
    source_files = []
    if args.from_files:
        source_files.extend(args.from_files)
    if args.chat_files:
        source_files.extend(args.chat_files)
    
    # 确定配置
    config = {}
    template_name = args.template
    
    # 方式1: 从文件提取
    if source_files:
        # 方式1a: 智能 LLM 提取（推荐，支持任意资料类型）
        if args.smart:
            print("🚀 启动智能模式：使用 LLM 分析资料类型...")
            try:
                extracted_config = generator.extract_from_files_with_llm(
                    source_files, 
                    hint=args.name,
                    llm_provider=args.llm_provider
                )
                config.update(extracted_config)
                config['_source_files'] = source_files
                # 根据提取的资料类型自动选择模板
                if extracted_config.get('suggested_skill_type'):
                    suggested = extracted_config['suggested_skill_type']
                    if suggested in generator.list_templates():
                        template_name = suggested
                        print(f"   自动选择模板: {template_name}")
            except Exception as e:
                print(f"❌ LLM 提取失败: {e}")
                print("   尝试使用规则提取...")
                # 后备到规则提取
                if not args.name:
                    print("❌ 需要提供 --name 作为提示")
                    return 1
                extracted_config = generator.extract_from_files(source_files, name_hint=args.name)
                config.update(extracted_config)
                config['_source_files'] = source_files
        
        # 方式1b: 传统规则提取（仅支持简历类资料）
        else:
            if not args.name:
                print("❌ 使用 --from-files 时需要提供 --name 作为姓名提示")
                return 1
            
            try:
                extracted_config = generator.extract_from_files(source_files, name_hint=args.name)
                config.update(extracted_config)
                config['_source_files'] = source_files
            except Exception as e:
                print(f"❌ 文件提取失败: {e}")
                return 1
    
    # 方式2: 加载配置文件
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # 配置文件优先级高于提取的配置
            config.update(file_config)
            template_name = file_config.get('template', template_name)
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return 1
    
    # 方式3: 命令行参数
    if args.name:
        config['name'] = args.name
    if args.skill_name:
        config['skill_name'] = args.skill_name
    
    # 验证
    if not config.get('name'):
        parser.error("需要提供 --name 或使用 --config 指定配置文件")
    
    # 生成
    try:
        skill_path = generator.generate(template_name, config, args.output)
        print(f"\n✅ Skill 生成成功!")
        print(f"   路径: {skill_path}")
        print(f"\n使用方式:")
        print(f"   1. 将 {skill_path} 复制到 OpenClaw skills 目录")
        print(f"   2. 重启 OpenClaw 服务")
        print(f"   3. 在聊天中 @{config['name']} 测试")
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
