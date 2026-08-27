# 使用 GitHub Pages 发布教材

本页说明如何把整理后的教材发布成公开网站。发布对象只有 Markdown、教学图片和站点配置。

## 发布前检查

确认当前目录中至少包含：

```text
wheeltec-ros-textbook/
├── .github/workflows/deploy-docs.yml
├── docs/
├── metadata/
├── tools/
├── mkdocs.yml
└── requirements.txt
```

在本地运行：

```powershell
python tools/quality.py check --root .
python -m unittest discover -s tests -v
.\.venv\Scripts\mkdocs.exe build --strict
```

三条命令全部成功后，再发布当前版本。

## 创建 GitHub 仓库

1. 登录 GitHub，新建一个仓库，例如 `wheeltec-ros-textbook`。
2. 如果教材需要公开访问，可以创建 Public 仓库。
3. 不要把上一级目录整体上传；仓库根目录应当就是当前 `wheeltec-ros-textbook` 目录。
4. 不要上传 `.venv/` 和 `site/`。它们已写入 `.gitignore`。

第一次推送时，在当前目录执行：

```powershell
git init -b main
git add .
git commit -m "Publish WHEELTEC ROS textbook"
git remote add origin https://github.com/<your-account>/wheeltec-ros-textbook.git
git push -u origin main
```

把 `<your-account>` 换成自己的 GitHub 用户名或组织名。不要原样复制占位符。

## 启用 GitHub Pages

进入仓库的 **Settings → Pages**，在 **Build and deployment** 中选择 **GitHub Actions**。随后打开仓库的 **Actions** 页面，等待 `Deploy documentation to GitHub Pages` 工作流完成。

部署成功后，项目站点通常位于：

```text
https://<your-account>.github.io/wheeltec-ros-textbook/
```

以后只要把更新推送到 `main` 分支，工作流就会重新执行严格构建并发布新版本。也可以在 Actions 页面通过 `workflow_dispatch` 手动触发。

## 自定义域名

如需使用自己的域名，先在 GitHub Pages 设置中填写域名，再按页面提示配置 DNS。绑定前应确认自己拥有该域名，不要把示例域名写入 `mkdocs.yml`。

## 发布失败时怎么查

| 现象 | 检查方法 |
|---|---|
| Actions 没有启动 | 检查工作流是否位于 `.github/workflows/`，默认分支是否为 `main` |
| 构建阶段失败 | 打开失败步骤，先在本地复现 `mkdocs build --strict` |
| Pages 显示 404 | 确认 Settings → Pages 的来源是 GitHub Actions，并检查部署任务是否成功 |
| 页面链接失效 | 运行 `python tools/quality.py check --root .`，修复报告的内部链接 |

## 版本更新流程

```powershell
git add docs metadata mkdocs.yml
git commit -m "Update textbook content"
git push
```

发布前始终保留本地构建检查。这样 GitHub Actions 的失败通常能在推送之前发现。

## 章节导航

[上一章：全系统验收](41-system-acceptance.md) · [返回本卷](index.md) · [返回教材首页](../index.md)
