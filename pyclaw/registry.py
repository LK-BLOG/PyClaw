"""
PyClaw USB 系统注册中心（API Freeze）

负责统一管理系统组件的注册和获取：
- 工具（Tools）
- 规划器（Planners）
- 评估器（Evaluators）
- 其他系统组件

这是系统的唯一组件访问入口。
"""
class Registry:
    """
    系统组件注册表（单例模式）
    """
    
    def __init__(self):
        self.tools = {}
        self.planners = {}
        self.evaluators = {}
        
    # ---------- TOOL 管理 ----------
    def register_tool(self, name, tool):
        """
        注册工具
        
        参数：
            name: 工具名称
            tool: 工具实例
        """
        self.tools[name] = tool
        
    def get_tool(self, name):
        """
        获取工具
        
        参数：
            name: 工具名称
            
        返回：
            工具实例或 None
        """
        return self.tools.get(name)
        
    # ---------- PLANNER 管理 ----------
    def register_planner(self, name, planner):
        """
        注册规划器
        
        参数：
            name: 规划器名称
            planner: 规划器实例
        """
        self.planners[name] = planner
        
    def get_planner(self, name):
        """
        获取规划器
        
        参数：
            name: 规划器名称
            
        返回：
            规划器实例或 None
        """
        return self.planners.get(name)
        
    # ---------- EVALUATOR 管理 ----------
    def register_evaluator(self, name, evaluator):
        """
        注册评估器
        
        参数：
            name: 评估器名称
            evaluator: 评估器实例
        """
        self.evaluators[name] = evaluator
        
    def get_evaluator(self, name):
        """
        获取评估器
        
        参数：
            name: 评估器名称
            
        返回：
            评估器实例或 None
        """
        return self.evaluators.get(name)
        
    # ---------- 辅助方法 ----------
    def get_all_tools(self):
        """获取所有注册的工具"""
        return self.tools
    
    def get_all_planners(self):
        """获取所有注册的规划器"""
        return self.planners
    
    def get_all_evaluators(self):
        """获取所有注册的评估器"""
        return self.evaluators
    
    def clear_all(self):
        """清除所有注册信息"""
        self.tools.clear()
        self.planners.clear()
        self.evaluators.clear()
