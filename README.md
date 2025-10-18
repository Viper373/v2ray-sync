# V2RayN 配置自动同步到 GitHub Gist

一个自动将 V2RayN 配置文件从 WebDAV 同步到 GitHub Gist 的工具，支持定时自动更新和手动触发。

## 🚀 功能特性

- ✅ 自动从 WebDAV 下载 V2RayN 备份文件
- ✅ 解析数据库并生成各种协议的订阅链接 (VMess, VLESS, Trojan, Hysteria2, etc.)
- ✅ 自动创建或更新 GitHub Gist
- ✅ 支持定时同步（每12小时）
- ✅ 支持手动触发
- ✅ 完全自动化，无需人工干预

## 📋 前置要求

1. **V2RayN 备份**：确保 V2RayN 已开启自动备份到 WebDAV。
2. **GitHub 账户**：用于存储 Gist 订阅。
3. **WebDAV 服务**：用于存储 V2RayN 备份文件。

## 🔧 配置步骤

请按照以下步骤完成配置，仅需操作一次。

### 第 1 步：Fork 此仓库

点击右上角的 "Fork" 按钮，将此仓库复制到你的账户下。

### 第 2 步：创建 GitHub Personal Access Token (PAT)

这是**必须的步骤**，用于授权脚本创建和更新 Gist。

1. 访问 [GitHub Developer settings > Personal access tokens](https://github.com/settings/tokens)。
2. 点击 "Generate new token (classic)"。
3. 勾选 `gist` 权限。**这是关键**，请勿遗漏。
4. 点击 "Generate token"。
5. **立即复制生成的令牌**，该令牌只会显示一次。

### 第 3 步：配置仓库 Secrets

进入你 Fork 后的仓库 → **Settings** → **Secrets and variables** → **Actions**，然后点击 **New repository secret** 添加以下四个 secret：
| Secret 名称 | 说明 | 示例 |
|-------------------|--------------------------------|-----------------------------------------------|
| `WEBDAV_URL`      | WebDAV ZIP 文件的完整 URL | `https://your-webdav.com/backup.zip`          |
| `WEBDAV_USERNAME` | WebDAV 用户名（如无需认证可留空） | `your_username`                              |
| `WEBDAV_PASSWORD` | WebDAV 密码 | `your_password`                              |
| `GIST_TOKEN`      | **第 2 步创建的 PAT**            | `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

### 第 4 步：手动触发首次同步

1. 进入你的 GitHub 仓库。
2. 点击 **Actions** 标签页。
3. 选择左侧的 **配置文件同步至Gist** 工作流。
4. 点击 **Run workflow** → **Run workflow** 手动执行一次。
   首次运行成功后，脚本会创建一个新的 Gist，并将 Gist ID 保存起来，供后续自动更新使用。

## 🔄 工作流程

### 自动定时同步

- **频率**：每12小时自动运行一次。
- **时间**：UTC 时间 00:00, 12:00 (对应北京时间 08:00, 20:00)。
- **无需任何操作**，系统会自动执行。

### 手动同步

任何时候需要立即更新订阅时，都可以通过第 4 步的方式手动触发工作流。

## 🎯 输出结果

同步完成后，脚本会在 Gist 中创建两个文件：

1. `subscription.txt`：包含所有节点 Base64 编码后的标准订阅链接。
2. `nodes_readable.txt`：包含所有节点的原始链接和分组信息，方便查看。

## 🔍 如何获取订阅链接

### 方法一：从 Actions 日志获取 (推荐)

1. 进入仓库的 **Actions** 页面。
2. 点击最新的一次运行记录。
3. 展开 **Run sync script** 步骤的日志。
4. 日志中会直接打印出订阅链接，格式如下：
   ```
   ✅ 同步成功!
   📡 订阅链接: https://gist.githubusercontent.com/.../subscription.txt
   ```

### 方法二：从 Gist 页面获取

1. 进入 GitHub Gist 页面 (https://gist.github.com/)。
2. 找到名称为 "V2Ray 订阅 - 更新: {时间}" 的 Gist。
3. 点击 `subscription.txt` 文件右上角的 **Raw** 按钮，复制地址栏中的链接即可。

---
**开始使用**：Fork 仓库 → 创建 PAT → 配置 Secrets → 手动触发首次同步
就是这么简单！🎉