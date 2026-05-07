"""
Intent Parser Layer - 意图解析层
负责将自然语言任务转换为结构化的工具调用意图
采用槽位提取（slot extraction）方法，比字符串匹配更稳定
"""
from typing import List, Dict, Any
from enum import Enum
import re


class IntentType(Enum):
    """支持的意图类型"""
    write_file = "write_file"
    read_file = "read_file"
    delete_file = "delete_file"
    list_dir = "list_dir"
    run_bash = "run_bash"
    run_python = "run_python"
    finish_task = "finish_task"


class Intent:
    """意图对象 - 包含槽位信息"""
    def __init__(self, intent_type: IntentType, params: Dict[str, Any], description: str):
        self.type = intent_type
        self.params = params
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.type.value,
            "params": self.params,
            "description": self.description
        }


class IntentParser:
    """
    语义解析器 - 将自然语言任务转换为结构化意图
    采用槽位提取方法，比字符串匹配更稳定
    """
    
    # 有效的文件扩展名白名单
    VALID_EXTENSIONS = ["txt", "py", "json", "md", "csv", "html", "js"]
    
    # 动作到模式的映射
    PATTERNS = {
        IntentType.write_file: [
            r"创建.*?文件",
            r"新建.*?文件",
            r"写入.*?内容",
            r"写.*?内容",
            r"写入.*?文件"
        ],
        IntentType.read_file: [
            r"读取.*?文件",
            r"查看.*?文件",
            r"读.*?文件"
        ],
        IntentType.delete_file: [
            r"删除.*?文件",
            r"删除.*?内容"
        ],
        IntentType.list_dir: [
            r"列出.*?目录",
            r"查看.*?目录"
        ],
        IntentType.run_bash: [
            r"执行.*?命令",
            r"运行.*?命令"
        ],
        IntentType.run_python: [
            r"执行.*?代码",
            r"运行.*?代码"
        ]
    }
    
    @staticmethod
    def extract_filename(text: str) -> str:
        """
        提取文件名 - 优先匹配带扩展名的文件名
        """
        # 首先，使用更精确的模式匹配文件名
        # 寻找包含扩展名且前面没有动词的文件名
        # 常见动词前缀
        verbs = ["在", "创建", "读取", "删除", "写入", "查看"]
        verb_pattern = r'(?:%s)' % '|'.join(verbs)
        
        # 尝试匹配文件名
        # 使用正向前瞻和后顾来确保只匹配真正的文件名部分
        # 模式解释：
        # (?:[\u4e00-\u9fa5a-zA-Z0-9_\-]*?) - 可选前缀
        # ([\w\u4e00-\u9fa5_-]+\.(' + '|'.join(IntentParser.VALID_EXTENSIONS) + r')) - 文件名
        extension_pattern = r'(?:[\u4e00-\u9fa5a-zA-Z0-9_\-]*?)' + r'([\w\u4e00-\u9fa5_-]+\.(' + '|'.join(IntentParser.VALID_EXTENSIONS) + r'))'
        match = re.search(extension_pattern, text)
        if match:
            filename = match.group(1)
            
            # 进一步清理文件名
            # 移除常见动词前缀
            prefixes = [
                "在工作区创建", "创建一个", "创建", "读取", "查看", "删除", "新建", "写入",
                "在工作区", "在目录", "目录下的", "文件", "临时文件", "workspace目录下的"
            ]
            for prefix in prefixes:
                if filename.startswith(prefix):
                    filename = filename[len(prefix):].strip()
            
            return filename
            
        # 匹配没有扩展名的文件名（带引号或标识符）
        quoted_pattern = r"['\"](.*?)['\"]"
        match = re.search(quoted_pattern, text)
        if match:
            filename = match.group(1)
            if filename and filename.strip() and '.' not in filename:
                filename += '.txt'  # 默认使用txt扩展名
            return filename
            
        # 兜底方案
        return "default.txt"
    
    @staticmethod
    def extract_content(text: str) -> str:
        """
        提取内容 - 优先匹配引号内的内容
        """
        quoted_pattern = r"['\"](.*?)['\"]"
        match = re.search(quoted_pattern, text)
        if match:
            return match.group(1).strip()
            
        # 匹配 "内容为 xxx" 格式
        content_pattern = r"内容为(.*?)(?:$|，|。|；|、)"
        match = re.search(content_pattern, text)
        if match:
            content = match.group(1).strip()
            if content:
                return content
            
        if "写入" in text:
            write_part = text.split("写入", 1)[1]
            content = re.sub(r'[，。；、]', '', write_part).strip()
            if content:
                return content
                
        return "Hello, World!"
    
    @staticmethod
    def extract_location(text: str) -> str:
        """
        提取位置信息（如工作区、特定目录等）
        """
        if "工作区" in text:
            return "workspace"
        return "workspace"
    
    def extract_intent(self, text: str) -> IntentType:
        """
        识别任务的意图
        """
        text_lower = text.lower()
        
        for intent_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent_type
        
        return IntentType.finish_task
    
    def parse(self, task: str) -> List[Intent]:
        """
        将自然语言任务解析为意图列表
        """
        task = task.strip()
        if not task:
            return [Intent(IntentType.finish_task, {}, "无任务内容")]
        
        # 1. 识别意图
        intent_type = self.extract_intent(task)
        
        # 2. 提取参数
        params = {}
        
        if intent_type in [IntentType.write_file, IntentType.read_file, IntentType.delete_file]:
            filename = self.extract_filename(task)
            params["path"] = f"./pyclaw/sandbox/workspace/{filename}"
            
        if intent_type == IntentType.write_file:
            params["content"] = self.extract_content(task)
        
        elif intent_type == IntentType.run_bash:
            quoted_pattern = r"['\"](.*?)['\"]"
            match = re.search(quoted_pattern, task)
            if match:
                params["cmd"] = match.group(1)
            else:
                params["cmd"] = "echo 'Hello World'"
        
        elif intent_type == IntentType.run_python:
            quoted_pattern = r"['\"](.*?)['\"]"
            match = re.search(quoted_pattern, task)
            if match:
                params["code"] = match.group(1)
            else:
                params["code"] = "print('Hello World')"
        
        # 生成意图对象
        description = self._generate_description(intent_type, params)
        intent = Intent(intent_type, params, description)
        
        return [intent]
    
    def _generate_description(self, intent_type: IntentType, params: Dict[str, Any]) -> str:
        """
        为意图生成描述
        """
        if intent_type == IntentType.write_file:
            filename = params.get("path", "")
            if filename:
                filename = filename.split("/")[-1]
            return f"创建 {filename}"
        
        elif intent_type == IntentType.read_file:
            filename = params.get("path", "")
            if filename:
                filename = filename.split("/")[-1]
            return f"读取 {filename}"
        
        elif intent_type == IntentType.delete_file:
            filename = params.get("path", "")
            if filename:
                filename = filename.split("/")[-1]
            return f"删除 {filename}"
        
        elif intent_type == IntentType.list_dir:
            return "列出目录"
        
        elif intent_type == IntentType.run_bash:
            cmd = params.get("cmd", "")
            return f"执行命令: {cmd[:50]}"
        
        elif intent_type == IntentType.run_python:
            code = params.get("code", "")
            return f"执行代码: {code[:50]}"
        
        return "结束任务"


class TaskCompiler:
    """
    任务编译器 - 将意图转换为可执行步骤
    确保与Execution Contract一致
    """
    
    def compile(self, intent_list: List[Intent]) -> List[Dict[str, Any]]:
        """
        将意图列表编译为可执行步骤
        """
        steps = []
        step_id = 1
        
        for intent in intent_list:
            if intent.type == IntentType.finish_task:
                continue
            
            steps.append({
                "id": step_id,
                "action": intent.type.value,
                "params": intent.params,
                "description": intent.description
            })
            step_id += 1
        
        # 添加任务完成步骤
        steps.append({
            "id": step_id,
            "action": IntentType.finish_task.value,
            "params": {"message": "任务完成"},
            "description": "任务完成"
        })
        
        return steps
