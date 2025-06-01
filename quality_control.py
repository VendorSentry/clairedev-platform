
import ast
import os
import sys
import subprocess
import json
from typing import Dict, List, Tuple, Any
import traceback

class QualityControl:
    """Comprehensive quality control system to prevent rushing and ensure code quality"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.suggestions = []
    
    def validate_syntax(self, file_path: str) -> bool:
        """Check Python syntax before deployment"""
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            ast.parse(source)
            return True
        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
            return False
    
    def check_imports(self, file_path: str) -> bool:
        """Verify all imports are available"""
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            __import__(alias.name)
                        except ImportError:
                            self.errors.append(f"Missing import: {alias.name} in {file_path}")
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        try:
                            __import__(node.module)
                        except ImportError:
                            self.errors.append(f"Missing module: {node.module} in {file_path}")
                            return False
            return True
        except Exception as e:
            self.errors.append(f"Import check failed for {file_path}: {e}")
            return False
    
    def validate_functions(self, file_path: str) -> bool:
        """Check function definitions and basic structure"""
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for placeholder implementations
                    if any(isinstance(child, ast.Pass) for child in node.body):
                        self.warnings.append(f"Function {node.name} in {file_path} has placeholder implementation")
                    
                    # Check for TODO comments
                    if "TODO" in source or "FIXME" in source:
                        self.warnings.append(f"TODO/FIXME found in {file_path}")
            
            return True
        except Exception as e:
            self.errors.append(f"Function validation failed for {file_path}: {e}")
            return False
    
    def test_basic_functionality(self) -> bool:
        """Test basic app functionality before deployment"""
        try:
            # Test database connection
            from database import DatabaseManager
            db = DatabaseManager()
            db.create_tables()
            
            # Test basic imports
            import main
            
            self.suggestions.append("Basic functionality tests passed")
            return True
        except Exception as e:
            self.errors.append(f"Basic functionality test failed: {e}")
            return False
    
    def validate_env_requirements(self) -> bool:
        """Check environment requirements"""
        required_files = ['.env.example', 'requirements.txt', 'main.py']
        
        for file in required_files:
            if not os.path.exists(file):
                self.errors.append(f"Required file missing: {file}")
                return False
        
        return True
    
    def run_full_quality_check(self) -> Dict[str, Any]:
        """Run comprehensive quality check"""
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        python_files = [f for f in os.listdir('.') if f.endswith('.py')]
        
        all_passed = True
        
        # 1. Environment validation
        if not self.validate_env_requirements():
            all_passed = False
        
        # 2. Syntax validation
        for file in python_files:
            if not self.validate_syntax(file):
                all_passed = False
        
        # 3. Import validation
        for file in python_files:
            if not self.check_imports(file):
                all_passed = False
        
        # 4. Function validation
        for file in python_files:
            if not self.validate_functions(file):
                all_passed = False
        
        # 5. Basic functionality test
        if not self.test_basic_functionality():
            all_passed = False
        
        return {
            'passed': all_passed,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'files_checked': python_files
        }
    
    def generate_quality_report(self) -> str:
        """Generate detailed quality report"""
        result = self.run_full_quality_check()
        
        report = "🔍 QUALITY CONTROL REPORT\n"
        report += "=" * 50 + "\n\n"
        
        if result['passed']:
            report += "✅ ALL QUALITY CHECKS PASSED\n\n"
        else:
            report += "❌ QUALITY ISSUES FOUND\n\n"
        
        if result['errors']:
            report += "🚨 CRITICAL ERRORS:\n"
            for error in result['errors']:
                report += f"  • {error}\n"
            report += "\n"
        
        if result['warnings']:
            report += "⚠️  WARNINGS:\n"
            for warning in result['warnings']:
                report += f"  • {warning}\n"
            report += "\n"
        
        if result['suggestions']:
            report += "💡 SUGGESTIONS:\n"
            for suggestion in result['suggestions']:
                report += f"  • {suggestion}\n"
            report += "\n"
        
        report += f"📁 Files Checked: {', '.join(result['files_checked'])}\n"
        
        return report

# Quality control integration for main app
def pre_deployment_check():
    """Run before any deployment"""
    qc = QualityControl()
    result = qc.run_full_quality_check()
    
    if not result['passed']:
        print("❌ DEPLOYMENT BLOCKED - Quality issues found:")
        for error in result['errors']:
            print(f"  • {error}")
        return False
    
    print("✅ Quality check passed - Safe to deploy")
    return True

if __name__ == "__main__":
    qc = QualityControl()
    print(qc.generate_quality_report())
