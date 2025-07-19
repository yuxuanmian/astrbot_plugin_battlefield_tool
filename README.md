# astrbot_plugin_battlefield_tool

# ✨Astrbot 一个查询战地风云战绩统计的插件

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)

## 🎮 支持游戏

- ✅ **战地4** (Battlefield 4)
- ✅ **战地1** (Battlefield 1)
- ✅ **战地5** (Battlefield V)

## ⌨️ 使用命令

| 功能 | 命令格式 | 参数说明                                             | 别名 |
|------|----------|--------------------------------------------------|------|
| **账号绑定** | `/bind [ea_name]` | `ea_name`: EA账号名                                 | `/绑定` |
| **查询战绩** | `/stat [ea_name],game=[游戏代号]` | `ea_name`: EA账号名<br>`game`: 游戏代号    | - |
| **武器统计** | `/weapons [ea_name],game=[游戏代号]` | `ea_name`: EA账号名<br>`game`: 游戏代号    | `/武器` |
| **载具统计** | `/vehicles [ea_name],game=[游戏代号]` | `ea_name`: EA账号名<br>`game`: 游戏代号    | `/载具` |
| **服务器查询** | `/servers [server_name],game=[游戏代号]` | `server_name`: 服务器名<br>`game`: 游戏代号 | `/服务器` |
💡 提示

**游戏代号对照表**:
- `bf4`: 战地4
- `bf1`: 战地1
- `bf5`: 战地5

**命令示例**
- `全参`:/stat shooting_star_c,game=bf4
- `无EA账号名`:/stat game=bf4
- `无游戏代号`:/stat shooting_star_c
- `无参`:/stat

## 🌟 功能预览

<div>
  <img src="https://s21.ax1x.com/2025/07/19/pV3xLwQ.jpg" width="30%" alt="bfv战绩查询效果"/>
  <img src="https://s21.ax1x.com/2025/07/19/pV3xjFs.jpg" width="30%" alt="bf1战绩查询效果"/>
</div>

## 📌 注意事项

html转图服务能力来自[CampuxUtility](https://github.com/idoknow/CampuxUtility)  

如果条件允许建议自部署一个，详见步骤见[Astrbot文档](https://astrbot.app/)的其他章

## 👍致谢
### 🎮 数据服务
- [api.gametools.network](https://api.gametools.network) - 提供战地系列游戏数据的API接口

### 💻 开源项目
- [nonebot-plugin-bfchat](https://github.com/050644zf/nonebot-plugin-bfchat) - 参考了其HTML样式设计

### 🖼️ 资源托管
- [路过图床](https://imgse.com/) - 提供图片托管服务

🙌 衷心感谢所有使用者和贡献者的支持！您的反馈和建议是我们持续改进的动力！

## 🤝 参与贡献
欢迎任何形式的贡献！以下是标准贡献流程：

1. **Fork 仓库** - 点击右上角 Fork 按钮创建您的副本
2. **创建分支** - 基于开发分支创建特性分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **提交修改** - 编写清晰的提交信息：
   ```bash
   git commit -m "feat: 添加新功能" -m "详细描述..."
   ```
4. **推送更改** - 将分支推送到您的远程仓库：
   ```bash
   git push origin feature/your-feature-name
   ```
5. **发起 PR** - 在 GitHub 上创建 Pull Request 到原仓库的 `main` 分支

## 📜 开源协议
本项目采用 [MIT License](LICENSE)
