# 開發優化盤點 Backlog

> 2026-11-16 盤點（Phase 1 後首次歸檔）。本文件是**跨階段**的開發與優化清單：README 的 Roadmap 是階段骨架，這裡收集具體工作項、生態整合與工程債。每次盤點時更新；完成的項目移入 Roadmap 對應階段的勾選紀錄。設計層的未決問題仍留在 [DESIGN.md](DESIGN.md) §6——本清單是「要做什麼」，那裡是「怎麼設計」。
> 2026-11-18 方向修訂：M1 降位為拉動即用的消費者整合；四層架構定案（核心／可組合系統／圖書館／轉接器，DESIGN §1）；Phase 2 重排為「統計驗收 → 架構核心 → 內容系統」。
> 2026-11-18 Phase 2 歸檔：population mode、統計驗收 v1、架構核心 v1、策略庫四項完成，勾選紀錄在 README Roadmap；工程補強（py.typed、CI 跨平台矩陣＋釘版、wheel 打包驗證）同日完成。本清單重新盤點為 Phase 3+ 的工作項。

## 1. 生態整合（跨專案）

- **M1「N 個體 × M 世界」的組裝（已降位，2026-11-18）**：從開發里程碑改為**拉動即用的消費者整合**——Unbodysoma `run_population` × 本專案 population mode 兩側基礎設施已就緒（世界側載體 `population.toml` 已定案，剩對方讀取 manifest 的協定），需要行為層回饋時再組裝。**世界詞彙的擴張不等待它。**
- **世界 provenance 進執行紀錄**：Unbodysoma 側要把外部世界的（產生器、preset@版本、種子、SHA-256）寫進 `meta.json`（其 BACKLOG §4）；本專案側確保 TOML 檔頭資訊完整即可（已滿足，追蹤對方進度）。
- **世界群標本**：標本卡已落地（`library.py`，`--fingerprint --json`）；下一步是 specimen-g-code 的世界標本攝入（其 Phase 4 適配器）與跨標本的累積查詢工具。

## 2. 幾何與地形（Phase 3）

- **地形場＋可達性**：高度場（值雜訊即可）影響植放規則與移動成本——abyssal-garden `CLEARS`（淨空保證）的對應物，也是其最值得抄的工程模式（DESIGN 開放問題 2）。以註冊系統形式落地（`S_TERRAIN` id 1 已保留）。
- **資源季節動態**：regrow 速率、水源水量隨季節參數變化（現在是常數）；以註冊系統形式先落核心＋JSON 轉接器，TOML 鍵集（Unbodysoma 端 `FoodPatch` 語意擴充，ADR-0010）跟上即接——過渡期由轉接器能力宣告（DESIGN §4）處理降級，不再擋路。
- **2D → 2.5D**：坡度場先於完整高度場（風險較小、對植放規則已足夠）。

## 3. 內容與分布層（Phase 2 遺留＋後續）

- **archetype 的參數面**：preset 目前是常數組合；族群層的「世界維度變異」（面積、貧瘠度、危險密度連續抽樣）可作為原型之上的分布層。
- **統計驗收的精化**：帶寬隨理論收緊（覆蓋率的獨立圓盤模型已近精確，可先行）；可達性加入圖論量測。
- **更多掠食者策略**：註冊表加一項即可（DESIGN §3）；候選——伏擊（時間空間皆集中）、追蹤（貼近有機體活動熱區）。

## 4. 3D 與前端（Phase 4，abyssal 血統的歸宿）

- **高度場輸出**：3D 密度場的柵格化版本，作為 Phase 3 地形的自然延伸。
- **完整世界 JSON 轉接器**：座標＋場參數，WebGPU 預覽的輸入——完整語彙的參考轉接器（DESIGN §4）。
- **WebGPU 預覽頁**：前端以**同源雜訊常數**重算場來鋪渲染——`scripts/verify_lineage.*` 已證明種子跨語言逐位元共享，預覽頁是這個投資的兌現（DESIGN 開放問題 3）。
- **品質分層**：比照來源專案的自適應策略（動態解析度、繪製距離）——只在預覽頁存在後才有意義（Phase 5）。

## 5. 工程與基礎設施

- **v0.2.0 release tag**：**就緒（2026-11-18）**——Phase 2 四項全落地，版本化契約定案、preset 全部 `@1`。打 tag 即可（`git tag v0.2.0 && git push --tags`）。
- **測試時長**：指紋帶 6 preset × 50 種子約 60 s（套件 ~80 s）；CI 若成負擔可分層（pytest marker 快慢兩速，或調降 N）——目前可接受，先記債。
- **CI 的 Node 作業（選配）**：把 `verify_lineage.mjs` 的跨語言比對納入 CI（需要 node runner；目前是文件化的手動步驟）。風險低但非必要——血統已由 Python 側的 golden 常數（`test_js_lineage`）單向釘死。
- **GitHub repo 的 description／topics**：定案（2026-11-18，本機無 gh 指令待套用）——
  description："Deterministic procedural world generator: seed + preset in, a complete reproducible world out — the habitat half of the Unbodysoma ecosystem."
  topics：`procedural-generation, worldgen, deterministic, simulation, python`。

## 6. 已回答的設計問題（歸檔）

| 舊問題 | 答案 |
|---|---|
| preset 版本化：世界要帶版本資訊嗎？ | 已定案（2026-11-16）：`preset@version` provenance 契約——`Preset.version` bump 制、輸出檔頭標注、DESIGN §2 第 5 點 |
| 世界產生器放哪個專案？（Uniconsign vs Unbodysoma vs 獨立） | 已定案：獨立專案（本專案），邊界見 Unbodysoma ADR-0010 |
| 模板與 Unbodysoma 的程式相依？ | 已定案：零相依——耦合只存在於 TOML 鍵集契約（雙邊測試把關） |
| M1 是開發里程碑嗎？ | 已定案（2026-11-18）：降位為拉動即用的消費者整合；開發節奏以世界詞彙為核心，需要行為回饋時才組裝 |
| 世界架構如何擴張／收縮？ | 已定案（2026-11-18）：四層架構（核心／可組合系統／圖書館／轉接器）；archetype＝系統組合＋參數，重組不改位元組——詳 DESIGN §1、§3、§4 |
| 統計驗收該斷言什麼、界線怎麼定？ | 已定案 v1（2026-11-18）：四項指標；界線＝可執行理論中心×文件化因子，不調到變綠——詳 DESIGN §5 |
| 系統介面與原型 schema？ | 已定案 v1（2026-11-18）：`Generation`／`System{name, stream_id, apply, needs}`／正準序＋組合驗證——詳 DESIGN §3 |
