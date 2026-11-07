# 文件自動檢查

本模板包含 .github/workflows/docs-check.yml 與 tools/check_docs.py。它們檢查 Markdown 本地連結與支援的標題錨點，不存取外部網站。

## 本機執行

Python 3.10 以上，不需第三方套件。在 repo 根目錄執行：

~~~bash
python tools/check_docs.py
~~~

若電腦使用 python3 命令：

~~~bash
python3 tools/check_docs.py
~~~

成功退出碼為 0；找到缺少的目標或錯誤錨點時為 1。輸出指出來源文件與問題連結。

## GitHub 執行

提交工作流程後，在允許 GitHub Actions 的 repo 中，push、pull_request 或手動 workflow_dispatch 會觸發 Documentation 工作流程，job 名稱為 docs-links。

- 首次 push 後，到 Actions 確認該次工作流程與結果。
- 若組織限制 Actions 或官方 action，請維護者依實際政策啟用。
- Fork PR 的第一次執行可能需維護者批准。
- 看到成功執行後，再把 docs-links 設為 main 的必要檢查；依畫面顯示名稱選取。
- 使用官方 actions/checkout，固定到已核對的 v7 commit；未來升級透過 PR。

本機腳本驗證不代表已在尚未建立的遠端 repo 執行。

## 範圍與限制

支援一般行內 Markdown 連結／圖片、參考式連結定義的目標、ATX 標題（# 開頭）及明確 HTML id／name。跳過 fenced code block 與外部 URL；不檢查網路可用性、複雜 Markdown／MDX 語法、所有 HTML 連結或 setext 標題。

特殊渲染或語法需人工確認。這項檢查不驗證程式功能、電路正確性或系統適用性。
