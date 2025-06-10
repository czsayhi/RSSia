#!/usr/bin/env python3
"""
字段标准化检查和修复工具
识别并修复项目中的字段命名不一致问题
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class FieldIssue:
    """字段问题记录"""
    file_path: str
    line_number: int
    issue_type: str
    current_field: str
    suggested_field: str
    context: str


class FieldStandardizationChecker:
    """字段标准化检查器"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues: List[FieldIssue] = []
        
        # 定义标准字段映射
        self.field_standards = {
            # 模版相关
            "id": "template_id",  # JSON配置中的id应该叫template_id
            "display_name": "template_name",  # 模版显示名称统一
            "name": "template_name",  # 各种name都统一为template_name
            
            # 用户相关
            "user_id": "user_id",  # 保持不变
            "username": "username",  # 保持不变
            
            # 订阅相关 
            "subscription_id": "subscription_id",  # 保持不变
            "source_id": "template_id",  # 前端的source_id改为template_id
            
            # 状态相关
            "status": "status",  # 保持不变，但值需要统一
            "is_active": "is_active",  # 保持不变
            
            # 时间相关
            "created_at": "created_at",  # 统一时间字段名
            "create_time": "created_at",  # 统一为created_at
            "updated_at": "updated_at",  # 统一时间字段名
            "update_time": "updated_at"  # 统一为updated_at
        }
        
        # 状态值标准化
        self.status_standards = {
            "open": "active",
            "closed": "inactive", 
            "active": "active",
            "inactive": "inactive",
            "error": "error"
        }
        
        # 需要检查的文件模式
        self.file_patterns = [
            "**/*.py",
            "**/*.json",
            "**/*.ts",
            "**/*.tsx"
        ]
        
        # 排除的目录
        self.exclude_dirs = {
            "__pycache__", ".git", "node_modules", ".next", 
            "venv", ".venv", "dist", "build"
        }
    
    def check_all_files(self) -> List[FieldIssue]:
        """检查所有文件的字段标准化问题"""
        print("🔍 开始检查字段标准化问题...")
        
        for pattern in self.file_patterns:
            for file_path in self.root_path.glob(pattern):
                if self._should_skip_file(file_path):
                    continue
                
                try:
                    self._check_file(file_path)
                except Exception as e:
                    print(f"❌ 检查文件失败: {file_path} - {e}")
        
        return self.issues
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """检查是否应该跳过这个文件"""
        # 跳过排除的目录
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return True
        
        # 跳过这个工具本身
        if file_path.name == "field_standardization_checker.py":
            return True
            
        return False
    
    def _check_file(self, file_path: Path) -> None:
        """检查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.suffix == '.json':
                self._check_json_file(file_path, content)
            elif file_path.suffix in ['.py', '.ts', '.tsx']:
                self._check_code_file(file_path, content)
                
        except UnicodeDecodeError:
            # 跳过二进制文件
            pass
    
    def _check_json_file(self, file_path: Path, content: str) -> None:
        """检查JSON文件"""
        try:
            data = json.loads(content)
            self._check_json_data(file_path, data, content)
        except json.JSONDecodeError:
            pass
    
    def _check_json_data(self, file_path: Path, data: any, content: str) -> None:
        """递归检查JSON数据"""
        if isinstance(data, dict):
            for key, value in data.items():
                # 检查字段名
                if key in self.field_standards and key != self.field_standards[key]:
                    line_num = self._find_line_number(content, f'"{key}":')
                    self.issues.append(FieldIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="field_name",
                        current_field=key,
                        suggested_field=self.field_standards[key],
                        context=f'JSON field "{key}" should be "{self.field_standards[key]}"'
                    ))
                
                # 递归检查嵌套结构
                self._check_json_data(file_path, value, content)
                
        elif isinstance(data, list):
            for item in data:
                self._check_json_data(file_path, item, content)
    
    def _check_code_file(self, file_path: Path, content: str) -> None:
        """检查代码文件"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检查字段定义和使用
            self._check_line_for_field_issues(file_path, line_num, line)
    
    def _check_line_for_field_issues(self, file_path: Path, line_num: int, line: str) -> None:
        """检查单行代码的字段问题"""
        # 检查字典键的使用 如 "source_id", 'display_name' 等
        field_patterns = [
            r'["\'](\w+)["\']:\s*',  # JSON风格的键
            r'\.(\w+)\s*=',  # 属性赋值
            r'(\w+)\s*=\s*Field',  # Pydantic字段定义
            r'item\.(\w+)',  # 对象属性访问
            r'\.(\w+)\s*\?',  # TypeScript可选属性
        ]
        
        for pattern in field_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                field_name = match.group(1)
                if field_name in self.field_standards and field_name != self.field_standards[field_name]:
                    self.issues.append(FieldIssue(
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="field_usage",
                        current_field=field_name,
                        suggested_field=self.field_standards[field_name],
                        context=line.strip()
                    ))
    
    def _find_line_number(self, content: str, search_text: str) -> int:
        """查找文本在文件中的行号"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 1
    
    def generate_report(self) -> str:
        """生成检查报告"""
        if not self.issues:
            return "✅ 未发现字段标准化问题！"
        
        report = []
        report.append(f"📊 字段标准化检查报告")
        report.append(f"=" * 50)
        report.append(f"总计发现 {len(self.issues)} 个问题\n")
        
        # 按文件分组
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            report.append(f"📁 {file_path}")
            for issue in file_issues:
                report.append(f"  📍 第{issue.line_number}行: {issue.current_field} → {issue.suggested_field}")
                report.append(f"     上下文: {issue.context}")
            report.append("")
        
        return "\n".join(report)
    
    def generate_fix_script(self) -> str:
        """生成修复脚本"""
        if not self.issues:
            return "# 没有需要修复的问题"
        
        script_lines = []
        script_lines.append("#!/bin/bash")
        script_lines.append("# 字段标准化修复脚本")
        script_lines.append("# 请仔细检查每个替换操作，确认无误后执行")
        script_lines.append("")
        
        # 按文件分组生成修复命令
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            script_lines.append(f"echo '修复文件: {file_path}'")
            
            for issue in file_issues:
                if issue.issue_type == "field_name":
                    # JSON字段替换
                    script_lines.append(
                        f"sed -i 's/\"{issue.current_field}\":/\"{issue.suggested_field}\":/g' {file_path}"
                    )
                elif issue.issue_type == "field_usage":
                    # 代码中的字段使用替换（需要更精确的替换）
                    script_lines.append(f"# 手动检查并替换: {issue.current_field} → {issue.suggested_field}")
            
            script_lines.append("")
        
        return "\n".join(script_lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="字段标准化检查工具")
    parser.add_argument("--check", action="store_true", help="检查字段标准化问题")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    parser.add_argument("--fix-script", action="store_true", help="生成修复脚本")
    parser.add_argument("--path", default=".", help="检查路径，默认为当前目录")
    
    args = parser.parse_args()
    
    checker = FieldStandardizationChecker(args.path)
    
    if args.check or args.report:
        issues = checker.check_all_files()
        
        if args.report:
            print(checker.generate_report())
        else:
            print(f"发现 {len(issues)} 个字段标准化问题")
            for issue in issues[:10]:  # 只显示前10个
                print(f"  {issue.file_path}:{issue.line_number} {issue.current_field} → {issue.suggested_field}")
            if len(issues) > 10:
                print(f"  ... 还有 {len(issues) - 10} 个问题")
    
    if args.fix_script:
        issues = checker.check_all_files()
        script = checker.generate_fix_script()
        
        with open("fix_field_standardization.sh", "w") as f:
            f.write(script)
        print("✅ 修复脚本已生成: fix_field_standardization.sh")


if __name__ == "__main__":
    main() 