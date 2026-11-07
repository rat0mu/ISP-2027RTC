# 新成員初始化指南

團隊 repo 已經建立。本指南給新加入的成員，說明第一次在自己電腦上準備專案的步驟：取得專案、設定提交身分、確認內容與權限。完成後接著看 [快速開始](usage.md) 走第一個任務。

不需要自己建立 repo、執行 git init 或推送初始提交；這些已由維護者完成。

## 1. 準備帳號與工具

- 自己的 GitHub 帳號，並把帳號名稱告訴維護者，請他邀請你成為協作者。
- 收到邀請後，到 GitHub 或 Email 接受邀請；接受前只能 clone 公開內容，無法推送分支。
- 安裝 Git，Windows 可使用 Git Bash 或 VS Code 終端機。工具需求詳見 [環境設定](installation.md)。

確認 Git 可以使用：

~~~bash
git --version
~~~

## 2. 取得專案

在要放專案的資料夾開啟終端機：

~~~bash
git clone https://github.com/rat0mu/ISP-2027RTC.git
cd ISP-2027RTC
~~~

若維護者提供的是其他網址或 SSH 網址，以維護者提供的為準。

建議不要放在 OneDrive、Google Drive 等同步資料夾內，避免同步程式與 Git 同時修改檔案造成衝突。

已經 clone 過的 repo 不要再執行 git init，也不要重新 clone 到同一位置覆蓋。

## 3. 設定提交身分

~~~bash
git config user.name "你的名字"
git config user.email "你的 Email"
~~~

這組姓名與 Email 只套用於本機這個 repo，會出現在提交紀錄中，不是 GitHub 登入認證。Email 使用願意公開與提交關聯的地址，也可採用 GitHub 提供的 noreply 地址。

push 時使用你自己的 GitHub 認證；遇到登入或權限錯誤，先看完整訊息，再確認是否已接受協作邀請。

## 4. 確認本機內容

~~~bash
git remote -v
git status
git branch --show-current
~~~

確認：
- origin 指向團隊 repo。
- 目前分支為 main，且工作區乾淨。
- 根目錄可看到 README.md、CONTRIBUTING.md、docs/、hardware/、firmware/ 等目錄。
- .github/、.gitignore、.gitattributes、.editorconfig 也存在。部分檔案總管預設隱藏點開頭的檔案，可用 `ls -a` 確認。

## 5. 本機文件檢查（選用）

若已安裝 Python 3.10 以上，在 repo 根目錄執行：

~~~bash
python tools/check_docs.py
~~~

看到 `[OK]` 與 0 errors 表示文件連結正常。只編輯文件時不一定要先安裝 Python，也可看 PR 上的遠端檢查結果；實際審查仍需閱讀內容。詳見 [自動檢查](automation.md)。

## 6. 閱讀必要文件

開始第一個任務前，依序閱讀：
1. [README](../README.md)：專案概要與開發流程。
2. [協作規範](../CONTRIBUTING.md)：分支、提交、PR 與審查要求。
3. [團隊分工](team.md)：確認自己負責的模組與審查人。
4. 自己負責模組的目錄 README。

尚未決定的 MCU、腳位與工具版本以各文件標示的狀態為準，不要依範例自行假設。

## 7. 完成第一個任務

依照 [快速開始](usage.md) 承接 Issue、開分支、修改、commit、push 並建立 PR。建議起始任務見 [首次工作清單](first_tasks.md)。

## 如果偏好圖形介面

可以使用 GitHub Desktop 的 Clone repository 功能取得專案，登入自己的 GitHub 帳號後即可提交與推送。仍需在設定中確認提交使用的姓名與 Email，並確認 origin 指向團隊 repo。

## 官方參考

- [Clone 儲存庫](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
- [設定提交 Email](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address)
- [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)
