# 🏎️ FH6 刷刷乐

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-6.11.1-brightgreen.svg" alt="PySide6">
  <img src="https://img.shields.io/badge/OpenCV-4.13.0.92-blue.svg" alt="OpenCV">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<h3 align="center">《极限竞速：地平线 6》自动化辅助工具</h3>

<p align="center">
  刷技术点 · 超级抽奖 · 自动驾驶 · 综合循环刷 · 删除车辆
</p>


## ✨ 功能特点

### 🎯 刷技术点
- 自定义循环次数和按住 W 时长
- 支持图像识别 + 纯按键双模式
- 赛后自动识别结算画面，识别失败自动重开（不计数）
- 通用延迟可调，适配不同网络/机器性能

### 🎰 刷超级抽奖
- 完整模拟买车 → 抽奖流程
- 图像识别监测买车前/买车后画面，失败即停不浪费
- 纯按键模式支持自定义买车等待/加载时间

### 🚗 自动驾驶
- 按住 W 90秒 → 按 Enter 防掉线 → 按住 W 90秒 → 循环
- 适合长时间挂机，防止游戏进入暂停状态

### 🔄 综合循环刷（高级功能）
- **流程图式卡片控制**：将多个步骤串联成一个完整循环
- **步骤列表**：导航至蓝图 → 刷技术点 → 返回居所 → 刷超级抽奖 → 删除车辆
- **每步独立参数**：每个步骤可单独设置循环次数、通用延迟等
- **实时高亮**：当前执行步骤在 UI 面板中高亮显示
- **单步开关**：未启用的步骤自动跳过
- **全局循环次数控制**：支持整轮大循环，进度自动保存

### 🗑️ 删除车辆
- 高阈值图像识别（98%），防止误删非目标车辆
- **双重识别保障**：主图匹配 + 确认图二次验证
- **驾驶状态检测**：自动跳过正在驾驶的车辆
- 删除成功自动计数，进度持久化
- ⚠️ 危险操作有弹窗警告

### 🔧 画面校准
- 实时预览窗口，方向键微调客户区偏移
- 一键保存偏移量到配置文件
- 强制设置窗口客户区为 1280x720，确保图像识别稳定

### 📊 进度持久化
- 所有模块的完成进度自动保存到配置文件
- 下次启动自动恢复，重置按钮一键归零


## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.11+** | 主体语言 |
| **PySide6** | GUI 框架 |
| **PySide6-Fluent-Widgets** | Fluent Design 界面组件，现代化 Windows 11 风格 |
| **OpenCV** | 图像识别与模板匹配 |
| **windows-capture** | 高性能 Windows 游戏窗口截图（WGC 接口） |
| **pywin32** | Windows API 调用，后台窗口消息模拟 |
| **threading + StoppableSleep** | 可中断的异步任务调度 |


## 📦 安装与使用

### 环境要求
- Windows 10/11
- Python 3.11 或更高版本
- 《极限竞速：地平线 6》已安装并运行
- 游戏窗口标题需为 `Forza Horizon 6`

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/[你的用户名]/FH6_ShuaShuaLe.git
cd FH6_ShuaShuaLe
