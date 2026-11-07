# 協作規範

狀態：起始規範 v0.1，供團隊討論採用。

## 1. 先有任務，再開始修改

使用 Task Issue 模板，寫清楚目的、範圍、交付物、驗收條件、執行者與審查人。討論與結論回寫 Issue，避免只留在聊天訊息。

新加入的成員可先承接文件、零件庫核對或小型工具任務，走完一次 PR 流程。

## 2. 分支

main 為長期整合分支。其他分支以任務命名，避免長期個人分支與 final_final 類型名稱。

| 前綴 | 用途 | 範例 |
| --- | --- | --- |
| docs/ | 文件 | docs/setup-guide |
| hardware/ | 電路與 PCB | hardware/power-review |
| firmware/ | MCU 功能 | firmware/sensor-driver |
| ground/ | 地面站 | ground/packet-view |
| mechanical/ | 機構 | mechanical/mount-review |
| fix/ | 修正問題 | fix/parser-boundary |
| test/ | 測試 | test/decoder-cases |
| experiment/ | 尚未決定採用的實驗 | experiment/filter-comparison |
| chore/ | 維護 | chore/ignore-rules |

同一任務可由數人合作，但先指定分支負責人。對共用分支不隨意改寫歷史或 force push。

## 3. 開始任務

先用 git status 確認工作區狀態，提交或妥善保存既有工作後再切換。

```bash
git status
git switch main
git pull --ff-only origin main
git switch -c docs/setup-guide
```

以上假設 origin 是團隊 repo，且你有分支推送權限。若無權限，由組長加入協作者或另行約定 fork 工作流，不向他人索取登入憑證。

--ff-only 失敗時先確認本機與遠端的分岔原因。git pull origin main 會整合進「目前分支」，不會自動切換到 main。

## 4. 提交與推送

```bash
git status
git diff
git add README.md
git diff --cached
git commit -m "docs: 補充新人操作說明"
git push -u origin docs/setup-guide
```

加入實際修改的檔案；commit 前檢查暫存內容。KiCad 與機構檔另外開啟檢查，必要時提供前後畫面。

Commit 格式：類型: 明確描述。可用 feat、fix、docs、test、refactor、chore。避免 update、push、final 等無法辨識目的的訊息。

一次提交盡量是一個完整改動。純搬移、格式整理與功能變更盡量分開。

## 5. 同步進行中的分支

在任務分支提交目前成果後，再整合最新 main：

```bash
git fetch origin
git merge origin/main
```

若有衝突，理解兩邊目的後解決。對程式重新建置／測試，對電路重新開啟並檢查。需要取消尚未完成的 merge 時使用 git merge --abort。不要用強制覆寫來掩蓋衝突。

## 6. PR 與審查

- 尚在進行可先開 Draft PR。
- 填寫 PR 模板：問題、改動、驗證、介面影響與未完成項。
- 至少由一位其他成員審查。介面改動請相關模組負責人確認。
- 無適用測試可寫「不適用」並解釋；缺乏驗證就寫「尚未執行」，不能標為通過。
- 文件初始化 PR 可用閱讀、連結與操作演練驗收。
- 自動檢查建立後，將可信的必要檢查納入合併條件。
- 由具權限的維護者確認驗收後合併。初始建議使用 squash merge，保留清楚的 PR 標題與說明。

PR 提交後繼續推送同一分支即可更新 PR，不必每次重新開一個。

## 7. 合併之後

```bash
git switch main
git pull --ff-only origin main
```

確認成果已整合後清理任務分支。GitHub 可在合併後刪除遠端分支。squash merge 後本機 git branch -d 可能因歷史判定拒絕；先確認合併內容，不把強制刪除當預設操作。

## 8. 硬體與機構協作

- 同一張 PCB 同時間指定一位編輯者；分支不能自動解決幾何與電氣衝突。
- 原理圖可依模組分工，頂層連接與元件編號由整合負責人協調。
- 變更附上修改位置、畫面、介面影響及 ERC／DRC 結果或尚未執行原因。
- 工具版本確認後寫入該目錄 README；升級前先討論。
- 正式製造檔與測試紀錄需要對應來源版本。

## 9. 版本與回復

main 上的改動需要保持可追溯。共同分支若需撤回，透過 PR 提交修正或適當 revert；merge commit 的回復由熟悉影響的人處理。

起始模板與 main 都不代表完成硬體、整機或飛行驗證。里程碑發布時再記錄硬體版號、韌體 commit、地面站版本、組態與驗證證據。
