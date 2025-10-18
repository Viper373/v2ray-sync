# V2RayN 配置自动同步到 GitHub Gist

一个自动将 V2RayN 配置文件从 WebDAV 同步到 GitHub Gist 的工具，支持定时自动更新和手动触发。

## 🚀 功能特性

- ✅ 自动从 WebDAV 下载 V2RayN 备份文件
- ✅ 解析数据库并生成各种协议的订阅链接
- ✅ 自动上传到 GitHub Gist
- ✅ 支持定时同步（每12小时）
- ✅ 支持手动触发
- ✅ 完全自动化，无需人工干预

## 📋 前置要求

1. **V2RayN 备份**：确保 V2RayN 已开启自动备份到 WebDAV
2. **GitHub 账户**：用于存储 Gist 订阅
3. **WebDAV 服务**：用于存储 V2RayN 备份文件

## ⚙️ 快速开始

### 第一步：Fork 此仓库

点击右上角的 "Fork" 按钮，将此仓库复制到你的账户下。

## 🔧 配置步骤

### 1. 配置仓库 Secrets

进入你的 GitHub 仓库 → **Settings** → **Secrets and variables** → **Actions**

点击 **New repository secret** 添加以下三个 secret：

| Secret 名称         | 说明                   | 示例                                   |
|-------------------|----------------------|--------------------------------------|
| `WEBDAV_URL`      | WebDAV ZIP 文件的完整 URL | `https://your-webdav.com/backup.zip` |
| `WEBDAV_USERNAME` | WebDAV 用户名（如无需认证可留空） | `your_username`                      |
| `WEBDAV_PASSWORD` | WebDAV 密码            | `your_password`                      |

### 2. 手动触发首次同步

1. 进入你的 GitHub 仓库
2. 点击 **Actions** 标签页
3. 选择 **Sync V2RayN Config to Gist** 工作流
4. 点击 **Run workflow** 手动执行

## 🔄 工作流程

### 自动定时同步

- **频率**：每6小时自动运行一次
- **时间**：UTC 时间 00:00, 06:00, 12:00, 18:00
- **无需任何操作**，系统会自动执行

### 手动同步

任何时候需要立即更新订阅时，都可以手动触发工作流。

## 🎯 输出结果

同步完成后，你会获得：

1. **订阅链接**：`https://gist.githubusercontent.com/.../subscription.txt`
2. **可读格式**：包含所有节点的详细信息和分组统计

## 🔍 查看订阅

1. 进入 GitHub Gist 页面 (https://gist.github.com/)
2. 找到名为 "V2Ray 订阅 - 更新: {时间}" 的 Gist
3. 点击 **Raw** 获取订阅链接

**开始使用**：Fork 此仓库 → 配置 Secrets → 手动触发首次同步

就是这么简单！🎉