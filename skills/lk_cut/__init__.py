"""
✂️ LK-Cut Skill for PyClaw
骆戡的视频剪辑偏好工具 - 支持视频分割、合并、转码、水印、变速等功能
"""
import os
import subprocess
import shutil
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path

from pyclaw.skill import SkillMetadata
from pyclaw.pyclaw_types import ToolDefinition, ToolResult


# Skill 配置
SKILL_CLASS = "LKCutSkill"


def _check_ffmpeg() -> bool:
    """检查 ffmpeg 是否可用"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return True
    except:
        return False


def _format_time(seconds: float) -> str:
    """秒数转 HH:MM:SS 格式"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _parse_time(time_str: str) -> float:
    """时间字符串转秒数"""
    try:
        if ':' in time_str:
            parts = list(map(float, time_str.split(':')))
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return float(time_str)
    except:
        return 0


# ==========================================
# 🔧 LK-Cut 核心工具
# ==========================================

@dataclass
class VideoInfoTool:
    """获取视频详细信息"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_info",
            description="获取视频的详细信息：分辨率、时长、码率、编码格式、音频参数等",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "视频文件路径"
                    }
                },
                "required": ["input"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg：sudo apt install ffmpeg / brew install ffmpeg")
        
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_format', '-show_streams', input_file],
                capture_output=True, text=True, timeout=30
            )
            
            import json
            info = json.loads(result.stdout)
            
            video_stream = None
            audio_stream = None
            
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            format_info = info.get('format', {})
            duration = float(format_info.get('duration', 0))
            size = int(format_info.get('size', 0))
            
            lines = ["📹 视频信息\n", f"📄 文件: {os.path.basename(input_file)}"]
            lines.append(f"📍 路径: {os.path.abspath(input_file)}")
            lines.append(f"📦 大小: {size // (1024**2)} MB ({size:,} bytes)")
            lines.append(f"⏱️  时长: {_format_time(duration)} ({duration:.1f} 秒)")
            lines.append(f"📊 码率: {int(format_info.get('bit_rate', 0)) // 1000} kbps")
            lines.append("")
            
            if video_stream:
                lines.append("🎬 视频流:")
                lines.append(f"  编码: {video_stream.get('codec_name', 'N/A')}")
                lines.append(f"  分辨率: {video_stream.get('width', 0)} x {video_stream.get('height', 0)}")
                lines.append(f"  帧率: {video_stream.get('r_frame_rate', 'N/A').split('/')[0]} fps")
                lines.append(f"  像素格式: {video_stream.get('pix_fmt', 'N/A')}")
                lines.append("")
            
            if audio_stream:
                lines.append("🎵 音频流:")
                lines.append(f"  编码: {audio_stream.get('codec_name', 'N/A')}")
                lines.append(f"  采样率: {audio_stream.get('sample_rate', 0)} Hz")
                lines.append(f"  声道: {audio_stream.get('channels', 0)}")
                lines.append(f"  比特率: {int(audio_stream.get('bit_rate', 0)) // 1000} kbps")
            
            return ToolResult(success=True, content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(success=False, content="", error=f"获取视频信息失败: {str(e)}")


@dataclass
class VideoCutTool:
    """视频剪切（骆戡偏好：快速分割片段）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_cut",
            description="快速剪切视频片段（无损模式优先），支持时间点或时间段",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "start": {
                        "type": "string",
                        "description": "开始时间，格式：HH:MM:SS 或 秒数"
                    },
                    "end": {
                        "type": "string",
                        "description": "结束时间，格式：HH:MM:SS 或 秒数"
                    },
                    "duration": {
                        "type": "string",
                        "description": "持续时长（可选，与end二选一）"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出文件路径，可选"
                    },
                    "fast": {
                        "type": "boolean",
                        "description": "快速模式（无损复制，默认true）",
                        "default": True
                    }
                },
                "required": ["input", "start"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        start = params.get("start", "")
        end = params.get("end", "")
        duration = params.get("duration", "")
        output = params.get("output", "").strip()
        fast = params.get("fast", True)
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        # 生成默认输出文件名
        if not output:
            name, ext = os.path.splitext(input_file)
            output = f"{name}_cut{ext}"
        
        # 构建命令
        cmd = ['ffmpeg', '-i', input_file, '-ss', start]
        
        if end:
            cmd.extend(['-to', end])
        elif duration:
            cmd.extend(['-t', duration])
        
        if fast:
            cmd.extend(['-c', 'copy'])  # 无损快速模式
        
        cmd.append(output)
        
        try:
            lines = ["✂️  LK-Cut 视频剪切\n", f"📥 输入: {input_file}"]
            lines.append(f"📤 输出: {output}")
            lines.append(f"⏱️  开始: {start}")
            if end: lines.append(f"⏱️  结束: {end}")
            if duration: lines.append(f"⏱️  时长: {duration}")
            lines.append(f"⚡ 模式: {'快速(无损)' if fast else '重新编码'}")
            lines.append("")
            lines.append("🔄 正在处理...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // (1024**2)
                lines.append(f"")
                lines.append(f"✅ 剪切完成!")
                lines.append(f"📦 输出大小: {out_size} MB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"剪切失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"剪切失败: {str(e)}")


@dataclass
class VideoMergeTool:
    """视频合并（骆戡偏好：批量合并多个片段）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_merge",
            description="合并多个视频文件为一个视频，支持任意数量输入",
            parameters={
                "type": "object",
                "properties": {
                    "inputs": {
                        "type": "array",
                        "description": "视频文件路径列表，按顺序合并",
                        "items": {"type": "string"}
                    },
                    "output": {
                        "type": "string",
                        "description": "输出文件路径"
                    },
                    "fast": {
                        "type": "boolean",
                        "description": "快速模式（无损，需相同编码，默认true）",
                        "default": True
                    }
                },
                "required": ["inputs"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        inputs = params.get("inputs", [])
        output = params.get("output", "").strip()
        fast = params.get("fast", True)
        
        if not inputs:
            return ToolResult(success=False, content="", error="请指定要合并的视频文件")
        
        for f in inputs:
            if not os.path.exists(f):
                return ToolResult(success=False, content="", error=f"文件不存在: {f}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        if not output:
            first_dir = os.path.dirname(inputs[0]) or "."
            output = os.path.join(first_dir, "LK_Cut_Merged.mp4")
        
        # 创建文件列表供ffmpeg使用
        list_file = output + ".txt"
        with open(list_file, 'w') as f:
            for inp in inputs:
                abs_path = os.path.abspath(inp).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        try:
            lines = ["🔗 LK-Cut 视频合并\n", f"📹 合并 {len(inputs)} 个视频:"]
            for i, inp in enumerate(inputs, 1):
                lines.append(f"  {i}. {os.path.basename(inp)}")
            lines.append("")
            lines.append(f"📤 输出: {output}")
            lines.append(f"⚡ 模式: {'快速(无损)' if fast else '重新编码'}")
            lines.append("")
            lines.append("🔄 正在合并...")
            
            cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file]
            if fast:
                cmd.extend(['-c', 'copy'])
            cmd.append(output)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // (1024**2)
                lines.append("")
                lines.append(f"✅ 合并完成!")
                lines.append(f"📦 输出大小: {out_size} MB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                
                # 清理临时文件
                try: os.remove(list_file)
                except: pass
                
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"合并失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"合并失败: {str(e)}")


@dataclass
class VideoConvertTool:
    """视频转码（骆戡偏好：快速转码预设）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_convert",
            description="视频格式/码率转换，支持多种预设：小体积、高质量、B站友好、抖音友好",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出文件路径，可选"
                    },
                    "preset": {
                        "type": "string",
                        "description": "预设方案：small(小体积), high(高质量), bilibili(B站友好), douyin(抖音友好), 4k, 1080p, 720p",
                        "enum": ["small", "high", "bilibili", "douyin", "4k", "1080p", "720p"]
                    },
                    "resolution": {
                        "type": "string",
                        "description": "自定义分辨率，如 1920x1080，可选"
                    },
                    "bitrate": {
                        "type": "string",
                        "description": "自定义码率，如 5M，可选"
                    },
                    "format": {
                        "type": "string",
                        "description": "输出格式：mp4, mov, avi, mkv, webm, gif, mp3（仅音频）",
                        "enum": ["mp4", "mov", "avi", "mkv", "webm", "gif", "mp3"]
                    }
                },
                "required": ["input"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        output = params.get("output", "").strip()
        preset = params.get("preset", "")
        resolution = params.get("resolution", "")
        bitrate = params.get("bitrate", "")
        format_type = params.get("format", "")
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        # 预设配置
        presets = {
            "small": {"vcodec": "libx264", "crf": 28, "preset": "fast", "audio": "aac", "ab": "128k"},
            "high": {"vcodec": "libx264", "crf": 18, "preset": "slow", "audio": "aac", "ab": "320k"},
            "bilibili": {"vcodec": "libx264", "crf": 23, "preset": "medium", "audio": "aac", "ab": "192k", "maxrate": "6M", "bufsize": "12M"},
            "douyin": {"vcodec": "libx264", "crf": 22, "preset": "medium", "audio": "aac", "ab": "128k", "ar": "44100"},
            "4k": {"vcodec": "libx264", "crf": 20, "preset": "slow", "s": "3840x2160"},
            "1080p": {"vcodec": "libx264", "crf": 23, "preset": "medium", "s": "1920x1080"},
            "720p": {"vcodec": "libx264", "crf": 23, "preset": "fast", "s": "1280x720"},
        }
        
        # 生成输出文件名
        if not output:
            name, ext = os.path.splitext(input_file)
            if preset:
                output = f"{name}_{preset}.mp4"
            elif format_type:
                output = f"{name}.{format_type}"
            else:
                output = f"{name}_converted.mp4"
        
        # 仅音频模式
        if format_type == "mp3":
            cmd = ['ffmpeg', '-i', input_file, '-vn', '-acodec', 'libmp3lame', '-q:a', '2', output]
        elif format_type == "gif":
            cmd = ['ffmpeg', '-i', input_file, '-vf', 'fps=10,scale=480:-1:flags=lanczos', '-c:v', 'gif', output]
        else:
            # 视频转码
            cmd = ['ffmpeg', '-i', input_file]
            
            # 应用预设
            if preset and preset in presets:
                p = presets[preset]
                if 'vcodec' in p: cmd.extend(['-c:v', p['vcodec']])
                if 'crf' in p: cmd.extend(['-crf', str(p['crf'])])
                if 'preset' in p: cmd.extend(['-preset', p['preset']])
                if 'audio' in p: cmd.extend(['-c:a', p['audio']])
                if 'ab' in p: cmd.extend(['-ab', p['ab']])
                if 'maxrate' in p: cmd.extend(['-maxrate', p['maxrate']])
                if 'bufsize' in p: cmd.extend(['-bufsize', p['bufsize']])
                if 's' in p: cmd.extend(['-s', p['s']])
                if 'ar' in p: cmd.extend(['-ar', p['ar']])
            else:
                # 默认预设
                cmd.extend(['-c:v', 'libx264', '-crf', '23', '-preset', 'medium', '-c:a', 'aac', '-ab', '192k'])
            
            # 自定义参数覆盖
            if resolution: cmd.extend(['-s', resolution])
            if bitrate: cmd.extend(['-b:v', bitrate])
            
            cmd.append(output)
        
        try:
            lines = ["🔄 LK-Cut 视频转码\n", f"📥 输入: {input_file}"]
            lines.append(f"📤 输出: {output}")
            if preset: lines.append(f"🎯 预设: {preset}")
            if resolution: lines.append(f"📐 分辨率: {resolution}")
            if bitrate: lines.append(f"📊 码率: {bitrate}")
            if format_type: lines.append(f"📁 格式: {format_type}")
            lines.append("")
            lines.append("🔄 正在转码...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // (1024**2)
                in_size = os.path.getsize(input_file) // (1024**2)
                ratio = (1 - out_size / in_size) * 100 if in_size > 0 else 0
                
                lines.append("")
                lines.append(f"✅ 转码完成!")
                lines.append(f"📦 输入大小: {in_size} MB")
                lines.append(f"📦 输出大小: {out_size} MB")
                if ratio > 0:
                    lines.append(f"📉 压缩率: -{ratio:.1f}%")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"转码失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"转码失败: {str(e)}")


@dataclass
class VideoSpeedTool:
    """视频变速（骆戡偏好：快速变速）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_speed",
            description="调整视频播放速度，支持加速和减速，可同时调整音频",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "speed": {
                        "type": "number",
                        "description": "速度倍数：0.5(减半), 2(加倍), 4(4倍速), 0.25(1/4速)等"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出文件路径，可选"
                    },
                    "audio_sync": {
                        "type": "boolean",
                        "description": "同时调整音频速度（默认true）",
                        "default": True
                    }
                },
                "required": ["input", "speed"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        speed = params.get("speed", 1.0)
        output = params.get("output", "").strip()
        audio_sync = params.get("audio_sync", True)
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if speed <= 0:
            return ToolResult(success=False, content="", error="速度必须大于0")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        if not output:
            name, ext = os.path.splitext(input_file)
            output = f"{name}_x{speed}{ext}"
        
        try:
            lines = ["⏩ LK-Cut 视频变速\n", f"📥 输入: {input_file}"]
            lines.append(f"📤 输出: {output}")
            lines.append(f"⚡ 速度: {speed}x")
            lines.append(f"🔊 音频同步: {'是' if audio_sync else '否'}")
            lines.append("")
            lines.append("🔄 正在处理...")
            
            # 构建滤镜
            v_filter = f"setpts={1/speed}*PTS"
            a_filter = f"atempo={speed}" if audio_sync else "anull"
            
            cmd = ['ffmpeg', '-i', input_file, '-filter:v', v_filter, '-filter:a', a_filter, output]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // (1024**2)
                lines.append("")
                lines.append(f"✅ 变速完成!")
                lines.append(f"📦 输出大小: {out_size} MB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"变速失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"变速失败: {str(e)}")


@dataclass
class VideoWatermarkTool:
    """添加水印（骆戡偏好：自定义水印位置）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_watermark",
            description="给视频添加图片水印或文字水印，支持9个位置和透明度调节",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "watermark": {
                        "type": "string",
                        "description": "水印图片路径 或 文字内容"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出文件路径，可选"
                    },
                    "position": {
                        "type": "string",
                        "description": "水印位置：center, top-left, top-right, bottom-left, bottom-right, top, bottom, left, right",
                        "enum": ["center", "top-left", "top-right", "bottom-left", "bottom-right", "top", "bottom", "left", "right"],
                        "default": "bottom-right"
                    },
                    "opacity": {
                        "type": "number",
                        "description": "透明度：0-1，默认0.8",
                        "default": 0.8
                    },
                    "scale": {
                        "type": "number",
                        "description": "水印缩放比例：0.1-1.0，默认

@dataclass
class VideoGIFTool:
    """制作GIF动图（骆戡偏好：快速制作）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_make_gif",
            description="将视频片段转换为GIF动图，支持自定义时长和尺寸",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出GIF文件路径，可选"
                    },
                    "start": {
                        "type": "string",
                        "description": "开始时间，格式：HH:MM:SS 或 秒数，默认开头",
                        "default": "0"
                    },
                    "duration": {
                        "type": "string",
                        "description": "GIF时长，格式：HH:MM:SS 或 秒数，默认5秒",
                        "default": "5"
                    },
                    "fps": {
                        "type": "integer",
                        "description": "GIF帧率，默认15",
                        "default": 15
                    },
                    "width": {
                        "type": "integer",
                        "description": "GIF宽度（高度自动缩放），默认480",
                        "default": 480
                    }
                },
                "required": ["input"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        output = params.get("output", "").strip()
        start = params.get("start", "0")
        duration = params.get("duration", "5")
        fps = params.get("fps", 15)
        width = params.get("width", 480)
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        if not output:
            name, _ = os.path.splitext(input_file)
            output = f"{name}.gif"
        
        try:
            lines = ["🎬 LK-Cut 制作GIF\n", f"📥 输入: {input_file}"]
            lines.append(f"📤 输出: {output}")
            lines.append(f"⏱️  开始时间: {start}")
            lines.append(f"⏱️  时长: {duration} 秒")
            lines.append(f"🎞️  帧率: {fps} fps")
            lines.append(f"📐 宽度: {width} px")
            lines.append("")
            lines.append("🔄 正在制作GIF...")
            
            cmd = [
                'ffmpeg', '-ss', start, '-t', duration, '-i', input_file,
                '-vf', f'fps={fps},scale={width}:-1:flags=lanczos',
                '-c:v', 'gif', output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // 1024
                lines.append("")
                lines.append(f"✅ GIF制作完成!")
                lines.append(f"📦 文件大小: {out_size} KB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"制作GIF失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"制作GIF失败: {str(e)}")


@dataclass
class VideoSubtitleTool:
    """添加字幕（骆戡偏好：烧录字幕）"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_add_subtitle",
            description="给视频烧录字幕，支持SRT/ASS格式字幕文件",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "字幕文件路径 (.srt, .ass)"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出视频文件路径，可选"
                    },
                    "font_size": {
                        "type": "integer",
                        "description": "字幕字号，默认24",
                        "default": 24
                    },
                    "font_color": {
                        "type": "string",
                        "description": "字幕颜色，默认white",
                        "default": "white"
                    },
                    "position": {
                        "type": "string",
                        "description": "字幕位置：bottom, center, top",
                        "enum": ["bottom", "center", "top"],
                        "default": "bottom"
                    }
                },
                "required": ["input", "subtitle"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        subtitle = params.get("subtitle", "").strip()
        output = params.get("output", "").strip()
        font_size = params.get("font_size", 24)
        font_color = params.get("font_color", "white")
        position = params.get("position", "bottom")
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not os.path.exists(subtitle):
            return ToolResult(success=False, content="", error=f"字幕文件不存在: {subtitle}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        if not output:
            name, ext = os.path.splitext(input_file)
            output = f"{name}_subtitled{ext}"
        
        # 字幕位置滤镜
        v_positions = {
            "bottom": "y=h-line_h-20",
            "center": "y=(h-text_h)/2",
            "top": "y=20"
        }
        
        try:
            lines = ["📝 LK-Cut 添加字幕\n", f"📥 输入: {input_file}"]
            lines.append(f"📄 字幕: {subtitle}")
            lines.append(f"📤 输出: {output}")
            lines.append(f"🔤 字号: {font_size}")
            lines.append(f"🎨 颜色: {font_color}")
            lines.append(f"📍 位置: {position}")
            lines.append("")
            lines.append("🔄 正在烧录字幕...")
            
            sub_ext = os.path.splitext(subtitle)[1].lower()
            
            if sub_ext == '.srt':
                cmd = [
                    'ffmpeg', '-i', input_file,
                    '-vf',
                    f"subtitles='{subtitle}':force_style='FontSize={font_size},PrimaryColour=&HFFFFFF'",
                    output
                ]
            else:  # ASS
                cmd = [
                    'ffmpeg', '-i', input_file, '-vf', f"ass='{subtitle}'", output
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // (1024**2)
                lines.append("")
                lines.append(f"✅ 字幕烧录完成!")
                lines.append(f"📦 输出大小: {out_size} MB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"添加字幕失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"添加字幕失败: {str(e)}")


@dataclass
class VideoRotateTool:
    """旋转/翻转视频"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_rotate",
            description="旋转或翻转视频，支持90/180/270度旋转，水平/垂直翻转",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出视频文件路径，可选"
                    },
                    "mode": {
                        "type": "string",
                        "description": "旋转模式：clockwise(顺时针90), counterclockwise(逆时针90), 180, hflip(水平翻转), vflip(垂直翻转)",
                        "enum": ["clockwise", "counterclockwise", "180", "hflip", "vflip"],
                        "default": "clockwise"
                    },
                    "fast": {
                        "type": "boolean",
                        "description": "快速模式（旋转元数据，不重新编码），默认true",
                        "default": True
                    }
                },
                "required": ["input"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        output = params.get("output", "").strip()
        mode = params.get("mode", "clockwise")
        fast = params.get("fast", True)
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        if not output:
            name, ext = os.path.splitext(input_file)
            output = f"{name}_rotated{ext}"
        
        # 旋转滤镜
        transpose_map = {
            "clockwise": "transpose=1",
            "counterclockwise": "transpose=2",
            "180": "transpose=1,transpose=1",
            "hflip": "hflip",
            "vflip": "vflip"
        }
        
        try:
            lines = ["🔄 LK-Cut 旋转视频\n", f"📥 输入: {input_file}"]
            lines.append(f"📤 输出: {output}")
            lines.append(f"🎯 模式: {mode}")
            lines.append(f"⚡ 快速模式: {'是' if fast else '否'}")
            lines.append("")
            lines.append("🔄 正在旋转...")
            
            if fast and mode in ["clockwise", "counterclockwise", "180"]:
                # 元数据旋转（快速，不重新编码）
                rotate_map = {
                    "clockwise": "90",
                    "counterclockwise": "270",
                    "180": "180"
                }
                cmd = ['ffmpeg', '-i', input_file, '-c', 'copy', '-metadata:s:v', f'rotate={rotate_map[mode]}', output]
            else:
                # 滤镜旋转（重新编码）
                cmd = ['ffmpeg', '-i', input_file, '-vf', transpose_map[mode], output]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // (1024**2)
                lines.append("")
                lines.append(f"✅ 旋转完成!")
                lines.append(f"📦 输出大小: {out_size} MB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"旋转失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"旋转失败: {str(e)}")


@dataclass
class VideoCropTool:
    """裁剪视频画面"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_crop",
            description="裁剪视频画面尺寸，支持多种预设比例和自定义尺寸",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出视频文件路径，可选"
                    },
                    "preset": {
                        "type": "string",
                        "description": "裁剪预设：1:1, 4:3, 16:9, 9:16(抖音竖屏), 21:9(宽屏)",
                        "enum": ["1:1", "4:3", "16:9", "9:16", "21:9"]
                    },
                    "x": {
                        "type": "integer",
                        "description": "裁剪起始X坐标（左上角）"
                    },
                    "y": {
                        "type": "integer",
                        "description": "裁剪起始Y坐标（左上角）"
                    },
                    "width": {
                        "type": "integer",
                        "description": "裁剪宽度"
                    },
                    "height": {
                        "type": "integer",
                        "description": "裁剪高度"
                    }
                },
                "required": ["input"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        output = params.get("output", "").strip()
        preset = params.get("preset", "")
        x = params.get("x", 0)
        y = params.get("y", 0)
        width = params.get("width", 0)
        height = params.get("height", 0)
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        if not output:
            name, ext = os.path.splitext(input_file)
            output = f"{name}_cropped{ext}"
        
        try:
            lines = ["✂️  LK-Cut 裁剪视频\n", f"📥 输入: {input_file}"]
            lines.append(f"📤 输出: {output}")
            
            if preset:
                lines.append(f"🎯 预设比例: {preset}")
                # 获取视频原始尺寸
                probe = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-print_format', 'json', 
                     '-show_streams', input_file],
                    capture_output=True, text=True, timeout=30
                )
                
                import json
                info = json.loads(probe.stdout)
                video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
                orig_w = int(video_stream['width'])
                orig_h = int(video_stream['height'])
                
                # 计算裁剪尺寸（居中裁剪）
                ratios = {
                    "1:1": 1.0,
                    "4:3": 4/3,
                    "16:9": 16/9,
                    "9:16": 9/16,
                    "21:9": 21/9
                }
                ratio = ratios.get(preset, 16/9)
                target_w = min(orig_w, int(orig_h * ratio))
                target_h = min(orig_h, int(orig_w / ratio))
                target_x = (orig_w - target_w) // 2
                target_y = (orig_h - target_h) // 2
                crop_filter = f"crop={target_w}:{target_h}:{target_x}:{target_y}"
            else:
                if width <= 0 or height <= 0:
                    return ToolResult(success=False, content="", error="请指定裁剪尺寸 width 和 height")
                lines.append(f"📍 位置: ({x}, {y})")
                lines.append(f"📐 尺寸: {width} x {height}")
                crop_filter = f"crop={width}:{height}:{x}:{y}"
            
            lines.append("")
            lines.append("🔄 正在裁剪...")
            
            cmd = ['ffmpeg', '-i', input_file, '-vf', crop_filter, output]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output):
                out_size = os.path.getsize(output) // (1024**2)
                lines.append("")
                lines.append(f"✅ 裁剪完成!")
                lines.append(f"📦 输出大小: {out_size} MB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
                
                return ToolResult(success=True, content="\n".join(lines))
            else:
                return ToolResult(success=False, content="", error=f"裁剪失败: {result.stderr[-500:]}")
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"裁剪失败: {str(e)}")


