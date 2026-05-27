---
name: lk_cut
description: LK-Cut技能 - 专业视频剪辑和处理工具，支持剪切、合并、转码、水印、音频提取等功能
---

# ✂️ LK-Cut技能

LK-Cut是PyClaw的专业视频剪辑和处理技能，提供13种强大的视频处理功能，专门为骆戡优化，符合他的剪辑偏好和习惯。

## 🎯 核心功能

### 视频信息获取
- 详细分析视频文件信息
- 获取视频分辨率、帧率、编码格式
- 检查视频流和音频流信息

### 视频编辑功能
- **剪切视频**：精确剪切视频片段
- **合并视频**：支持多个视频文件合并
- **格式转换**：视频转码和格式转换
- **变速处理**：调整视频播放速度
- **添加水印**：支持文字和图片水印
- **字幕处理**：添加字幕到视频中
- **视频旋转**：旋转和翻转视频

### 内容提取功能
- **音频提取**：提取视频中的音频为MP3/AAC/WAV/FLAC格式
- **帧提取**：按时间间隔提取视频帧保存为图片

### 其他功能
- **制作GIF**：将视频片段转换为GIF动图
- **裁剪画面**：裁剪视频画面尺寸
- **缩略图**：生成视频缩略图

## 📦 依赖库

- **FFmpeg** - 视频处理核心依赖
- **python-pptx** - PPT制作功能依赖（可选）

## 🔐 Sudo密码说明（仅本地/U盘版）

对于需要系统权限的操作（如安装依赖）：
- **加密密码：** `574263`
- **解密方法：** 每个数字减 1
- **GitHub 版不需要此密码**

## 🛠️ 工具列表

### 视频信息工具
```json
{
  "name": "video_info",
  "description": "获取视频详细信息，包括分辨率、帧率、编码格式等",
  "parameters": {
    "input": "输入视频文件路径"
  }
}
```

### 视频剪切工具
```json
{
  "name": "video_cut",
  "description": "剪切视频片段，支持精确的时间控制",
  "parameters": {
    "input": "输入视频文件路径",
    "start_time": "开始时间（秒）",
    "end_time": "结束时间（秒）",
    "output": "输出文件路径（可选）"
  }
}
```

### 视频合并工具
```json
{
  "name": "video_merge",
  "description": "合并多个视频文件到一个文件中",
  "parameters": {
    "inputs": "输入视频文件路径列表（用逗号分隔）",
    "output": "输出文件路径（可选）"
  }
}
```

### 格式转换工具
```json
{
  "name": "video_convert",
  "description": "视频格式转换和转码",
  "parameters": {
    "input": "输入视频文件路径",
    "format": "输出格式（MP4/AVI/MKV等）",
    "output": "输出文件路径（可选）"
  }
}
```

### 视频变速工具
```json
{
  "name": "video_speed",
  "description": "调整视频播放速度",
  "parameters": {
    "input": "输入视频文件路径",
    "speed": "播放速度（例如1.5表示1.5倍速）",
    "output": "输出文件路径（可选）"
  }
}
```

### 水印添加工具
```json
{
  "name": "video_watermark",
  "description": "添加文字或图片水印到视频",
  "parameters": {
    "input": "输入视频文件路径",
    "text": "水印文字（可选）",
    "image_path": "水印图片路径（可选）",
    "position": "水印位置（默认右下角）",
    "output": "输出文件路径（可选）"
  }
}
```

### 字幕添加工具
```json
{
  "name": "video_subtitle",
  "description": "添加字幕到视频中",
  "parameters": {
    "input": "输入视频文件路径",
    "subtitle_path": "字幕文件路径（.ass/.ssa/.srt）",
    "output": "输出文件路径（可选）"
  }
}
```

### 音频提取工具
```json
{
  "name": "video_extract_audio",
  "description": "提取视频中的音频",
  "parameters": {
    "input": "输入视频文件路径",
    "format": "输出格式（MP3/AAC/WAV/FLAC）",
    "output": "输出文件路径（可选）"
  }
}
```

### 帧提取工具
```json
{
  "name": "video_extract_frames",
  "description": "提取视频帧保存为图片",
  "parameters": {
    "input": "输入视频文件路径",
    "interval": "提取间隔（秒）",
    "width": "输出图片宽度",
    "output_dir": "输出目录（可选）"
  }
}
```

### 制作GIF工具
```json
{
  "name": "video_make_gif",
  "description": "将视频片段转换为GIF动图",
  "parameters": {
    "input": "输入视频文件路径",
    "start_time": "开始时间（秒）",
    "duration": "GIF时长（秒）",
    "output": "输出文件路径（可选）"
  }
}
```

### 视频旋转工具
```json
{
  "name": "video_rotate",
  "description": "旋转和翻转视频",
  "parameters": {
    "input": "输入视频文件路径",
    "angle": "旋转角度（90/180/270度）",
    "output": "输出文件路径（可选）"
  }
}
```

### 裁剪画面工具
```json
{
  "name": "video_crop",
  "description": "裁剪视频画面尺寸",
  "parameters": {
    "input": "输入视频文件路径",
    "x": "左上角x坐标",
    "y": "左上角y坐标",
    "width": "裁剪宽度",
    "height": "裁剪高度",
    "output": "输出文件路径（可选）"
  }
}
```

### 缩略图生成工具
```json
{
  "name": "video_thumbnail",
  "description": "生成视频缩略图",
  "parameters": {
    "input": "输入视频文件路径",
    "time_position": "截图时间位置（秒）",
    "output": "输出文件路径（可选）"
  }
}
```

## 🐛 故障排除

### FFmpeg 未找到
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

### 常见错误
1. `FileNotFoundError` - 文件路径不正确
2. `PermissionError` - 权限不足
3. `ValueError` - 参数无效
4. `RuntimeError` - FFmpeg命令失败

## 🔄 版本更新

### v1.0.0（2024-05-12）
- 首次发布
- 添加视频信息获取功能
- 添加视频剪切和合并功能
- 添加视频变速和水印功能
- 添加字幕处理和音频提取功能
- 添加视频旋转和裁剪功能
- 添加GIF制作和缩略图功能
