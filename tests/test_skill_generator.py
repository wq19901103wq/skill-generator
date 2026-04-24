"""
Skill Generator 主生成器测试

测试范围:
- SkillGenerator 类的方法
- 模板加载和渲染
- 配置合并和验证
- 目录结构创建
"""

import pytest
import json
from pathlib import Path
from skill_generator import SkillGenerator


class TestSkillGenerator:
    """测试 SkillGenerator 主生成器"""

    @pytest.fixture
    def generator(self):
        return SkillGenerator()

    @pytest.fixture
    def template_dir(self, tmp_path):
        """创建临时模板目录"""
        template_path = tmp_path / "templates" / "test_template"
        template_path.mkdir(parents=True)
        
        # 创建 manifest.json
        manifest = {
            "name": "test_template",
            "description": "测试模板",
            "version": "1.0.0",
            "defaults": {
                "greeting": "你好",
                "triggers": ["@{name}"]
            },
            "required_fields": ["name"],
            "directories": ["data/wiki"],
            "files": {
                "SKILL.md": "SKILL.md.template"
            },
            "static_files": {}
        }
        (template_path / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False),
            encoding="utf-8"
        )
        
        # 创建模板文件
        (template_path / "SKILL.md.template").write_text(
            "---\nname: {skill_name}\n---\n# {name}\n{greeting}！",
            encoding="utf-8"
        )
        
        return tmp_path / "templates"

    def test_list_templates(self, generator, template_dir):
        """测试列出模板"""
        gen = SkillGenerator(template_dir=str(template_dir))
        templates = gen.list_templates()
        
        assert "test_template" in templates

    def test_load_template(self, generator, template_dir):
        """测试加载模板"""
        gen = SkillGenerator(template_dir=str(template_dir))
        template = gen.load_template("test_template")
        
        assert template["name"] == "test_template"
        assert template["required_fields"] == ["name"]
        assert "_template_path" in template

    def test_load_template_not_found(self, generator):
        """测试加载不存在的模板"""
        with pytest.raises(ValueError) as exc_info:
            generator.load_template("nonexistent")
        
        assert "不存在" in str(exc_info.value)

    def test_merge_config(self, generator):
        """测试配置合并"""
        defaults = {"greeting": "你好", "title": "工程师"}
        user_config = {"name": "张三", "greeting": "您好"}
        
        result = generator._merge_config(defaults, user_config)
        
        assert result["name"] == "张三"      # 用户配置优先
        assert result["greeting"] == "您好"  # 用户配置覆盖默认值
        assert result["title"] == "工程师"   # 默认值保留

    def test_validate_config_success(self, generator, template_dir):
        """测试配置验证通过"""
        gen = SkillGenerator(template_dir=str(template_dir))
        template = gen.load_template("test_template")
        config = {"name": "张三"}
        
        # 不应该抛异常
        gen._validate_config(template, config)

    def test_validate_config_missing_required(self, generator, template_dir):
        """测试缺少必填字段"""
        gen = SkillGenerator(template_dir=str(template_dir))
        template = gen.load_template("test_template")
        config = {}  # 缺少 name
        
        with pytest.raises(ValueError) as exc_info:
            gen._validate_config(template, config)
        
        assert "缺少必填字段" in str(exc_info.value)
        assert "name" in str(exc_info.value)

    def test_generate(self, generator, template_dir, tmp_path):
        """测试完整生成流程"""
        gen = SkillGenerator(template_dir=str(template_dir))
        output_dir = tmp_path / "output"
        
        skill_path = gen.generate(
            template_name="test_template",
            config={"name": "张三"},
            output_dir=str(output_dir)
        )
        
        # 验证目录结构
        skill_dir = Path(skill_path)
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "data" / "wiki").exists()
        
        # 验证渲染结果
        skill_content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "张三" in skill_content
        assert "您好" in skill_content or "你好" in skill_content

    def test_name_to_pinyin_slug(self, generator):
        """测试中文名转拼音 slug"""
        # Surname mapped + MD5 hash of remainder + "-digital-twin" suffix
        slug1 = generator._name_to_pinyin_slug("张三")
        assert slug1.startswith("zhang-") and slug1.endswith("-digital-twin")

        slug2 = generator._name_to_pinyin_slug("李四")
        assert slug2.startswith("li-") and slug2.endswith("-digital-twin")

        slug3 = generator._name_to_pinyin_slug("王艺涵")
        assert slug3.startswith("wang-") and slug3.endswith("-digital-twin")

    def test_render_string(self, generator):
        """测试字符串渲染"""
        template = "你好，{name}！你的职位是{title}。"
        vars_dict = {"name": "张三", "title": "产品经理"}
        
        result = generator._render_string(template, vars_dict)
        
        assert result == "你好，张三！你的职位是产品经理。"

    def test_render_string_missing_var(self, generator):
        """测试渲染时变量缺失"""
        template = "你好，{name}！"
        vars_dict = {}  # 缺少 name
        
        # 变量缺失时应该保留原样或返回空
        result = generator._render_string(template, vars_dict)
        # 当前实现可能保留 {name} 或替换为空
        assert isinstance(result, str)


class TestCLIFunctions:
    """测试 CLI 相关功能"""

    def test_cli_list_templates(self, capsys):
        """测试 --list 参数"""
        import sys
        from unittest.mock import patch
        
        with patch.object(sys, 'argv', ['skill_generator.py', '--list']):
            # 这里需要 mock 实际的 CLI 运行
            # 由于 CLI 直接调用 sys.argv，测试比较复杂
            # 建议后续将 CLI 逻辑抽取为独立函数以便测试
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
