---
title: "这个博客是怎么搭起来的"
date: 2026-10-18T09:30:00+08:00
categories: ["技术"]
tags: ["Hugo", "hugo-coder", "GitHub Pages"]
description: "本站的技术选型、目录结构、配置要点与部署方式，换新环境时按此还原即可。"
---

## 选型

博客的核心诉求只有三个：**写得快、部署省心、不花钱**。

- **Hugo**：单二进制、构建快，中文排版和代码高亮开箱可用。
- **hugo-coder**：极简单列布局，自带浅色/深色配色切换，几乎没有视觉噪音。
- **GitHub Pages**：仓库推上去即发布，不用碰服务器。

整站没有服务端逻辑，构建产物就是一堆静态文件。

## 目录结构

```
myblog/
├── content/
│   ├── posts/          # 文章
│   └── about.md        # 独立页面
├── static/img/         # 头像、图标
├── assets/scss/        # 自定义样式（会走 Hugo 资源管线）
├── layouts/_partials/  # 覆盖主题的模板片段
├── themes/
│   └── hugo-coder/     # git submodule
└── hugo.toml           # 站点配置
```

## 几个容易踩的坑

### 1. 图片必须放 static/

hugo-coder 输出图片地址用的是 `relURL`，**不走 Hugo 的资源管线**：

```go-html-template
<img src="{{ . | relURL }}">
```

所以 `assets/` 下的文件不会被输出到 `public/`，放错位置会直接破图。
`assets/` 只放 SCSS 这类需要被 Hugo 编译的资源。

### 2. 语言代码要跟 i18n 文件名对齐

主题的简体中文文件叫 `zh-cn.toml`，所以配置里必须写：

```toml
defaultContentLanguage = "zh-cn"
```

写成 `zh` 或 `zh-cn` 之外的组合，界面文案会全部变空，而且**不会报任何错**。

### 3. 文章要放在 content/posts/

主题给 `posts` 这个 section 单独写了列表页和分页模板。
文章放在 `content/post/`（少个 s）能渲染，但会丢掉分页和该section 的专用样式。

### 4. 文章的日期不能写未来

Hugo 默认 `buildFuture = false`，日期晚于当前时间的文章会被**静默排除**，
构建不报错、列表页也不显示，很容易怀疑是别的地方出了问题。

## 配置要点

主题的参数集中在 `[params]` 下，几项比较常用：

```toml
[params]
author = "你的名字"
description = "一句话介绍"
info = ["标签一", "标签二"]   # 显示在头像下方
avatarURL = "/img/avatar.svg"
colorScheme = "auto"          # auto / light / dark
customSCSS = ["scss/custom.scss"]
```

## 自定义样式

放 `assets/scss/custom.scss`，在 `hugo.toml` 里用 `customSCSS` 引入。
它会被编译成独立的 CSS 文件，在主题样式**之后**加载，所以可以直接覆盖。

唯一要注意的是暗色模式：主题把暗色样式写在 `body.colorscheme-dark` 下，
特异性比裸 `body` 高，自定义暗色样式时必须用同样的选择器才能生效。

## 中文字体

中文站直接用系统字体（雅黑/苹方）能跑起来，但观感偏旧。这个站用的是
**Noto Sans SC**（思源黑体，SIL OFL 许可，可自由分发）的本地子集。

完整字体 16.9MB，直接挂到网页上不现实，所以做了子集化：

```bash
# 首次：下载源字体（只需一次）
curl -L -o NotoSansSC-VF.ttf \
  "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"

# 生成子集（约 1.8MB）
python tools/subset-font.py NotoSansSC-VF.ttf
```

脚本里的取舍：只按「当前站点用到的字」取子集体积最小，但以后写新文章会缺字，
回退到系统字体后中西文观感割裂；所以这里取「站点实际用字 + GB2312 全集 6763 常用汉字」，
一次生成长期够用。

**新增文章后要重新跑一次脚本**，否则新出现的字（尤其是 GB2312 之外的生僻字）
会回退到系统字体。

用的是可变字体，一个文件覆盖 100–900 全部字重，标题的 700 和正文的 400
共用同一份，不会重复下载。

## 首页的文章列表

hugo-coder 的首页只有个人简介，文章列表单独放在 `/posts/`。
想在首页也列出文章，可以覆盖扩展点 `layouts/_partials/home/extensions.html`。

注意它位于 `.container.centered`（`display: flex`）内部，
自己再套一层 `container centered` 会和简介区**并排**，而不是上下排列。

## 发布到 GitHub Pages

仓库里的 `.github/workflows/deploy.yml` 会在推送到 `master` 时触发，
依次完成：拉代码（同时初始化 `themes/` 下的 submodule）→ 构建 → 发布。

首次使用需要在仓库 **Settings → Pages → Build and deployment** 里
把 Source 选成 **GitHub Actions**。

`baseURL` 不用手改：CI 会自动注入真实的 `base_url`。

## 站点信息

身份信息集中在两处：`hugo.toml` 里的 `title`、`params.author` 和社交链接，
以及 `content/about.md` 里的署名。

配置里别留占位符。`baseURL` 写错会直接构建失败或链接全 404，
但 `title`、`params.author` 这类只影响显示，写错了也不会有任何报错，
很容易漏到上线之后才发现——所以配置完最好 `hugo server` 看一眼首页和标签页。