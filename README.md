# 桌面AI助手 (Desktop AI Assistant)

一个基于 PyQt6 和 Ollama 的桌面宠物应用，可以与本地 AI 模型进行对话交互。

## 功能特点

- 🐾 **可爱桌宠** - 在桌面上显示一个可拖拽的宠物形象
- 🤖 **AI对话** - 集成 Ollama 本地 AI 模型，支持智能对话
- 💬 **气泡聊天** - 优雅的气泡式消息显示，自动调整位置
- 🎯 **智能交互** - 点击宠物显示输入框，拖拽移动位置
- 📌 **置顶显示** - 始终保持在桌面最上层
- 🗂️ **系统托盘** - 最小化到系统托盘，不占用任务栏空间

## 安装要求

### 系统要求
- Windows / macOS / Linux
- Python 3.7+

### 依赖安装
```bash
pip install PyQt6 requests
```

### Ollama 安装
1. 访问 [Ollama官网](https://ollama.ai/) 下载并安装
2. 启动 Ollama 服务
3. 下载所需的 AI 模型：
```bash
ollama pull qwen3:0.6b
```

## 快速开始

### 1. 配置设置
在代码开头修改配置参数：

```python
# 你的 Ollama 模型名称
MODEL_NAME = "qwen3:0.6b"
# 宠物图片文件路径
PET_IMAGE_PATH = "icon.png"
# 宠物显示尺寸
PET_SIZE = QSize(150, 150)
# Ollama API 地址（默认无需修改）
OLLAMA_API_URL = "http://localhost:11434/api/generate"
```

### 2. 运行程序
```bash
python desktop_assistant.py
```

## 使用说明

### 基本操作
- **左键点击**：显示输入框，与 AI 对话
- **左键拖拽**：移动宠物位置
- **右键点击**：显示功能菜单
- **系统托盘**：双击显示/隐藏宠物，右键打开菜单

### 对话功能
1. 点击宠物显示输入框
2. 输入问题后按回车发送
3. AI 回复会以气泡形式显示在宠物头顶
4. 气泡会自动在指定时间后消失

### 输入框操作
- **回车**：发送消息
- **Esc**：关闭输入框
- **点击外部**：自动隐藏输入框

## 文件结构

```
desktop_assistant.py    # 主程序文件
icon.png               # 宠物图标文件（示例）
README.md             # 说明文档
```

## 自定义配置

### 修改宠物形象
- 支持 PNG、GIF 格式图片
- 修改 `PET_IMAGE_PATH` 指向你的图片文件
- 调整 `PET_SIZE` 改变显示尺寸

### 更换 AI 模型
- 修改 `MODEL_NAME` 为其他 Ollama 模型
- 确保模型已通过 `ollama pull` 下载
- 支持的模型：qwen、llama、mistral 等

### 样式定制
- 气泡样式：修改 `ChatBubble` 类的样式表
- 输入框样式：修改 `InputBox` 类的样式表
- 显示时间：调整气泡的 `display_time` 计算逻辑

## 故障排除

### 常见问题

1. **Ollama 连接失败**
   - 确保 Ollama 服务正在运行
   - 检查 `OLLAMA_API_URL` 是否正确
   - 在终端运行 `ollama serve` 启动服务

2. **图片无法显示**
   - 检查图片文件路径是否正确
   - 确保图片文件存在于程序目录
   - 支持格式：PNG、GIF

3. **程序无响应**
   - 检查 AI 模型是否已正确下载
   - 确认系统资源充足
   - 尝试使用更小的模型

4. **气泡位置异常**
   - 自动调整逻辑会防止气泡超出屏幕
   - 可根据需要调整位置计算参数

## 开发说明

### 核心类说明
- `DesktopAssistant`：主宠物窗口类
- `AIWorker`：AI 请求工作线程
- `ChatBubble`：聊天气泡窗口
- `InputBox`：输入框窗口

### 扩展建议
- 添加更多宠物动画效果
- 支持多模型切换
- 增加对话历史记录
- 添加语音输入输出

## 许可证

本项目仅供学习和个人使用。

## 技术支持

如有问题请检查：
1. Ollama 服务状态
2. 网络连接
3. 模型文件完整性
4. Python 依赖版本

---

享受与你的桌面 AI 助手互动吧！ 🎉
