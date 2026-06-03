<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-6.11.1-brightgreen.svg" alt="PySide6">
  <img src="https://img.shields.io/badge/OpenCV-4.13.0.92-blue.svg" alt="OpenCV">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/version-0.4.2-red.svg" alt="Version">
</p>

<h1 align="center">
  🏎️ FH6_ShuaShuaLe
</h1>

<p align="center">
  <strong>《极限竞速：地平线 6》自动化辅助工具</strong><br>
  刷技术点 · 超级抽奖 · 综合循环刷 · 送外卖 · 刷劲敌 · 线上挂机 · 遥测监控
</p>

## ✨ 功能一览

- 🎯 **刷技术点** - 图像识别/纯按键双模式，自动重开
- 🎰 **刷超级抽奖** - 完整买车抽奖流程，失败即停
- 🔄 **综合循环刷** - 步骤串联，独立参数，实时高亮
- 🍔 **送外卖** - 遥测模式（推荐）/图像识别/纯按键
- 🏁 **刷劲敌** - 按住W + 定时Enter
- 🌐 **线上挂机** - 未完成和测试，待后续更新
- 📊 **遥测监控** - UDP实时显示80+数据字段
- 🔧 **画面校准** - 偏移微调，强制1280x720
- 💾 **进度持久化** - 自动保存，一键重置
- 🎨 **Fluent Design界面** - 浅色/深色主题

> 📖 **详细操作步骤、蓝图代码、车辆调教、游戏内设置请查看 [小黑盒教程帖](https://www.xiaoheihe.cn/app/bbs/link/182618437)**

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 主体语言 |
| PySide6 | GUI框架 |
| PySide6-Fluent-Widgets | Fluent Design组件，Windows 11风格 |
| OpenCV | 图像识别与模板匹配 |
| windows-capture | 高性能窗口截图（WGC） |
| pywin32 | Windows API，后台按键 |

## 📦 快速开始

```bash
git clone https://github.com/Prlock4367/FH6_ShuaShuaLe.git
cd FH6_ShuaShuaLe
pip install -r requirements.txt
python main.py
```

##  环境要求
- Windows 10/11（建议1903+）
- 《极限竞速：地平线 6》已运行，窗口标题 Forza Horizon 6
- 游戏键位默认，关闭“下一站”

## ❓ 常见问题

- **找不到窗口**：管理员运行，检查游戏标题
- **图像识别失败**：运行画面校准，确保窗口1280x720
- **遥测模式绑定失败**：检查游戏IP/端口，微软商店版需解除网络限制
- **启动闪退**：查看 `fh6_tool.log`，安装VC++运行库

## 🧪 后续计划

- ✅ 线上挂机
- 🔄 自动换挡（基于遥测）
- 🔄 漂移辅助（过三星）
- 🔄 更多自动驾驶场景

## ☕ 赞助支持（量力而行）

如果这个工具帮到了你，可以请作者喝杯咖啡，完全自愿～  
赞助全部用于项目维护，也是我更新的小动力。

👉 [前往爱发电支持 Prlock](https://afdian.com/a/Prlock)

## 📞 反馈

- **GitHub Issues**：[提交Bug/需求](https://github.com/Prlock4367/FH6_ShuaShuaLe/issues)
- **小黑盒**：[教程帖留言](https://www.xiaoheihe.cn/app/bbs/link/182618437)（附截图+日志）

## 📄 许可证

MIT © Prlock

## ⚠️ 免责声明

本工具为个人开发，与《地平线6》官方无关。仅模拟键盘操作，不修改内存。使用第三方工具存在账号风险，请自行判断承担后果。仅供学习交流，勿用于商业或破坏公平环境。

<p align="center">Made with ❤️ by Prlock</p>
