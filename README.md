# WHEELTEC ROS 工程教材

本目录存放按工程任务重写的多文件教材。教材以 ROS 2 为主线，面向已经拿到 WHEELTEC 机器人、需要完成开发、部署和故障排查的读者。

这是基于用户资料整理的非官方学习项目，不代表 WHEELTEC 官方文档。产品名称和商标归其权利人所有。

MkDocs 为教材提供侧边栏、全文搜索和章节导航；每个 Markdown 文件也可以单独打开。公开版本以整理后的教材正文为准，不依赖外部资料目录。

## 本地预览

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\mkdocs.exe serve
```

## GitHub Pages 发布

仓库已经包含 `.github/workflows/deploy-docs.yml`。将当前目录作为独立 GitHub 仓库推送后，在仓库的 **Settings → Pages** 中选择 **GitHub Actions**。完整步骤见[使用 GitHub Pages 发布教材](docs/08-deployment-maintenance/42-github-pages-deployment.md)。
