import sys
import os
import requests
from PyQt6.QtWidgets import (QApplication, QLabel, QMenu, QSystemTrayIcon,
                             QLineEdit, QWidget, QVBoxLayout)
from PyQt6.QtCore import Qt, QPoint, QSize, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QPixmap, QMovie, QAction, QCursor, QMouseEvent, QIcon

# ==========================================
# 0. 配置区域 (在此修改参数)
# ==========================================
# 你的 Ollama 模型名称 (请确保在终端用 'ollama pull' 下载过)
MODEL_NAME = "qwen3:0.6b"
# 宠物图片文件名 (支持 .png 或 .gif)
PET_IMAGE_PATH = "icon.png"
# 宠物尺寸 (宽, 高)
PET_SIZE = QSize(150, 150)
# Ollama API 地址
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# ==========================================
# 1. AI 工作线程 (防止界面卡死)
# ==========================================
class AIWorker(QThread):
    response_received = pyqtSignal(str)  # 信号：当收到回复时发出

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            # 构造请求数据
            data = {
                "model": MODEL_NAME,
                "prompt": self.prompt,
                "stream": False  # 关闭流式输出，一次性返回
            }

            response = requests.post(OLLAMA_API_URL, json=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                reply_text = result.get("response", "")
                self.response_received.emit(reply_text)
            else:
                self.response_received.emit(f"API 错误: {response.status_code}")

        except Exception as e:
            self.response_received.emit(f"连接 Ollama 失败: {str(e)}\n请检查 Ollama 是否运行。")


# ==========================================
# 2. 气泡显示窗口 (用于显示 AI 回复)
# ==========================================
class ChatBubble(QWidget):
    def __init__(self):
        # 显式传递 None 作为父对象，确保它是独立的顶层窗口
        super().__init__(parent=None)

        # --- 窗口标志设置 ---
        # ToolTip 模式在 Windows 上优先级极高，不会被遮挡
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.ToolTip)

        # 设置背景透明 (用于实现圆角)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)  # 显示时不抢焦点

        # --- 布局设置 ---
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # 外边距，留出阴影/边框位置

        # --- 内部文本标签 ---
        self.label = QLabel()
        self.label.setWordWrap(True)  # 自动换行

        # 样式表：深色文字，白色背景，圆角黑边框
        self.label.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                border: 2px solid #333333;
                border-radius: 10px;
                padding: 8px;
                color: #000000;
                font-family: "Microsoft YaHei";
                font-size: 14px;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.label)
        self.setLayout(layout)

        # 固定最大宽度，防止气泡太宽
        self.setFixedWidth(240)

        # 定时器：用于自动隐藏气泡
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def show_message(self, text, pet_rect):
        """
        显示消息并自动调整位置到宠物头顶
        :param text: 要显示的文字
        :param pet_rect: 宠物的几何矩形 (self.geometry())
        """
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()

        # --- 位置计算参数 ---
        y_offset = 10  # 垂直偏移微调
        margin = 5  # 间距

        # --- 计算水平位置 (让气泡在宠物头顶居中) ---
        pet_center_x = pet_rect.x() + (pet_rect.width() // 2)
        target_x = pet_center_x - (self.width() // 2)

        # --- 计算垂直位置 (默认在上方) ---
        target_y = pet_rect.y() - self.height() - margin + y_offset

        # 防止气泡跑出屏幕顶部
        if target_y < 0:
            # 如果顶住了屏幕，就改到宠物脚底下显示
            target_y = pet_rect.y() + pet_rect.height() + margin

        self.move(target_x, target_y)
        self.show()
        self.raise_()  # 提升窗口层级

        # 根据字数动态计算显示时间 (基础3秒 + 每个字150毫秒)
        display_time = 3000 + (len(text) * 150)
        self.hide_timer.start(display_time)


# ==========================================
# 3. 输入框窗口
# ==========================================
class InputBox(QWidget):
    text_entered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 保持原有的窗口标志设置
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"向 {MODEL_NAME} 提问... (Esc 关闭)")
        # 样式保持不变
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 240);
                border: 1px solid #aaa;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #0078d7; }
        """)
        self.input_field.returnPressed.connect(self.on_submit)
        layout.addWidget(self.input_field)
        self.setLayout(layout)
        self.setFixedSize(220, 40)

    def on_submit(self):
        text = self.input_field.text().strip()
        if text:
            self.text_entered.emit(text)
            self.input_field.clear()
            # --- 关键修改 ---
            # 这里删除了 self.hide()，这样回车后窗口不会消失，焦点也不会丢失
            # self.hide()

    def focusOutEvent(self, event):
        # 点击输入框外部时，依然自动隐藏
        self.hide()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        # 增加功能：按下 Esc 键手动关闭输入框
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)


# ==========================================
# 4. 主程序：桌面宠物
# ==========================================
class DesktopAssistant(QLabel):
    def __init__(self):
        super().__init__()

        # 状态变量
        self.is_dragging = False
        self.drag_position = QPoint()
        self.mouse_press_global_pos = QPoint()

        # 初始化界面和组件
        self.init_ui()
        self.init_tray()
        self.chat_box = InputBox()
        self.bubble = ChatBubble()

        # 连接信号
        self.chat_box.text_entered.connect(self.handle_input)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.load_resource()
        self.show()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(PET_IMAGE_PATH):
            self.tray_icon.setIcon(QIcon(PET_IMAGE_PATH))
        else:
            print(f"警告: 托盘图标找不到文件 {PET_IMAGE_PATH}")

        tray_menu = QMenu()

        # 新增：设置 (占位符)
        action_settings = QAction("设置", self)
        action_settings.triggered.connect(lambda: None)
        tray_menu.addAction(action_settings)

        # 新增：显示桌宠 (占位符)
        action_show_pet = QAction("显示桌宠", self)
        action_show_pet.triggered.connect(lambda: None)
        tray_menu.addAction(action_show_pet)

        # 添加一个分隔线，使菜单结构更清晰
        tray_menu.addSeparator()

        # 3. 原有的：退出
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 双击托盘显示/隐藏 (此功能保留)
        self.tray_icon.activated.connect(
            lambda r: self.setVisible(not self.isVisible())
            if r == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )

    def load_resource(self):
        if not os.path.exists(PET_IMAGE_PATH):
            self.setText("无图")
            self.setStyleSheet("color: red; font-weight: bold; background: white;")
            self.resize(100, 50)
            print(f"错误: 当前目录下未找到 {PET_IMAGE_PATH}，请放入图片文件。")
            return

        file_ext = os.path.splitext(PET_IMAGE_PATH)[1].lower()
        if file_ext == '.gif':
            self.movie = QMovie(PET_IMAGE_PATH)
            self.movie.setScaledSize(PET_SIZE)
            self.setMovie(self.movie)
            self.movie.start()
        else:
            pixmap = QPixmap(PET_IMAGE_PATH)
            pixmap = pixmap.scaled(PET_SIZE.width(), PET_SIZE.height(),
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(pixmap)
        self.resize(PET_SIZE)

    def handle_input(self, text):
        # 1. 显示思考气泡
        self.bubble.show_message("思考中...", self.geometry())

        # 2. 启动后台线程请求 AI
        self.ai_thread = AIWorker(text)
        self.ai_thread.response_received.connect(self.on_ai_reply)
        self.ai_thread.start()

    def on_ai_reply(self, reply_text):
        # 3. 收到回复，更新气泡
        self.bubble.show_message(reply_text, self.geometry())

    # --- 鼠标事件处理 (拖拽与点击) ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.mouse_press_global_pos = event.globalPosition().toPoint()
            # 计算鼠标点击点相对于窗口左上角的偏移
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            self.chat_box.hide()  # 拖动时隐藏输入框
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            # 移动窗口
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.bubble.hide()  # 移动时隐藏气泡，避免错位
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            curr_pos = event.globalPosition().toPoint()
            # 如果鼠标移动距离很短，视为点击，显示输入框
            if (curr_pos - self.mouse_press_global_pos).manhattanLength() < 5:
                self.show_input_box()

    def show_input_box(self):
        pet_geo = self.geometry()
        # 让输入框水平居中于宠物下方
        x = pet_geo.x() + (pet_geo.width() - self.chat_box.width()) // 2
        y = pet_geo.y() + pet_geo.height() + 10
        self.chat_box.move(x, y)
        self.chat_box.show()
        self.chat_box.input_field.setFocus()
        self.chat_box.activateWindow()

    def show_context_menu(self):
        menu = QMenu(self)

        # 1. 动作交互菜单项
        action_interact = QAction("动作交互", self)
        # 连接一个空的 lambda 作为占位符，暂时不执行任何操作
        action_interact.triggered.connect(lambda: None)
        menu.addAction(action_interact)

        # 2. 隐藏显示菜单项
        action_toggle_visibility = QAction("隐藏桌宠", self)
        action_toggle_visibility.triggered.connect(lambda: None)
        menu.addAction(action_toggle_visibility)

        # 3. 对话界面菜单项
        action_chat_interface = QAction("对话界面", self)
        action_chat_interface.triggered.connect(lambda: None)
        menu.addAction(action_chat_interface)

        # 添加一个分隔线，使菜单结构更清晰
        menu.addSeparator()

        # 4. 退出菜单项（原有的）
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)

        # 在鼠标当前位置显示菜单
        menu.exec(QCursor.pos())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = DesktopAssistant()
    sys.exit(app.exec())