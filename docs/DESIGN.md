# 設計文件 Design

> 狀態：v0.1.0 骨架的設計定案。改變任何「難以反悔」的決定時，先在本文更新章節與理由；若影響已發佈世界的重現性，必須開 GitHub Issue 討論。
> 本文件管「怎麼設計」；「要做什麼」（工作項、工程債、生態整合）見 [BACKLOG.md](BACKLOG.md)。

## 1. 目標與非目標

**目標**

- 一顆種子＋一個預設 → 一個完整世界，**逐位元可重現**（跨平台、跨 Python 版本）。
- 今天就對 [Unbodysoma](https://github.com/Galen-Chu/Unbodysoma) 有用：輸出可直接執行的情境 TOML（它是第一個消費者，不是開發節奏的約束）。
- 生態規則明確：為什麼食物長這裡、水在那裡、掠食者何時來，每條規則都有出處或理由。
- **系統可組合**（2026-11-18 定案）：世界由可插拔的生成系統組合而成——**原型（archetype）＝系統組合＋參數**。擴張＝新系統入註冊表；收縮＝原型少選系統（kelp-basin 去掉常駐危險區即雛形）。per-system 串流 id（§2）是系統介面的既有錨點。
- **世界圖書館**（2026-11-18 定案）：原型庫（版本化定義、可查詢的 JSON 索引）＋標本索引——世界是（種子, 原型）的純函數，**標本只需索引卡**（seed, archetype@version, 統計指紋），世界本體按需重生成，儲存成本趨近於零。
- 管線可成長到 3D 與 WebGPU 預覽（血統：abyssal-garden，見 Unbodysoma 的 WORLDGEN.md）。

**非目標**

- 不是遊戲引擎、不是渲染器（渲染是 Phase 4 的預覽轉接器，不是核心）。
- 不做無限串流世界：世界有界（如同 abyssal-garden 的固定體積網格）。價值在「無限種世界」，不在「無限大世界」。
- 不做即時生成：載入時一次生成完畢，與消費者的模擬迴圈解耦。
- **不做程式級整合**（2026-11-18 定案）：與消費者的耦合只存在於轉接器契約（鍵集／格式）；消費者的開發節奏不約束世界詞彙——新系統先落核心與 JSON 轉接器，Unbodysoma TOML 等其跟上（轉接器能力宣告，§4）。M1「N 個體 × M 世界」是拉動即用的消費者整合，不是開發里程碑。

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
   bump（0.x 期間所有 preset 維持 `@1`）。
6. **族群種子派生**（2026-11-18，population mode）：`--count N` 世界群中第 `i` 個
   世界的種子恆為 `master + i`。與系統 id 同級的穩定契約——世界群裡每個世界都能
   單獨以 `sanctuary --seed master+i --preset …` 重現，族群不需要自己的亂數流。

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

### 可組合系統（2026-11-18 v1 落地，原「架構方向」）

`generate()` 的固定管線已拆為 `systems.py` 的五個註冊系統。介面（開放問題 4 的
v1 答案）：

- **`Generation`**：可變累積上下文（seed、preset、串流工廠、場、四種實體清單）。
- **`System`**：`{name, stream_id, apply, needs}`——`apply` 只動自己的串流、讀先行
  系統的產物、附加實體；`needs` 宣告資料相依（shelter→food、hazard-patrol→food）。
- **正準序**：`food, water, shelter, hazard-permanent, hazard-patrol`（相依的拓撲
  序）；執行恆為正準序限制到原型的選擇，選擇的書寫順序無意義。跨系統順序本就不
  影響位元組（串流獨立），正準序只為相依服務。
- **驗證**：未知系統、空組合、相依缺失在 `generate()` 入口大聲報錯。

兩條硬約束的兌現：**重組不改位元組**（150 世界逐位元驗證＋golden 把關）；**收縮
先於擴張**（kelp-basin 已以組合方式去掉 hazard-permanent，不再是
`permanent_hazards=0` 參數繞道；無庇護所原型起點＝世界中心）。之後每個新內容系統
（地形、季節）以註冊系統形式加入——擴張與收縮自此是常規操作。

**第一個擴張實例（2026-11-18）：掠食者策略庫**——以「巡邏系統的行為參數」形式
落地（`strategies.py` 的策略註冊表，原型以 `patrol_strategy` 選用）：fixed（Phase 1
行為，抽取序逐位元保留）、sweep（全天均勻、不可預測）、circadian（恆 6 h 週期、
可學習）、regional（全部造訪集中單一錨點斑塊、迫使遷移）。四者以統計特徵可區分
（§5），策略置換不動任何其他系統的實體（per-system 串流的直接兌現，有測試釘死）。
新增策略＝往註冊表加一項，核心管線零改動。

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

### 世界群 manifest（population mode，2026-11-18）

`--count N ≥ 2` 時 CLI 寫入一個目錄：N 份情境 TOML＋一份 `population.toml`。
manifest 是 Sanctuary 自有契約（非 Unbodysoma 鍵集，毋須雙邊同步）：`[population]`
記錄 generator／version／preset@version／master seed／count／duration_h（覆寫時加
organism_seed）；`[[worlds]]` 逐世界記錄 name、file、seed、該檔 SHA-256——世界群可
作為單一單位驗證，也是 M1 實驗紀錄引用世界側 provenance 的載體（BACKLOG §2）。
沒有時間戳：manifest 是輸入的純函數，重跑逐位元相同（golden：
`population_meadow_seed1_count3.toml`）。`--count 1` 維持單檔／stdout 行為，
不產生 manifest（向後相容）。

### 轉接器能力宣告（2026-11-18 定案，機制已落地）

每個轉接器宣告自己能表達的系統／特性集合（能力矩陣）。核心詞彙超出轉接器能力
時，行為必須是**明確降級（文件化）或大聲報錯**，絕不默默省略。機制已落地：
`toml_out.TOML_SYSTEMS`（五系統全支援）＋ `scenario_toml` 入口的
`_check_capability`（超出即 `ValueError`）。第一個實際觸發點是 Phase 3 季節動態
——先落核心＋JSON，TOML 在 Unbodysoma 鍵集跟上（ADR-0010）前會報錯而非省略。
JSON 側：原型庫索引與標本卡（`library.py`）已經是 JSON 產物；完整世界 JSON 隨
Phase 4 WebGPU 預覽到來。這讓 Unbodysoma 的鍵集擴充節奏不再擋住核心的新系統。

## 5. 測試策略

- **單元**：RNG 決定論／獨立性／邊界；雜訊值域與格點性質；smoothstep 端點。
- **不變量**：每個 preset × 種子 {0, 1, 7, 42, 20261116}：數量精確、全在
  邊界內、間距成立、起點＝庇護所、排程鍵有限且每日、庇護所不在常駐危險區內。
- **Golden**：`meadow × seed 1` 的完整 TOML 逐位元比對——任何吞噬決定論的
  改動（字典序、浮點格式、串流順序）都會在此爆炸。意圖改變輸出時，重生成
  golden 並在 commit 訊息說明理由。
- **世界群**：派生恆等式（population 第 i 個世界 == `generate(seed + i)`）、
  manifest 鍵集與逐檔 SHA 對應、CLI 目錄模式、manifest golden。

### 統計驗收（2026-11-18 v1，開放問題 1 的答案）

單一世界過不變量；一「類」世界過統計。指紋（`stats.fingerprint`）跨種子彙總
四項指標，界線＝**可執行理論的中心 × 明確因子**（常數在 `stats.py`），不是調到
測試變綠。實測（100 種子，2026-11-18）：

| 指標 | 理論中心 | 帶 | 實測 |
|---|---|---|---|
| 食物→最近水中位數 | `sqrt(ln2·A_eff/(πn))`（泊松參考，A_eff=(W−4)(H−4)） | ×[0.5, 2.0] | 比值 1.11–1.22 |
| 庇護所→最近水中位數 | 同上 | ×[0.5, 2.0] | 比值 0.78–0.93 |
| 庇護所→最近食物中位數 | 偏移量 3–5；「最近」可能取自側翼斑塊 | [2.0, 5.5] | 2.57–3.61 |
| 危險覆蓋率（聯集圓盤／名目面積，0.5 格網格估計） | `1−∏(1−E[圓盤]/A)`（獨立圓盤） | ×[0.5, 1.75] | 比值 1.00–1.01 |

觀察記錄：獨立圓盤模型幾乎精確（比值≈1.00）；水源距離的膨脹方向符合有限點數
（均勻方格精確值比泊松高約 9%）＋邊界＋場叢聚；庇護所向中心偏移使其→水距離
低於均勻理論；meadow 的庇護所→最近食物（2.57）低於偏移下限——「最近」常取自
側翼斑塊，故帶下限放至 2.0。巡邏時段為**結構性**斷言、按策略分派（fixed/regional：
時段 {11,14,17,20} 循環＋±0.5h；circadian：恆 6 h 週期；sweep：全天域 [8, 32)
均勻）——四策略以時段散布（fixed≈3.9 h vs sweep≈22.2 h）、週期（fixed 缺口≈3 h
vs circadian 恆 6 h）、目標選擇（regional 全同錨點）三者可區分。CI 以 50 顆種子
檢定（中位數對 gross-degeneracy 帶寬檢定力足夠）；`--fingerprint` CLI 預設 100。
遺留：理論精化後收緊帶寬；可達性加入圖論量測；指紋入標本索引（架構核心）。

附註（效能）：`_sample`／`_place_permanent` 的拒絕條件改為便宜者先行（間距／
淨空先於 fbm 場）——接受集合是條件的 AND，順序不影響輸出（150 世界逐位元驗證），
生成提速 ~1.4×，讓 100 種子指紋在 CI 可負擔。

## 6. 開放問題

1. ~~**統計驗收**~~ → **v1 已定案**（2026-11-18，見 §5 統計驗收）：四項指標、
   可執行理論中心×文件化因子；遺留為帶寬收緊與新指標（圖論可達性）。
2. **地形場**（Phase 3）：可通行性目前不存在（torus 網格全域可走）。引入
   高度場後，植放規則要加「可達性」——這是 abyssal `CLEARS`（淨空保證）的
   對應物，也是它最值得抄的工程模式之一。
3. **WebGPU 預覽**（Phase 4）：輸出格式傾向 JSON（座標＋場參數），前端以
   同源雜訊常數重算場來鋪渲染——種子真正跨語言共享的那一天。
4. ~~**系統介面與原型 schema**~~ → **v1 已定案**（2026-11-18，見 §3 可組合
   系統）：`Generation`／`System{name, stream_id, apply, needs}`／正準序＋組合
   驗證；原型＝`Preset.systems` 組合宣告。隨新系統落地按需精化。
