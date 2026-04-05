#!/usr/bin/env python3
"""
OpenClaw Skill Generator
通用 Skill 生成器 - 支持多种 Skill 模板

用法:
    # 生成分身 Skill
    python3 skill_generator.py --template personal_digital_twin --name "张三" --output ./skills
    
    # 使用配置文件
    python3 skill_generator.py --config config.json
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


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
        skill_name = final_config.get('skill_name', f"{final_config.get('name', 'skill')}-digital-twin")
        output_path = Path(output_dir) if output_dir else self.output_dir
        skill_path = output_path / skill_name
        
        # 创建目录结构
        self._create_structure(skill_path, template)
        
        # 渲染模板文件
        self._render_templates(skill_path, template, final_config)
        
        # 复制静态文件
        self._copy_static_files(skill_path, template)
        
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
        static_files = template.get('static_files', [])
        
        for src, dest in static_files.items():
            src_path = template_path / src
            dest_path = skill_path / dest
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
    
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
        
        return vars_dict
    
    def _render_string(self, template: str, vars_dict: Dict) -> str:
        """渲染字符串模板"""
        result = template
        for key, value in vars_dict.items():
            placeholder = '{' + key + '}'
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result


def main():
    parser = argparse.ArgumentParser(description='OpenClaw Skill Generator')
    parser.add_argument('--template', '-t', help='模板名称')
    parser.add_argument('--name', '-n', help='分身名称（如：王艺涵）')
    parser.add_argument('--skill-name', '-s', help='Skill 目录名')
    parser.add_argument('--output', '-o', default='./skills', help='输出目录')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--list', '-l', action='store_true', help='列出可用模板')
    
    args = parser.parse_args()
    
    generator = SkillGenerator()
    
    # 列出模板
    if args.list:
        templates = generator.list_templates()
        print("可用模板:")
        for t in templates:
            print(f"  - {t}")
        return
    
    # 加载配置
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        template_name = config.get('template')
    else:
        if not args.template or not args.name:
            parser.error("需要提供 --template 和 --name，或使用 --config")
        template_name = args.template
        config = {
            'name': args.name,
            'skill_name': args.skill_name or f"{args.name.lower().replace(' ', '-')}-digital-twin"
        }
    
    # 生成
    try:
        skill_path = generator.generate(template_name, config, args.output)
        print(f"✅ Skill 生成成功: {skill_path}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
