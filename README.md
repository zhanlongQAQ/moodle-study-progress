# Moodle Study Progress

一个基于 [救驾（jiujiastudy）](https://github.com/jiujiastudy/jiujiastudy) 的学习进度扩展。它从课程结构中识别已发布的正课课件，为每门课生成 Module、Topic 或 Week 刻度。学生手动选择自己的进度，选择保存在当前浏览器中。以后有新课件发布，刻度会增加，之前选中的章节会保留。

## 体验 Demo

下载仓库后，用浏览器打开 `index.html`。把 Reaction Engineering 的进度拖到 **Topic 6**，再点 **模拟发布 Topic 7**。新刻度会出现，滑块仍停在 Topic 6。三门示例课程用的都是虚构数据，打开页面即可体验。

如需修改示例，编辑 `example-courses.json`，然后在仓库目录运行以下命令重新生成 `index.html`。脚本只使用 Python 标准库。

```powershell
python progress.py
```

## 如何识别进度

- 按各门课自己的 Module、Topic 或 Week 编号识别章节。每章需要有已开放的正课讲义或幻灯片才会进入刻度。
- 课程进度按课程 ID 保存，保存的是章节号。比如一门课跳过 Reading Week，下一章仍显示 Week 7。
- `progress.py` 接收与救驾模块快照同形的课程结构。这个仓库包含章节识别、网页渲染和离线 Demo。

在本地使用时，救驾每周更新课件信息并生成周报。个人部署还加了当前学年课程筛选、已完成待办过滤，以及实验时段和远期截止提醒的显示调整。

## 来源与许可

项目源于对救驾周报的个人定制。Moodle 采集和原有周报来自 [jiujiastudy](https://github.com/jiujiastudy/jiujiastudy)，本仓库展示新增的课程进度功能。适用 [PolyForm Noncommercial License 1.0.0](LICENSE)，许可证保留了上游版权声明。
