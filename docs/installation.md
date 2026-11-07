# 環境設定

狀態：初始化階段。

## 目前需求

- Git 與自己的 GitHub 帳號。
- 能編輯 UTF-8 Markdown 的文字編輯器。
- 要推送團隊 repo 時，需要適當的寫入權限與自己的認證設定。

Windows 可用 Git Bash 操作 Git；編輯器可自行選擇。先確認：

```bash
git --version
```

目前只有文件與協作模板，沒有韌體建置、燒錄或 GUI 啟動步驟。

## 第一次取得專案

由維護者提供真實 repo 網址。下方 YOUR_ACCOUNT 與 2027RTC-avionics 必須替換為實際值：

```bash
git clone https://github.com/YOUR_ACCOUNT/2027RTC-avionics.git
cd 2027RTC-avionics
git config user.name "你的名字"
git config user.email "你的 Email"
git remote -v
git status
```

這裡的姓名與 Email 只套用於本機這個 repo。Email 使用願意與提交紀錄關聯的地址，也可採用 GitHub 提供的 noreply 地址。clone 可以取得內容，push 仍需權限與自己的認證。

若你是第一位建立 repo 的維護者，使用 [初始化指南](repo_setup.md)。不要在已 clone 的 repo 重新 git init。

## 之後加入的工具

實作開始後，各目錄 README 應記錄：

| 位置 | 待補內容 |
| --- | --- |
| [hardware/](../hardware/README.md) | EDA 工具版本、零件庫與開啟步驟 |
| [firmware/](../firmware/README.md) | MCU、工具鏈、建置命令與輸出位置 |
| [ground_station/](../ground_station/README.md) | 語言版本、相依與主要啟動入口 |
| [mechanical/](../mechanical/README.md) | CAD 工具版本、外部引用與組立入口 |
| [tests/](../tests/README.md) | 測試相依、執行方式與通過條件 |

尚未決定的工具保持待確認。有新工具時先確認其他成員能重現，再把流程寫入文件。

下一步：[快速開始](usage.md)。

若要本機執行文件檢查，需要 Python 3.10 以上，無額外套件；見 [自動檢查](automation.md)。
