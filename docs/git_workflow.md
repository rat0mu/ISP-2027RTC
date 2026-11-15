# Git 工作流程

本文件提供操作與說明；協作要求以 [CONTRIBUTING.md](../CONTRIBUTING.md) 為準。

## 每日開發流程

### 情境 A：開始一個新任務

先確認工作區狀態。若還有別項工作，先提交到原分支或依協作安排保存，再切換。

```bash
git status
git switch main
git pull --ff-only origin main
git switch -c docs/onboarding-guide
```

docs/onboarding-guide 是示範任務分支，請依自己的任務取名。--ff-only 遇到本機與遠端分岔時會停止；先檢查原因，不用強制覆寫處理。

### 情境 B：繼續昨天的任務

```bash
git status
git switch docs/onboarding-guide
git pull --ff-only
```

最後一行適用於已設定遠端追蹤的分支。第一次推送前尚未設定追蹤時，先確認分支狀態，無須執行這行。

要把團隊 main 的新內容帶進目前任務分支，在妥善提交工作後：

```bash
git fetch origin
git merge origin/main
```

同步自己的任務分支與整合 main 是不同動作。功能分支已由多人共用時，不隨意改寫已推送的歷史。

### 修改完成後：檢查、提交、推送

以本次只修改根目錄 README.md 為例：

```bash
git status
git diff

git add README.md
git diff --cached

git commit -m "docs: 補充新人操作說明"
git push -u origin docs/onboarding-guide
```

- git add 選定此次要提交的內容。
- git diff --cached 檢查已選定的內容。
- git commit 在本機建立版本紀錄。
- git push 把提交推到遠端分支。
- 第一次 push 使用 -u 設定追蹤；之後在同一分支可使用 git push。

將 git add README.md 改成自己的實際修改檔案。新增檔案不會出現在一般 git diff 的差異中，請一起看 git status 與暫存後的 diff。圖形檔還需要開啟檢查與必要畫面。

### 建立 PR 並回應意見

在 GitHub 將任務分支提出合併至 main：

- Base：main。
- Compare：本次任務分支。
- 填寫 PR 模板，連結相關 Issue。
- 指定另一位成員審查。
- 依意見修改後，繼續 commit 並 push 同一分支，PR 會隨之更新。

尚未完成時可先開 Draft PR，讓相關成員提早確認方向。無法完成的部分清楚列出，必要時拆成後續任務。

### 合併後同步

```bash
git switch main
git pull --ff-only origin main
```

確認成果已整合後，再清理已完成的分支。新任務重新從最新 main 開始。分支清理與 squash merge 的注意事項見 [協作規範](../CONTRIBUTING.md)。


## 分支與提交命名

### 分支

目前只規劃 main 作為長期整合分支。每項任務使用短期分支；需要其他長期分支時，先說明用途與維護方式。

| 前綴 | 用途 | 範例 |
| --- | --- | --- |
| docs/ | 文件與教學 | docs/onboarding-guide |
| hardware/ | 電路、PCB 與零件庫 | hardware/power-review |
| firmware/ | MCU 功能 | firmware/sensor-driver |
| ground/ | PC 地面站 | ground/packet-view |
| mechanical/ | CAD 與裝配 | mechanical/mount-review |
| fix/ | 修正既有問題 | fix/parser-boundary |
| test/ | 測試 | test/decoder-cases |
| experiment/ | 尚未確定採用的實驗 | experiment/filter-comparison |
| chore/ | 儲存庫與工具維護 | chore/ignore-rules |

避免 test2、mybranch、final_final 等無法辨識目的的名稱。任務編號可加入分支名，方便追溯，例如 docs/12-onboarding-guide。

### Commit

採用「類型: 修改目的」：

```text
docs: 補充新人操作說明
feat: 新增資料匯出功能
fix: 修正解析器的邊界處理
test: 增加不完整封包測試案例
refactor: 抽出共用資料轉換函式
chore: 調整本機產物忽略規則
```

以上是格式範例。描述應對應實際成果，避免只寫 update、push 或 done。一次提交盡量有完整且清楚的目的；搬移檔案與功能修改盡量分開。


## 常見問題

### commit 與 push 有什麼不同？

commit 是本機版本紀錄，push 才把提交傳到遠端。push 到任務分支後，成果仍需經 PR 合併才會進入 main。

### git pull origin main 會切到 main 嗎？

不會。它會取得遠端 main 並整合進目前所在分支。先用 git branch --show-current 確認位置；要更新本機 main，先切換至 main。

### git push 失敗怎麼辦？

先讀完整錯誤，確認是版本落後、權限、認證、分支名稱、保護規則或檔案限制。不要一律重複 pull，也不要用 force push 覆蓋共同分支。

若是同一任務分支遠端已有新提交，先確認自己的工作已保存，再整合該分支；若 main 更新，使用 fetch 後將 main 整合進任務分支。

### 發生 merge 衝突怎麼辦？

用 git status 找衝突檔，理解兩邊改動後解決，再檢查、暫存與完成 merge。程式重新建置／測試；硬體與機構重新開啟檢查。需要取消尚未完成的 merge 可用 git merge --abort。開始整合前先保存既有工作。

### 不小心把檔案加入暫存，還沒 commit，怎麼取消？

```bash
git restore --staged README.md
```

把 README.md 換成實際路徑。此操作取消暫存，保留工作目錄的修改。

### 目前沒有測試程式，PR 要怎麼填？

文件任務可記錄連結檢查、閱讀審查或操作演練。若某類測試不適用，說明原因；若需要但還沒做，標明尚未執行。之後有實作再補適當測試。


返回 [文件索引](README.md)。
