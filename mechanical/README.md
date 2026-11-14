# 機構

狀態：概念模型 avbay v0.10（單段設備艙加外側安裝面、束線柱、可拆頂蓋與軟質天線；電池直立、兩顆一組沿 X 前後排列並加螺絲側蓋；920 MHz 天線掛在側面；板間距 11.81，配合 Samtec SFM／TFM 板對板堆疊接頭），尚未審查，尺寸未定案。

放航電艙、固定件、CAD、裝配與接口尺寸。

- CAD 工具：SOLIDWORKS 2018 SP3。
- 現行來源檔與組立入口：[cad/](cad/README.md) 的 `avbay_v0_10_assembly.SLDASM`；裝入鼻錐的檢查組合件由 `fitcheck_nose.py` 產生。
- 對應板版號：尚未建立；PCB 外形為直徑 110 的馬蹄形板，開槽與孔位見 [cad/README.md](cad/README.md)。
- 來源 CAD 與輸出 STEP／STL 的對應關係：尚未輸出。
- 外部引用與模型來源：鼻錐 `cad/NOSE_v1.SLDPRT` 由團隊提供；其餘無外部引用。
- 裝配檢查與驗證狀態：僅完成 CAD 干涉檢查（航電艙內部、以及裝入 NOSE_v1），其餘見 [cad/README.md](cad/README.md)。

採用明確版號，避免 final、new、latest 等難以追溯的檔名。尺寸變更通知硬體負責人。
