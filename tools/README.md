# 輔助工具

目前提供 check_docs.py：檢查 Markdown 的本地連結與標題錨點，不存取外部網站。

## 本機執行

Python 3.10 以上，不需第三方套件。在 repo 根目錄執行：

~~~bash
python tools/check_docs.py
~~~

電腦使用 python3 命令時，改用 `python3 tools/check_docs.py`。成功時退出碼為 0；找到缺少的目標或錯誤錨點時為 1，輸出會指出來源文件與問題連結。

## GitHub 執行

.github/workflows/docs-check.yml 會在 push、pull_request 或手動觸發時執行同一支腳本，工作流程名稱為 Documentation，job 名稱為 docs-links。要把它設為 main 的必要檢查，需在 GitHub 的分支保護中另外設定。

## 範圍與限制

- 支援行內連結與圖片、參考式連結、# 開頭的標題，以及明確的 HTML id／name。
- 跳過程式碼區塊與外部網址；不檢查 setext 標題與複雜的 HTML 連結。
- 這項檢查不驗證程式功能、電路正確性或系統適用性。

未來增加建置、解碼或分析工具時，補充輸入、輸出、相依與執行方式，使用可設定路徑；臨時產物放 output/。
