"""
Runtime Trace System - 执行链可视化
让PyClaw的每一步都可追踪和观测
"""
from typing import List, Dict, Any
from datetime import datetime
import json
import os


class TraceRecord:
    """单步执行的详细记录"""
    def __init__(self, step: int, timestamp: datetime, layer: str, component: str,
                 action: str, params: Dict[str, Any], status: str, result: Any,
                 duration: float = 0.0):
        self.step = step
        self.timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        self.layer = layer
        self.component = component
        self.action = action
        self.params = params
        self.status = status  # success / failure / blocked / confirm
        self.result = result
        self.duration = duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "layer": self.layer,
            "component": self.component,
            "action": self.action,
            "params": self.params,
            "status": self.status,
            "result": str(self.result) if isinstance(self.result, dict) else self.result,
            "duration": round(self.duration, 3)
        }


class RuntimeTrace:
    """运行时执行链追踪系统"""
    LAYERS = {
        "planner": "📋 Planner",
        "runtime": "⚙️ Runtime",
        "tool": "🔧 Tool",
        "evaluator": "📊 Evaluator",
        "memory": "🧠 Memory",
        "policy": "🔒 Policy"
    }

    def __init__(self, task: str = "unknown"):
        self.records: List[TraceRecord] = []
        self.task = task
        self.start_time = datetime.now()
        self.end_time = None
        self._step_count = 0

    def record(self, layer: str, component: str, action: str, params: Dict[str, Any],
               status: str, result: Any, duration: float = 0.0):
        self._step_count += 1
        record = TraceRecord(
            step=self._step_count,
            timestamp=datetime.now(),
            layer=layer,
            component=component,
            action=action,
            params=params,
            status=status,
            result=result,
            duration=duration
        )
        self.records.append(record)

    def start(self):
        """记录系统启动"""
        self.record(
            layer="system",
            component="bootstrap",
            action="start",
            params={"task": self.task},
            status="success",
            result="PyClaw v0.7.2启动成功",
            duration=0.0
        )

    def finish(self):
        """记录任务完成"""
        self.end_time = datetime.now()
        total_duration = (self.end_time - self.start_time).total_seconds()
        self.record(
            layer="system",
            component="runtime",
            action="finish",
            params={"total_steps": self._step_count},
            status="success",
            result=f"任务完成，总耗时: {total_duration:.3f}秒",
            duration=total_duration
        )

    def to_json(self) -> str:
        """导出为JSON格式"""
        data = {
            "task": self.task,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S.%f") if self.end_time else None,
            "total_steps": self._step_count,
            "records": [record.to_dict() for record in self.records]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def to_html(self) -> str:
        """导出为HTML可视化页面"""
        html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyClaw 执行链追踪</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
        .stats { display: flex; justify-content: space-around; margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .stat-item { text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
        .timeline { margin-top: 30px; }
        .trace-item { display: flex; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db; transition: all 0.3s; }
        .trace-item:hover { transform: translateX(5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .step-number { min-width: 40px; height: 40px; line-height: 40px; text-align: center; background: #3498db; color: white; border-radius: 50%; font-weight: bold; margin-right: 20px; }
        .trace-content { flex: 1; }
        .trace-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .layer { font-size: 12px; padding: 4px 12px; border-radius: 12px; color: white; font-weight: bold; }
        .layer-system { background: #95a5a6; }
        .layer-planner { background: #34495e; }
        .layer-runtime { background: #27ae60; }
        .layer-tool { background: #f39c12; }
        .layer-evaluator { background: #8e44ad; }
        .layer-memory { background: #16a085; }
        .layer-policy { background: #c0392b; }
        .status { font-size: 12px; padding: 4px 12px; border-radius: 12px; background: #2ecc71; color: white; font-weight: bold; }
        .status-failure { background: #e74c3c; }
        .status-blocked { background: #f39c12; }
        .status-confirm { background: #3498db; }
        .action { font-weight: bold; color: #2c3e50; margin-bottom: 5px; }
        .component { font-size: 12px; color: #7f8c8d; margin-bottom: 5px; }
        .params { font-size: 12px; background: white; padding: 8px; border-radius: 4px; margin-bottom: 5px; overflow-x: auto; }
        .result { font-size: 12px; color: #27ae60; }
        .result-error { color: #e74c3c; }
        .timestamp { font-size: 11px; color: #bdc3c7; margin-top: 5px; }
        .duration { font-size: 11px; color: #9b59b6; margin-left: 10px; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 0; }
        .download-btn { display: block; width: 200px; margin: 30px auto 0; padding: 12px 24px; background: #3498db; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold; transition: background 0.3s; }
        .download-btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PyClaw 执行链追踪</h1>
"""

        # 添加统计信息
        duration = 0.0
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        html += f"""
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{self._step_count}</div>
                <div class="stat-label">总执行步骤</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{round(duration, 3)}</div>
                <div class="stat-label">总耗时(秒)</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(1 for r in self.records if r.layer == 'tool')}</div>
                <div class="stat-label">工具调用</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(1 for r in self.records if r.status == 'failure')}</div>
                <div class="stat-label">失败次数</div>
            </div>
        </div>

        <div class="timeline">
"""

        # 添加详细执行链
        for record in self.records:
            layer_class = record.layer.replace(" ", "-").lower()
            layer_class = f"layer-{layer_class}"
            layer_name = self.LAYERS.get(record.layer, record.layer)
            layer_style = ""

            if record.layer == "system":
                layer_style = 'style="background:#95a5a6"'
            elif record.layer == "planner":
                layer_style = 'style="background:#34495e"'
            elif record.layer == "runtime":
                layer_style = 'style="background:#27ae60"'
            elif record.layer == "tool":
                layer_style = 'style="background:#f39c12"'
            elif record.layer == "evaluator":
                layer_style = 'style="background:#8e44ad"'
            elif record.layer == "memory":
                layer_style = 'style="background:#16a085"'
            elif record.layer == "policy":
                layer_style = 'style="background:#c0392b"'

            status_class = ""
            if record.status == "failure":
                status_class = "status-failure"
            elif record.status == "blocked":
                status_class = "status-blocked"
            elif record.status == "confirm":
                status_class = "status-confirm"

            html += f"""
            <div class="trace-item">
                <div class="step-number">{record.step}</div>
                <div class="trace-content">
                    <div class="trace-header">
                        <div class="layer {layer_class}" {layer_style}>{layer_name}</div>
                        <div class="status {status_class}">{record.status}</div>
                    </div>
                    <div class="action">{record.action}</div>
                    <div class="component">{record.component}</div>
                    <div class="params">
                        <strong>参数:</strong> <pre>{json.dumps(record.params, ensure_ascii=False, indent=2)}</pre>
                    </div>
                    <div class="result {'result-error' if record.status == 'failure' else ''}">
                        <strong>结果:</strong> {record.result}
                    </div>
                    <div class="timestamp">
                        {record.timestamp}
                        <span class="duration">耗时: {record.duration:.3f}秒</span>
                    </div>
                </div>
            </div>
"""

        html += """
        </div>
        <a href="#" class="download-btn" onclick="downloadJSON()">下载JSON文件</a>
    </div>
    <script>
        function downloadJSON() {
            const data = JSON.parse(`""" + json.dumps(json.loads(self.to_json()), ensure_ascii=False) + """`);
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'pyclaw-execution-trace.json';
            a.click();
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""
        return html

    def save(self, filename: str = None):
        """保存追踪结果到文件"""
        if not filename:
            filename = f"trace-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"

        if filename.endswith('.json'):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
        elif filename.endswith('.html'):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.to_html())
        else:
            # 默认保存为HTML
            with open(filename + '.html', 'w', encoding='utf-8') as f:
                f.write(self.to_html())

        print(f"执行链追踪已保存到: {filename}")
