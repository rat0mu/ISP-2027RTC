# 專案結構與資料

本文件提供操作與說明；協作要求以 [CONTRIBUTING.md](../CONTRIBUTING.md) 為準。

## 目前狀態與文件效力

| 項目 | 目前狀態 | 後續更新位置 |
| --- | --- | --- |
| Repo 目錄與協作規範 | 已建立起始模板，待團隊確認採用 | 本文件、[CONTRIBUTING.md](../CONTRIBUTING.md) |
| 人員分工 | 待指定 | [docs/team.md](team.md) |
| 硬體與系統架構 | 待確認 | [docs/architecture.md](architecture.md) |
| 電氣、資料與機構介面 | 待確認 | [docs/interfaces.md](interfaces.md) |
| MCU、EDA 與開發工具版本 | 待確認 | 各實作目錄的 README |
| 韌體與地面站 | 尚未實作 | firmware/、ground_station/ |
| 測試程式與結果 | 尚未建立 | [tests/README.md](../tests/README.md) |
| 文件 CI | 已附工作流程，待首次遠端執行 | [自動檢查](automation.md) |
| GitHub 分支保護 | 需維護者手動設定 | GitHub 儲存庫設定 |
| 專案授權 | 待決定 | 本文件，選定後新增 LICENSE |

本手冊 提供共同入口與操作說明；完整協作細節以 [CONTRIBUTING.md](../CONTRIBUTING.md) 為準。規範變更應透過 PR 同步調整相關文件，避免同一件事存在兩套互相矛盾的說法。

文件與實作不一致時，應建立 Issue 記錄差異，由相關負責人確認；不要只依某一份較舊文件或個人記憶做跨模組變更。


## 檔案放置方式

| 位置 | 用途 | 加入第一份實作時應補充 |
| --- | --- | --- |
| [hardware/](../hardware/README.md) | 原理圖、PCB、必要 Symbol／Footprint／模型與硬體說明 | 現行專案入口、工具版本、板版號與檢查狀態 |
| [firmware/](../firmware/README.md) | MCU 韌體、硬體設定與建置入口 | MCU、對應板版號、工具鏈、建置方式與輸出位置 |
| [ground_station/](../ground_station/README.md) | PC 端連線、解碼、GUI 與操作說明 | 主要啟動入口、相依環境、相容協定版本 |
| [mechanical/](../mechanical/README.md) | 航電艙、固定件、CAD、裝配與接口尺寸 | 現行 CAD 入口、工具版本、尺寸基準與外部引用 |
| docs/ | 現行架構、介面、分工、規範與決策 | 文件狀態、適用版本與負責人 |
| [tests/](../tests/README.md) | 可重複執行的測試與小型必要輸入 | 執行命令、通過條件與已知限制 |
| [tools/](../tools/README.md) | 建置、檢查、解碼與分析腳本 | 使用方式、輸入、輸出與相依 |
| .github/ | GitHub Issue、PR 模板與後續自動檢查設定 | 模板更新原因及實際生效條件 |

### 目錄增加原則

- 目前先保留一層分類，每個工作目錄已有 README，因此 Git 能保留這些目錄。
- 有明確用途與實際內容後，再增加子目錄。
- 正式來源依功能或子系統命名；人員歸屬記錄在分工文件與 Issue。
- 確定主備硬體與 MCU 後，再決定各自的專案位置與共用範圍。
- 有停用成果時才新增 archive/，並寫明停用原因與替代來源。
- 新增或搬移檔案時，同步修正相關連結、模型與零件庫路徑。


## 檔案與資料管理

### 命名與路徑

- 目錄與一般來源檔建議英文小寫 snake_case，避免空格。
- README.md、CONTRIBUTING.md 等慣例名稱維持原樣。
- 資料與數值應標明單位、座標或時間基準。
- 團隊共用資產使用 repo 相對路徑，避免個人 C:/Users/... 或 /Users/... 路徑。
- 本機設定放在被忽略的設定檔；需要時提供 example。
- 正式來源避免以人名或 latest、new、final 命名。

### 哪些檔案保留

| 類別 | 原則 |
| --- | --- |
| 原理圖、PCB、來源 CAD、程式 | 進版本控制，入口清楚 |
| 必要 Symbol、Footprint、模型 | 依來源與授權保存，確保可開啟 |
| 小型必要測試 CSV 與校正資料 | 可進版本控制，記錄用途與來源 |
| 正式製造輸出與測試報告 | 對應來源版本，依發布方式保存 |
| 臨時 log、可重生圖表與分析輸出 | 放指定產出目錄，預設忽略 |
| 編譯中間檔、快取、自動備份 | 忽略 |
| 個人設定與認證資訊 | 使用本機設定管理 |

目前不全域忽略 CSV、BOM 或 Gerber，避免把需要交接的資料一併排除。大型原始資料與二進位資產加入前，先確認必要性、大小、引用關係與保存方式；如有需要，再評估專門的資產管理方式。

.gitignore 不會自動取消既有追蹤。整理備份目錄前先確認沒有 Symbol、模型或設定仍被引用。請見 [工程基本規則](engineering_rules.md)。


返回 [文件索引](README.md)。
