# ⚙️ astrbot_plugin_gscore_adapter v0.4.3

> [!IMPORTANT]  
> 请注意！该插件并不能开箱即用，你还需要完成Core的安装和配置！！
>
> 如果使用Docker安装Core，请务必确保HOST和PORT填写正确，该插件可以修改链接Core的HOST和PORT！！
>
> 类似ISSUES [#12] [#10] 

[早柚核心](https://docs.sayu-bot.com/)
**💖一套业务逻辑，多个平台支持！**

**🎉 [详细文档](https://docs.sayu-bot.com)** ( [快速开始(安装)](https://docs.sayu-bot.com/Started/InstallCore.html) | [链接Bot](https://docs.sayu-bot.com/LinkBots/AdapterList.html) | [插件市场](https://docs.sayu-bot.com/InstallPlugins/PluginsList.html) )

## 配置补充

- `GSCORE_ONLY_PREFIXES`：可选字符串列表。
  - 示例：`["core", "gs", "sr", "zzz", "ww"]`
  - 当用户消息文本命中这些前缀时，消息仅会发送给 GsCore，并显式调用 `event.stop_event()` 阻断后续 LLM 流程。

## 优点&特色

- 🔀 **异步优先**：异步处理~~大量~~消息流，不会阻塞任务运行
- 🔧 **易于开发**：即使完全没有接触过Python，也能在一小时内迅速上手 👉 [插件编写指南](https://docs.sayu-bot.com/CodePlugins/CookBook.html)
- ♻ **热重载**：修改插件配置&安装插件&更新插件，无需重启也能直接应用
- **🌎 [网页控制台](https://docs.sayu-bot.com/Advance/WebConsole.html)**：集成网页控制台，可以通过WEB直接操作**插件数据库/配置文件/检索日志/权限控制/数据统计/批量发送** 等超多操作
- 📄 **高度统一**：统一**所有插件**的[插件前缀](https://docs.sayu-bot.com/CodePlugins/PluginsPrefix.html)/[配置管理](https://docs.sayu-bot.com/CodePlugins/PluginsConfig.html)/[帮助图生成](https://docs.sayu-bot.com/CodePlugins/PluginsHelp.html)/权限控制/[数据库写入](https://docs.sayu-bot.com/CodePlugins/PluginsDataBase.html)/[订阅消息](https://docs.sayu-bot.com/CodePlugins/Subscribe.html)，所有插件编写常见方法一应俱全，插件作者可通过简单的**继承重写**实现**高度统一**的逻辑
- 💻 **多元适配**：借助上游Bot (NoneBot2 / Koishi / YunzaiBot) 适配，支持QQ/QQ频道/微信/Tg/Discord/飞书/KOOK/DODO/OneBot v11(v12)等多个平台，做到**一套业务逻辑，多个平台支持**！
- 🚀 **作为插件**：该项目**不能独立使用**，作为**上游Bot (NoneBot2 / Koishi / YunzaiBot)** 的插件使用，无需迁移原本Bot，保留之前全部的功能，便于充分扩展
- 🛠 **内置命令**：借助内置命令，轻松完成**重启/状态/安装插件/更新插件/更新依赖**等操作
- 📝 **帮助系统**：通过统一适配，可按照不同**权限输出**不同帮助，并支持插件的**二级菜单注册**至主帮助目录，并支持在帮助界面使用不同的**自定义前缀**

<details><summary>主菜单帮助示例</summary><p>
<a><img src="https://s2.loli.net/2025/02/07/glxaJyS6325zvbG.jpg"></a>
</p></details>

## 感谢

- 本项目仅供学习使用，请勿用于商业用途
- [爱发电](https://afdian.com/a/KimigaiiWuyi)
- [GPL-3.0 License](https://github.com/Genshin-bots/gsuid_core/blob/master/LICENSE) ©[@KimigaiiWuyi](https://github.com/KimigaiiWuyi)