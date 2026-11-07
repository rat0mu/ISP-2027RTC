# 2027RTC Avionics

2027 台灣盃火箭航電團隊的開發專案，集中管理電路、MCU 韌體、PC 地面站、機構與驗證資料，方便成員協作與交接。

> 目前為初始化階段，已建立目錄與協作規範；系統設計、工具版本與人員分工待確認。

## 需求

- Git、GitHub 帳號與文字編輯器。
- 參與開發時所需的儲存庫權限與審查安排。

各子系統的開發工具將隨實作補充，詳見 [環境設定](docs/installation.md)。

## 使用方式

首次建立儲存庫，請依照 [初始化指南](docs/repo_setup.md) 操作；新成員請從 [快速開始](docs/usage.md) 閱讀。

取得專案後，可先確認本機狀態與目前分支：

```bash
git status
git branch --show-current
```

開發流程：**Issue → 任務分支 → 修改與驗證 → PR 審查 → 合併至 main**。

## 相關文件

- [文件索引](docs/README.md)：目錄用途、架構、介面與團隊分工。
- [協作規範](CONTRIBUTING.md)：分支、提交、PR 與審查要求。
- [測試與版本](docs/testing.md) · [常見問題](docs/troubleshooting.md)。

## 授權

授權待團隊決定；第三方資產保留各自的來源與授權資訊。
