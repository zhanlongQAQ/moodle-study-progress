# Moodle Study Progress

这是基于 [救驾（jiujiastudy）](https://github.com/jiujiastudy/jiujiastudy) v0.3.1 的可安装版本。救驾生成本周清单和 Deadline 雷达。这个版本在 Moodle 的本周清单里加了 Module、Topic 或 Week 进度条，刻度随课件更新，学习进度由学生手动选择。

## 安装和使用

在 Codex 里发送这句话，并把后面的学校地址换成你平时登录的 Moodle 地址。

> 帮我从 https://github.com/zhanlongQAQ/moodle-study-progress 安装这版救驾技能，并按它的 SKILL.md 初始化。我的 Moodle 地址是 `https://你的学校的Moodle地址`。

也可以手动安装。把本仓库克隆或解压到 Codex 的 `~/.agents/skills/jiujiastudy`，让 `SKILL.md` 和 `tools/` 直接位于该目录下。Windows PowerShell 示例：

```powershell
git clone https://github.com/zhanlongQAQ/moodle-study-progress.git "$env:USERPROFILE\.agents\skills\jiujiastudy"
```

如果已经安装过原版，先把原技能目录备份到 `skills/` 之外，再把此版本放到同一个位置。已有的救驾学习档案在独立的数据目录中。安装后开一个新对话，输入「用救驾连我的 Moodle」，在弹出的学校登录窗口里用自己的账号登录，然后说「这周学什么」。通过 Git 克隆安装的同学，可以在技能目录运行 `git pull --ff-only` 更新。

章节刻度适用于采用 `Module 1`、`Topic 1` 或 `Week 1` 这类节标题，并提供可识别正课讲义或幻灯片的 Moodle 课程。其他课程仍可使用本周清单和 Deadline 雷达。进度保存在打开本周清单的浏览器中。

定时刷新和收发邮件由使用者按自己的账号和授权配置。需要简短的行动摘要时，可以直接说「把本周的新事项整理成邮件，每条只写我要做什么、时间和链接」。

上游附带的 `/jj-learn` 学习页和 `/humanizer` 文字润色入口也保留在 `skills/`。

## 体验 Demo

下载仓库后，用浏览器打开 `index.html`。把 Reaction Engineering 的进度拖到 **Topic 6**，再点 **模拟发布 Topic 7**。新刻度会出现，滑块仍停在 Topic 6。三门示例课程用的都是虚构数据，打开页面即可体验。

如需修改示例，编辑 `example-courses.json`，然后在仓库目录运行以下命令重新生成 `index.html`。脚本只使用 Python 标准库。

```powershell
python progress.py
```

## 如何识别进度

- 按各门课自己的 Module、Topic 或 Week 编号识别章节。每章需要有已开放的正课讲义或幻灯片才会进入刻度。
- 课程进度按课程 ID 保存，保存的是章节号。比如一门课跳过 Reading Week，下一章仍显示 Week 7。
- 周报和离线 Demo 共用 `tools/cc_progress.py`。周报读取本机 Moodle 模块快照，Demo 读取 `example-courses.json`。

## 我的本地救驾配置

- 每周更新课件信息并生成周报，只追踪当前学年的指定课程。
- 过滤已完成待办，在清单中保留实验时段和远期截止提醒。
- 邮件改成简短的行动摘要，只列仍需关注或处理的事项。每条写清楚要做什么、什么时候做，并附上相关链接。

## 来源与许可

本仓库以 [jiujiastudy v0.3.1](https://github.com/jiujiastudy/jiujiastudy/releases/tag/v0.3.1) 为基础，加入了课程进度功能。适用 [PolyForm Noncommercial License 1.0.0](LICENSE)，保留上游版权声明及 [第三方许可说明](THIRD_PARTY_NOTICES.md)。
