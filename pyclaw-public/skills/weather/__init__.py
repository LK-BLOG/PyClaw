"""
🌤️ Weather Skill for PyClaw
查询全球城市天气的 Skill
"""
import httpx
from dataclasses import dataclass
from typing import Dict, Any

from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "WeatherSkill"


@dataclass
class WeatherTool:
    """查询城市天气"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_weather",
            description="查询指定城市的当前天气、温度、湿度等信息",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如 '北京'、'上海'、'Tokyo'、'New York'"
                    },
                    "unit": {
                        "type": "string",
                        "description": "温度单位：'c' 摄氏度（默认），'f' 华氏度",
                        "default": "c"
                    }
                },
                "required": ["city"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        city = params.get("city", "")
        unit = params.get("unit", "c")
        
        if not city:
            return ToolResult(success=False, content="", error="请指定城市名称")
        
        try:
            # 使用 wttr.in 免费天气 API
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"https://wttr.in/{city}?format=j1"
                response = await client.get(url)
                data = response.json()
            
            current = data["current_condition"][0]
            weather_desc = current["weatherDesc"][0]["value"]
            temp = current["temp_C"] if unit == "c" else current["temp_F"]
            humidity = current["humidity"]
            windspeed = current["windspeedKmph"]
            
            unit_label = "°C" if unit == "c" else "°F"
            
            result = f"""🌤️ {city} 天气

当前: {weather_desc}
温度: {temp}{unit_label}
湿度: {humidity}%
风速: {windspeed} km/h

数据来源: wttr.in
"""
            return ToolResult(success=True, content=result)
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"查询天气失败: {str(e)}")


class WeatherSkill:
    """
    🌤️ Weather Skill for PyClaw
    查询全球城市天气
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="Weather",
            description="查询全球城市的实时天气、温度、湿度、风速等信息",
            author="PyClaw Team",
            version="1.0.0",
            tags=["weather", "weather", "工具"],
            website="https://github.com/pyclaw/skill-weather"
        )
    
    def get_tools(self):
        return [WeatherTool()]
    
    async def initialize(self) -> bool:
        print("[Weather Skill] 天气 Skill 初始化完成")
        return True
    
    async def cleanup(self) -> None:
        print("[Weather Skill] 天气 Skill 已卸载")