@dataclass
class VideoThumbnailTool:
    """生成视频缩略图"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="video_thumbnail",
            description="生成视频缩略图，支持在指定时间点截取",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入视频文件路径"
                    },
                    "output": {
                        "type": "string",
                        "description": "输出图片路径，可选"
                    },
                    "time": {
                        "type": "string",
                        "description": "截取时间点，格式HH:MM:SS或秒数，默认1秒",
                        "default": "1"
                    },
                    "width": {
                        "type": "integer",
                        "description": "图片宽度，默认1280",
                        "default": 1280
                    },
                    "count": {
                        "type": "integer",
                        "description": "生成多张缩略图（1-9），默认1张",
                        "default": 1
                    }
                },
                "required": ["input"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_file = params.get("input", "").strip()
        output = params.get("output", "").strip()
        time_pos = params.get("time", "1")
        width = params.get("width", 1280)
        count = params.get("count", 1)
        
        if not os.path.exists(input_file):
            return ToolResult(success=False, content="", error=f"文件不存在: {input_file}")
        
        if not _check_ffmpeg():
            return ToolResult(success=False, content="", error="需要安装 ffmpeg")
        
        if not output:
            name, _ = os.path.splitext(input_file)
            if count > 1:
                output = f"{name}_thumbnail_%02d.jpg"
            else:
                output = f"{name}_thumbnail.jpg"
        
        try:
            lines = ["🖼️  LK-Cut 生成缩略图\n", f"📥 输入: {input_file}"]
            lines.append(f"📤 输出: {output}")
            lines.append(f"⏱️  时间点: {time_pos}")
            lines.append(f"📐 宽度: {width} px")
            lines.append(f"🖼️  数量: {count} 张")
            lines.append("")
            lines.append("🔄 正在生成...")
            
            if count > 1:
                # 多张缩略图：平均分布时间
                # 先获取时长
                probe = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-print_format', 'json', 
                     '-show_format', input_file],
                    capture_output=True, text=True, timeout=30
                )
                import json
                info = json.loads(probe.stdout)
                duration = float(info['format']['duration'])
                
                # 生成时间点
                for i in range(count):
                    t = (i + 1) * duration / (count + 1)
                    out_file = output.replace('%02d', f'{i+1:02d}') if '%02d' in output else output.replace('.jpg', f'_{i+1:02d}.jpg')
                    cmd = ['ffmpeg', '-ss', str(t), '-i', input_file, '-vframes', '1', '-vf', f'scale={width}:-1', '-q:v', '2', out_file]
                    subprocess.run(cmd, capture_output=True, timeout=30)
            else:
                # 单张缩略图
                cmd = ['ffmpeg', '-ss', time_pos, '-i', input_file, '-vframes', '1', '-vf', f'scale={width}:-1', '-q:v', '2', output]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # 检查输出
            if count > 1:
                base_out = output.replace('%02d', '*') if '%02d' in output else output
                files = [f for f in os.listdir(os.path.dirname(output) or '.') if os.path.basename(output).replace('%02d', '') in f]
                if len(files) > 0:
                    total_size = sum(os.path.getsize(os.path.join(os.path.dirname(output) or '.', f)) for f in files)
                    lines.append("")
                    lines.append(f"✅ 缩略图生成完成!")
                    lines.append(f"🖼️  生成: {len(files)} 张")
                    lines.append(f"📦 总大小: {total_size // 1024} KB")
                    lines.append(f"📍 保存到: {os.path.abspath(os.path.dirname(output) or '.')}")
            elif os.path.exists(output):
                out_size = os.path.getsize(output) // 1024
                lines.append("")
                lines.append(f"✅ 缩略图生成完成!")
                lines.append(f"📦 大小: {out_size} KB")
                lines.append(f"📍 保存到: {os.path.abspath(output)}")
            else:
                return ToolResult(success=False, content="", error=f"缩略图生成失败")
            
            return ToolResult(success=True, content="\n".join(lines))
                
        except Exception as e:
            return ToolResult(success=False, content="", error=f"生成缩略图失败: {str(e)}")


# ==========================================
# 🎬 LK-Cut Skill 主类
# ==========================================

class LKCutSkill:
    """
    ✂️ LK-Cut Skill for PyClaw
    骆戡的视频剪辑偏好工具 - 专业视频处理工具集
    
    包含12个核心工具：
    - video_info: 获取视频信息
    - video_cut: 剪切视频片段
    - video_merge: 合并多个视频
    - video_convert: 视频转码/格式转换
    - video_speed: 调整播放速度
    - video_watermark: 添加图片/文字水印
    - video_extract_audio: 提取音频
    - video_extract_frames: 提取帧保存为图片
    - video_make_gif: 制作GIF动图
    - video_add_subtitle: 烧录字幕
    - video_rotate: 旋转/翻转视频
    - video_crop: 裁剪视频画面
    - video_thumbnail: 生成缩略图
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="LK-Cut",
            description="骆戡的视频剪辑偏好工具集 - 支持剪切、合并、转码、变速、水印、字幕、GIF等12种视频处理功能",
            author="骆戡",
            version="1.0.0",
            tags=["video", "ffmpeg", "cut", "merge", "watermark", "gif", "视频剪辑"],
            website=""
        )
    
    def get_tools(self):
        return [
            VideoInfoTool(),
            VideoCutTool(),
            VideoMergeTool(),
            VideoConvertTool(),
            VideoSpeedTool(),
            VideoWatermarkTool(),
            VideoExtractAudioTool(),
            VideoExtractFramesTool(),
            VideoGIFTool(),
            VideoSubtitleTool(),
            VideoRotateTool(),
            VideoCropTool(),
            VideoThumbnailTool()
        ]
    
    async def initialize(self) -> bool:
        print("[LK-Cut Skill] ✂️  骆戡的视频剪辑工具初始化...")
        if _check_ffmpeg():
            print("[LK-Cut Skill] ✅ ffmpeg 已找到，准备就绪")
        else:
            print("[LK-Cut Skill] ⚠️  ffmpeg 未安装，部分功能可能不可用")
            print("[LK-Cut Skill] 💡  安装命令: sudo apt install ffmpeg / brew install ffmpeg")
        print(f"[LK-Cut Skill] 🎯  已注册 {len(self.get_tools())} 个视频处理工具")
        return True
    
    async def cleanup(self) -> None:
        print("[LK-Cut Skill] 视频剪辑工具已卸载")

# 导出 Skill 类
SKILL_CLASS = LKCutSkill
