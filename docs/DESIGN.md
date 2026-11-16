# 設計文件 Design

> 狀態：v0.1.0 骨架的設計定案。改變任何「難以反悔」的決定時，先在本文更新章節與理由；若影響已發佈世界的重現性，必須開 GitHub Issue 討論。

## 1. 目標與非目標

**目標**

- 一顆種子＋一個預設 → 一個完整世界，**逐位元可重現**（跨平台、跨 Python 版本）。
- 今天就對 [Unbodysoma](https://github.com/Galen-Chu/Unbodysoma) 有用：輸出可直接執行的情境 TOML。
- 生態規則明確：為什麼食物長這裡、水在那裡、掠食者何時來，每條規則都有出處或理由。
- 管線可成長到 3D 與 WebGPU 預覽（血統：abyssal-garden，見 Unbodysoma 的 WORLDGEN.md）。

**非目標**

- 不是遊戲引擎、不是渲染器（渲染是 Phase 4 的預覽轉接器，不是核心）。
- 不做無限串流世界：世界有界（如同 abyssal-garden 的固定體積網格）。價值在「無限種世界」，不在「無限大世界」。
- 不做即時生成：載入時一次生成完畢，與消費者的模擬迴圈解耦。

## 2. 決定論契約 Determinism Contract

這是本專案最不可妥協的性質，由四層保證：

1. **自帶 PRNG**（`rng.py`）：mulberry32，逐運算移植自 abyssal-garden 的
   `rnd`。不使用 Python `random`——stdlib 只保證 `random()` 跨版本穩定，
   且無法與未來的 JS 端（WebGPU 預覽）共享序列。同一演算法在 JS 與 Python
   對同一種子產出相同數列，這是 Phase 4 前端能重用種子的前提。
   **已驗證（2026-11-16，Node 22）**：`scripts/verify_lineage.mjs`（函式逐字
   複製自 abyssal-garden 的 `math.js`）與 `scripts/verify_lineage.py` 的
   35 行輸出逐位元相同——預設種子 20261110 的前 20 個抽樣、`rseed(3)` 串流
   的 10 個抽樣、值雜訊 z=0 切片的 5 個值。前 30 個數值已固化為
   `test_js_lineage` 的 golden 常數，任何破壞跨語言血統的改動會在 CI 爆炸。
2. **Per-system 串流**：系統 `i` 的串流種子為 `base + i·7919`（鏡射
   abyssal-garden 的 `rseed`）。**系統 id 是穩定契約，終身不重編**；新系統
   取下一個未用的 id，舊世界的輸出不變：

   | id | 系統 | 用途 |
   |---|---|---|
   | 1 | terrain（保留） | 地形場是位置的純函數，目前不用串流 |
   | 2 | food | 食物斑塊採樣 |
   | 3 | water | 水源採樣 |
   | 4 | shelter | 庇護所偏移量 |
   | 5 | hazard | 常駐危險區位置與半徑 |
   | 6 | patrol | 巡邏順序與時刻抖動 |

3. **純函數生成**：`generate(seed, preset) -> World` 無副作用、無全域狀態；
   密度場（fertility／wetness）是位置的純函數，只依賴 preset 常數。
4. **定位格式化輸出**：浮點數一律 `_f()`（6 位小數、去尾零）；檔案一律
   LF（`.gitattributes` 強制）。golden test（`tests/golden/meadow_seed1.toml`）
   以逐位元比對把整條鏈釘死。
5. **Preset 版本化**（2026-11-16 定案，原開放問題 2）：每個 preset 帶
   `version`（改任何數字或生成語意時 bump），`World` 記錄
   `preset_version`，輸出檔頭以 `preset=<名稱>@<版本>` 標注。這是
   **provenance 契約而非時光機**：舊世界標明它由哪個修訂生成；bump 之後
   要重現舊世界，需 checkout 當時的 commit。第一個 release tag 之前不
   bump，v0.1.0 的所有 preset 都是 `@1`。

**重生指令**寫進每個輸出檔的註解頭兩行（含版本與 `sanctuary --seed … --preset …`），
呼應 Unbodysoma 執行紀錄 `meta.json` 保存情境原文＋SHA-256 的可追溯文化。

## 3. 密度場與植放演算法

全部移植自 abyssal-garden 的「生態撒點」模式（其 `world.js`）：以雜訊場當
密度函數，拒絕採樣決定位置，規則決定接受與否。

| 階段 | 場 / 規則 | 出處與理由 |
|---|---|---|
| fertility | `fbm2(x·scale + 3.7, y·scale + 9.1, 4 octaves)` | abyssal 的域偏移慣例：每個場用不同偏移即彼此獨立；octave 常數（2.03／0.5）同源 |
| wetness | `fbm2(x·0.045 + 47.3, …, 3 octaves)` | 較粗的尺度：水系比食物斑塊更連貫 |
| 食物 | 在 fertility ≥ 0.5 處拒絕採樣；最小間距 `min_food_gap`；失敗 20,000 次後先棄閾值、再每 20,000 次間距減半 | 鬆弛保證終止；間距理由：Unbodysoma 的邊際值定理——斑塊要夠遠，離開才值得 |
| 水 | 同法於 wetness 場，間距 6 | abyssal 的 `KELPZ` 熱點模式：群落由場決定，不是手工座標 |
| 庇護所 | 放在 fertility 最高的食物斑塊旁 3–5 格、朝世界中心偏移 | 仿生物學的巢域中心性；也讓「記得回家的路」的行為有實際結構 |
| 常駐危險區 | fertility < 0.45 的貧瘠地；離水、庇護所、既有危險區至少 `hazard_clearance` | 危險與資源在場上負相關——環境有可讀的結構，而非均勻雜訊 |
| 巡邏 | 每日造訪不同食物斑塊；時段取自 {11, 14, 17, 20} 時＋±0.5h 抖動；窗口 1 h、週期 86400 s | 直接映射 Unbodysoma `grid_72h.toml` 的排程語意（時刻自 08:00 起算的秒數） |

## 4. 轉接器契約 Adapter Contract

`toml_out.scenario_toml()` 發射的鍵集必須**精確等於** Unbodysoma
`config.py` 的允許清單（其 ADR-0008：未知鍵一律報錯）：

| 本專案 dataclass | TOML 區段 | Unbodysoma 鏡像 |
|---|---|---|
| `FoodPatch` | `[[world.food]]` x, y, [capacity], regrow_per_hour | `unbodysoma.world.grid.FoodPatch` |
| `WaterSource` | `[[world.water]]` x, y | `WaterSource` |
| `Shelter` | `[[world.shelters]]` x, y, radius, insulation | `Shelter` |
| `Hazard`（常駐） | `[[world.hazards]]` x, y, radius, strength | `Hazard`（start/end/every 省略＝預設無限） |
| `Hazard`（排程） | 同上＋start, end, every | `Hazard` |

注意：TOML 沒有無限大字面值，所以常駐危險區**必須**省略排程鍵——
`test_permanent_hazard_omits_schedule` 把關。`test_roundtrip_structure` 以
stdlib `tomllib` 讀回並比對鍵集；Unbodysoma 端的實測（生成檔直接
`python -m unbodysoma run`）是發佈前的手動驗收步驟。

`[scenario]` 的 `seed` 預設等於世界種子（一個數字重建一切）；實驗要解耦
「世界差異」與「行為雜訊」時用 `--organism-seed` 覆寫。

## 5. 測試策略

- **單元**：RNG 決定論／獨立性／邊界；雜訊值域與格點性質；smoothstep 端點。
- **不變量**：每個 preset × 種子 {0, 1, 7, 42, 20261116}：數量精確、全在
  邊界內、間距成立、起點＝庇護所、排程鍵有限且每日、庇護所不在常駐危險區內。
- **Golden**：`meadow × seed 1` 的完整 TOML 逐位元比對——任何吞噬決定論的
  改動（字典序、浮點格式、串流順序）都會在此爆炸。意圖改變輸出時，重生成
  golden 並在 commit 訊息說明理由。

## 6. 開放問題

1. **統計驗收**（Phase 2）：「同一 preset 跨 100 顆種子」該斷言哪些分布性質
   （最近水源距離的中位數、危險覆蓋率、巡邏時段覆蓋）？界線太緊會讓生成器
   為測試而生成，太鬆則失去意義。
2. **地形場**（Phase 3）：可通行性目前不存在（torus 網格全域可走）。引入
   高度場後，植放規則要加「可達性」——這是 abyssal `CLEARS`（淨空保證）的
   對應物，也是它最值得抄的工程模式之一。
3. **WebGPU 預覽**（Phase 4）：輸出格式傾向 JSON（座標＋場參數），前端以
   同源雜訊常數重算場來鋪渲染——種子真正跨語言共享的那一天。
