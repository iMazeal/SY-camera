# 实时画面流与 GUI 界面设计 Spec

## 概述

在树莓派 3B+（800×480 DSI 触摸屏）上实现相机实时预览和基础拍照功能的第一阶段。目标：应用启动直接进入预览，点击圆形按钮拍照保存，预览和拍照分辨率保持一致。

## 界面布局

```
┌──────────────────────────────────────┬────────────┐
│                                      │   右边栏     │
│                                      │  (~100px)   │
│          取景器 (Viewfinder)          │             │
│                                      │  ● 拍照按钮  │
│      QGlPicamera2  640×480           │   (圆形)     │
│                                      │             │
│                                      │  ▓ 相册按钮  │
│                                      │  (圆角矩形)   │
│                                      │             │
└──────────────────────────────────────┴────────────┘
←─────────── 800px ───────────────────→
```

- **取景器**：占满左侧全部空间，QGlPicamera2 实时显示 640×480 @ 30fps
- **右侧边栏**：深色背景，约 100px 宽，垂直居中放置圆形拍照按钮，底部放置圆角矩形的相册按钮
- **所有按钮均为纯图标，无文字**
- **窗口**：无边框全屏 800×480

## 技术栈

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| GUI 框架 | PyQt5 | RPi 预装，与 QGlPicamera2 原生集成 |
| 相机预览 | QGlPicamera2 | OpenGL ES 硬件加速，Picamera2 官方封装 |
| 相机控制 | Picamera2 API | 支持曝光时间/增益等参数调节 |
| Mock 模式 | numpy 生成测试图 | 开发机无摄像头硬件时降级运行 |
| 图像处理 | opencv-python-headless | 图像编解码、文件管理 |

## 模块设计

### `src/main.py` — 应用入口

- 初始化 QApplication（设置 Qt::AA_EnableHighDpiScaling）
- 检测 Picamera2 硬件是否可用
  - 可用：创建 Picamera2 实例
  - 不可用：进入 Mock 模式（CameraManager 使用测试图数据源）
- 初始化 CameraManager → 创建 MainWindow → 启动 → app.exec()

### `src/camera_manager.py` — 相机控制

**入参**：Picamera2 或 None（Mock 模式）
**方法**：

| 方法 | 说明 |
|------|------|
| `start_preview()` | 配置并启动 640×480 预览 |
| `capture(output_path)` | 切换 still 模式 → 拍照 → 重命名 → 恢复预览 |
| `switch_to_mock()` | 切换到测试图模式 |
| `set_control(name, value)` | 设置相机参数（曝光/增益等），透传 Picamera2.set_controls |

**边界**：
- 拍照期间连续点击：通过 busy flag 防抖，拍照中忽略后续请求
- Mock 模式下的 capture()：将当前测试图"保存"为文件

### `src/ui/main_window.py` — 主窗口

- QMainWindow，无边框，全屏 800×480
- QHBoxLayout：左 = Viewfinder，右 = ControlsPanel
- 连接 ControlsPanel.capture_requested → CameraManager.capture()

### `src/ui/viewfinder.py` — 取景器封装

- 继承 QGlPicamera2 的封装类
- 暴露 done_signal（拍照完成通知）
- Mock 模式下显示 QLabel（numpy 数组转 QPixmap，定时刷新）

### `src/ui/controls.py` — 右侧控制面板

- QWidget，固定宽度 ~100px，深色背景
- 内部布局：顶部弹性空间 → 圆形成品按钮 → 弹性空间 → 相册按钮（圆角矩形）→ 底部间距
- **拍照按钮**：QPushButton，圆形（setMask），红色渐变，纯图标（白色圆环），点击发出 capture_requested 信号
- **相册按钮**：QPushButton，圆角矩形，纯图标图标，后续实现
- 按钮均设 QSizePolicy 居中

## 拍照流程

```
用户点击圆形拍照按钮
    ↓ (已通过防抖，忽略重复点击)
ControlsPanel.capture_requested 信号发射
    ↓
MainWindow 槽函数触发 CameraManager.capture()
    ↓
CameraManager:
  1. 生成时间戳文件名 YYYYMMDD_HHMMSS.jpg
  2. 调用 picam2.switch_mode_and_capture_file(config, path, signal_function=…)
    ↓
QGlPicamera2.done_signal 触发
    ↓
CameraManager.wait(job) 确保完成
CameraManager 恢复预览
    ↓
拍照完成，文件已保存到 ./photos/
```

## 命名规则

- 照片文件：`photos/YYYYMMDD_HHMMSS.jpg`
- 例如：`photos/20260427_143022.jpg`
- 启动时自动创建 `photos/` 目录（如不存在）

## Mock 模式

在 x86_64 开发机上，Picamera2 无法访问摄像头硬件。检测到不可用时：

1. CameraManager 创建 numpy 测试图（彩色渐变/棋盘格）
2. QTimer 定时刷新测试图模拟预览（约 15fps）
3. 拍照操作将当前帧保存为 JPEG
4. 控制台对应输出 `[Mock] Captured: photos/xxx.jpg`

## 里程碑

| # | 内容 | 预计文件 |
|---|------|----------|
| 1 | 项目初始化 + 环境依赖 | pyproject.toml |
| 2 | CameraManager（含 Mock） | camera_manager.py |
| 3 | 主窗口 + 取景器 | main_window.py, viewfinder.py |
| 4 | 右侧控制面板 | controls.py |
| 5 | 入口集成 | main.py |
| 6 | 端到端验证 | 启动测试 |
