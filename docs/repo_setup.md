# 在 GitHub 建立這個專案

本包已含完整的起始檔案與文件檢查工作流程。第一次建立採用「建立空白遠端 → 解壓 → 本機初始化 → 推送」的順序。

## 1. 建立空白 GitHub repo

登入自己的 GitHub，建立新儲存庫：

| 欄位 | 建議 |
| --- | --- |
| Owner | 你的帳號或團隊組織 |
| Repository name | 2027RTC-avionics，可自行調整 |
| Description | 2027 台灣盃火箭航電開發：硬體、韌體、地面站與文件 |
| Visibility | 團隊決定 Public 或 Private |
| README／.gitignore／License 初始化 | 此次先不由 GitHub 產生，使用本包檔案 |

建立後取得 HTTPS 或 SSH repo 網址。以下範例使用 HTTPS，請將 YOUR_ACCOUNT 與名稱改成實際值。

如果遠端已經有 commit，先確認內容與整合方式，不用強制覆寫處理。

## 2. 解壓縮檔案

解壓後進入 2027RTC-repo-starter。正確位置會直接看到 README.md、CONTRIBUTING.md、hardware/ 與 docs/。

確認 .github/、.gitignore、.gitattributes、.editorconfig 也存在。不要把 ZIP 檔本身上傳當作完整 repo；GitHub 需要其中的來源檔案。

## 3. 開啟終端機並設定初始提交

Windows 可在此目錄開啟 Git Bash 或 VS Code 終端機。以下指令適用尚未 git init 的解壓目錄：

~~~bash
git init -b main
git config user.name "你的名字"
git config user.email "你的 Email"

git add .
git status
git diff --cached --stat
git commit -m "chore: 建立 2027RTC 專案架構與協作規範"

git remote add origin https://github.com/YOUR_ACCOUNT/2027RTC-avionics.git
git remote -v
git push -u origin main
~~~

姓名／Email 是提交身分，不是 GitHub 登入認證。push 使用你自己的認證設定；遇到錯誤先看完整訊息。若 GitHub 提示登入或缺少權限，處理帳號與權限後再推送。

第一次使用前可在 docs/team.md 填入維護者，其他未定欄位保留待確認。尚未決定的 MCU、腳位與工具版本不用先填猜測值。

## 4. 檢查第一次推送

在 GitHub repo 確認：
- 根目錄直接顯示精簡 README。
- docs/README.md 可以開啟，連到各主題。
- .github/ 內有 Issue 模板、PR 模板與 workflows/docs-check.yml。
- Actions 中出現 Documentation 工作流程。若組織限制執行，依實際政策處理。
- docs-links 的結果符合預期。

本包只在本機驗證文件檢查；第一次遠端執行結果須在你建立的 repo 查看。詳見 [自動檢查](automation.md)。

## 5. 邀請組員與分配責任

加入協作者並安排適當權限，在 [team.md](team.md) 填入真實帳號。至少安排主要與備援維護者。

CODEOWNERS.example 目前不生效。確認帳號與權限後填入並改名為 CODEOWNERS；是否要求 code owner 核准，再由團隊決定。

## 6. 設定 main 的保護

初始推送與協作權限確認後，依帳號方案與可用的 ruleset／分支保護功能設定：
- 合併前要求 PR。
- 有其他審查人後，要求至少一位其他成員核准。
- 限制 main 的 force push 與刪除。
- 文件檢查已成功執行後，選取畫面上的 docs-links 作為必要檢查。
- 若使用 CODEOWNERS，再決定是否要求負責人核准。

這些是 GitHub 端設定，檔案存在不會自動建立規則。

## 7. 演練第一個 PR

建議任務：填寫團隊分工或補充新人環境說明。

讓另一位組員從 clone 開始，承接 Issue、開分支、修改、commit、push、建立 PR；另一人確認內容與驗收後合併。

建議起始任務見 [首次工作清單](first_tasks.md)，後續操作見 [快速開始](usage.md)。

## 如果偏好圖形介面

可以使用 GitHub Desktop 的既有本機儲存庫功能，加入上面已初始化的目錄，再依介面登入與推送。仍需確認 origin 指向剛建立的空白 repo。

初次上傳建議 Git 或 GitHub Desktop，以確保點開頭的設定檔與 .github/ 一起提交。

## 本機文件檢查（選用）

若已安裝 Python 3.10 以上，在 repo 根目錄執行：

~~~bash
python tools/check_docs.py
~~~

只有編輯文件時不一定要先安裝 Python；也可依遠端工作流程結果檢查，實際審查仍需閱讀。

## 官方參考

- [建立儲存庫](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
- [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [分支保護](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
