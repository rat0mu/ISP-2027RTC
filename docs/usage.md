# 快速開始

這份指南協助新成員走完第一個任務。目前可使用小型文件任務演練，不需電路板或編譯器。

## 1. 確認環境與分工

依照 [環境設定](installation.md) 取得專案，再閱讀 [協作規範](../CONTRIBUTING.md) 與 [團隊分工](team.md)。

確認 origin 指向正確的團隊 repo，並且有分支推送權限。沒有權限時聯絡維護者。

## 2. 承接一項可驗收的任務

在 GitHub 建立或承接 Issue，確認目的、交付物、驗收條件、執行者與審查人。

初期任務範例：補充新人環境說明，讓另一位成員依文件完成一次提交與 PR。

## 3. 建立任務分支

工作區已有修改時先提交或妥善保存，再執行：

```bash
git status
git switch main
git pull --ff-only origin main
git switch -c docs/setup-guide
```

## 4. 修改、檢查與提交

以下以修改 README.md 為例：

```bash
git diff
git add README.md
git diff --cached
git commit -m "docs: 補充新人環境說明"
git push -u origin docs/setup-guide
```

git add 要使用本次實際修改的路徑。新增檔案一起看 git status；圖形成果另外開啟檢查。

## 5. 建立 PR

在 GitHub 選擇 base 為 main，compare 為 docs/setup-guide，填寫 PR 模板並指定另一位成員審查。

依意見修改後繼續 commit、push 同一分支即可更新 PR。尚未完成時可開 Draft PR。

## 6. 合併與同步

具權限的維護者確認驗收後合併。回到本機執行：

```bash
git switch main
git pull --ff-only origin main
```

完成後清理任務分支；新任務從最新 main 開始。

- 日常操作與分支命名：[Git 工作流程](git_workflow.md)。
- 成果要求與驗收：[任務與審查](collaboration.md)。
- 操作問題：[常見問題](troubleshooting.md)。
