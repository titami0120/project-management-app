# データモデル設計方針

## エンティティ一覧

| エンティティ | テーブル名 | 説明 |
|-------------|-----------|------|
| 部門 | `departments` | 組織の管理単位 |
| チーム | `teams` | 主管部門を持つ作業グループ |
| チームメンバー | `team_members` | チームと要員の中間テーブル（多対多） |
| 要員 | `members` | 業務にアサインされる個人 |
| 案件 | `matters` | 業務受注の最上位単位 |
| プロジェクト | `projects` | 案件を構成するフェーズ・作業区分（工数管理の基本単位） |
| 月次工数 | `monthly_workloads` | 要員×プロジェクト×年月の工数記録（計画・実績・シミュレーション） |
| 見込工数バージョン | `forecast_versions` | CSVアップロード時に作成される見込工数のバージョン管理 |
| 見込工数スナップショット | `forecast_snapshots` | バージョン時点での見込工数のスナップショット |

---

## エンティティ間のリレーション（論理レベル）

> **凡例**
> - `★` : DB上のFK制約あり（物理実装済）
> - `☆` : 論理的な関係（アプリ層のクエリや結合で取得。FK非保持）
> - カーディナリティ表記：`1`, `N`, `M`, `0..1`

---

### 1. 組織階層

```
部門 1 ────★──── N  要員        要員は必ず1つの部門（主管部門）に所属する
部門 1 ────★──── N  チーム      チームは主管部門を1つ持つ
チーム N ───★──── M  要員        team_members（中間テーブル）で実装
                                  要員は0件以上のチームに所属できる
```

### 2. 案件・プロジェクト

```
案件 1 ────★──── N    プロジェクト   プロジェクトは必ず1つの案件に紐づく
案件 N ────★──── 0..1 要員           PM（matters.pm_member_id）。1案件に0〜1名
```

### 3. 工数（月次工数を中心とした関係）

月次工数（monthly_workloads）は「要員 × プロジェクト × 年月」の**関連エンティティ**であり、
計画・シミュレーション・実績の3種の工数値を属性として持つ。

```
要員 N ────★──── M プロジェクト    monthly_workloads で実装
                  属性: year, month, planned_mm, simulated_mm, actual_mm
```

月次工数を介した**派生関係**（FK非保持。集計・結合クエリで取得）：

```
部門  ────☆──── プロジェクト    要員 → monthly_workloads → プロジェクト
部門  ────☆──── 案件            上記 → projects.matter_id
チーム ───☆──── プロジェクト    チームメンバー → 要員 → monthly_workloads → プロジェクト
チーム ───☆──── 案件            上記 → projects.matter_id
```

> これらの派生関係が「部門単位」「チーム単位」での工数集計ビューの基盤となる。

### 4. 見込工数バージョン管理

見込工数バージョン（forecast_versions）は、CSVアップロード時に月次工数から導出した
見込工数の**時点スナップショット**を保持する。

```
月次工数 ──────☆──── 見込工数バージョン    CSVアップロード時に見込工数を導出して作成
                      ↑ 直接のFK非保持。バージョン作成処理が参照する論理的な依存

見込工数バージョン 1 ──★──── N  見込工数スナップショット
見込工数スナップショット N ──★──── 1 要員
見込工数スナップショット N ──★──── 1 プロジェクト
見込工数スナップショット N ──☆──── 1 案件    projects.matter_id 経由の論理関係（FK非保持）
```

### 5. CSVとエンティティのマッピング（論理対応）

CSVの各列はDBの特定カラムにコードで突合する（DB上のFK制約なし）。  
詳細なバリデーション・処理仕様は `.kiro/steering/csv-spec.md` を参照。

```
【部門】
計画工数CSV [所属部門コード] ──☆── departments.code         upsertキー
計画工数CSV [所属部門名]     ──☆── departments.name

【要員】
計画工数CSV [社員コード]     ──☆── members.employee_code    upsertキー
計画工数CSV [氏名]           ──☆── members.name
計画工数CSV [所属部門コード] ──☆── members.department_id    (code→id で解決)

【プロジェクト】
計画工数CSV [WBS仮コード]    ──☆── projects.wbs_tmp         upsertキー
計画工数CSV [WBSコード]      ──☆── projects.code            任意（列なし or 空値 → NULL）
計画工数CSV [WBS名称]        ──☆── projects.name

【月次工数】
計画工数CSV [社員コード]     ──☆── monthly_workloads.member_id   (employee_code→id で解決)
計画工数CSV [WBS仮コード]    ──☆── monthly_workloads.project_id  (wbs_tmp→id で解決)
計画工数CSV [会計年度]       ──☆── monthly_workloads.year        変換: 4〜12月はFY, 1〜3月はFY+1
計画工数CSV [4月〜3月]       ──☆── monthly_workloads.planned_mm  0.00の新規INSERTはスキップ

【無視する列】
計画工数CSV [プロダクトコード] ── 保存しない（バリデーションも行わない）
計画工数CSV [プロダクト名]     ── 保存しない（バリデーションも行わない）
計画工数CSV [所属会社コード]   ── 保存しない（バリデーションも行わない）
計画工数CSV [所属会社名]       ── 保存しない（バリデーションも行わない）
```

### 6. ユニーク制約（物理）

| テーブル | 複合ユニーク制約 |
|---------|----------------|
| `monthly_workloads` | `(member_id, project_id, year, month)` |
| `forecast_snapshots` | `(version_id, member_id, project_id, year, month)` |

---

## 主要エンティティの属性

### 部門（departments）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `name` | VARCHAR(100) | 部門名（例：開発部） |
| `code` | VARCHAR(50) UNIQUE | 部門コード |
| `is_deleted` | BOOLEAN | 論理削除フラグ |
| `created_at` | DATETIME | |

### チーム（teams）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `name` | VARCHAR(100) | チーム名 |
| `department_id` | INTEGER FK | 主管部門 |
| `is_deleted` | BOOLEAN | 論理削除フラグ |
| `created_at` | DATETIME | |

### チームメンバー（team_members）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `team_id` | INTEGER FK | |
| `member_id` | INTEGER FK | |
複合PK：`(team_id, member_id)`

### 要員（members）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `name` | VARCHAR(100) | 氏名 |
| `employee_code` | VARCHAR(50) UNIQUE | 社員コード |
| `department_id` | INTEGER FK | 所属部門（主管部門） |
| `is_deleted` | BOOLEAN | 論理削除フラグ |
| `created_at` | DATETIME | |

### 案件（matters）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `name` | VARCHAR(200) | 案件名（例：XX社向け受注管理システム開発） |
| `code` | VARCHAR(50) UNIQUE | 案件コード |
| `client_name` | VARCHAR(200) | 顧客名（NULL可） |
| `start_date` | DATE | 開始日（NULL可） |
| `end_date` | DATE | 終了日（NULL可） |
| `status` | VARCHAR(20) | 計画中 / 進行中 / 完了 / 中断 |
| `pm_member_id` | INTEGER FK | PM（要員ID、NULL可） |
| `is_deleted` | BOOLEAN | 論理削除フラグ |
| `created_at` | DATETIME | |

### プロジェクト（projects）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `matter_id` | INTEGER FK | 所属案件（必須） |
| `wbs_tmp` | VARCHAR(50) NOT NULL | WBS仮コード（必須。計画工数CSVの[WBS仮コード]と対応） |
| `name` | VARCHAR(200) | プロジェクト名（例：要件定義フェーズ） |
| `code` | VARCHAR(50) | WBSコード（任意。NULL可） |
| `order` | INTEGER | 案件内での表示順 |
| `is_deleted` | BOOLEAN | 論理削除フラグ |
| `created_at` | DATETIME | |

> **備考**：プロジェクト化されていない取組も「仮想プロジェクト」として登録できるよう `wbs_tmp` を識別子とする。`code` は正式なWBSコードが確定した場合のみ設定する。

### 月次工数（monthly_workloads）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `member_id` | INTEGER FK | 要員 |
| `project_id` | INTEGER FK | プロジェクト |
| `year` | INTEGER | 年（例：2025） |
| `month` | INTEGER | 月（1〜12） |
| `planned_mm` | NUMERIC(5,2) | 計画工数（人月、NULL可。計画工数CSVから取り込み） |
| `simulated_mm` | NUMERIC(5,2) | シミュレーション工数（人月、NULL可。ユーザーが画面上で変更した値） |
| `actual_mm` | NUMERIC(5,2) | 実績工数（人月、NULL可。取り込み元・仕様は別途検討） |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

> **見込工数の導出ルール**：`actual_mm` が存在する月は `actual_mm` を見込とし、存在しない月は `simulated_mm`（NULLの場合は `planned_mm`）を見込として表示する。

### 見込工数バージョン（forecast_versions）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `version_no` | INTEGER | バージョン番号（自動採番） |
| `trigger_type` | VARCHAR(20) | 作成契機：`plan_upload`（計画CSV）/ `actual_upload`（実績CSV） |
| `note` | VARCHAR(500) | 説明・備考（NULL可） |
| `created_at` | DATETIME | |

### 見込工数スナップショット（forecast_snapshots）
| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER PK | |
| `version_id` | INTEGER FK | 見込工数バージョン |
| `member_id` | INTEGER FK | 要員 |
| `project_id` | INTEGER FK | プロジェクト |
| `year` | INTEGER | 年 |
| `month` | INTEGER | 月（1〜12） |
| `forecast_mm` | NUMERIC(5,2) | バージョン時点での見込工数（人月） |
| `created_at` | DATETIME | |

---

## 設計方針

1. **工数の保存形式**：NUMERIC(5,2)（小数点第2位まで格納可能、例：0.50人月）。1.0人月超えは許容し、アプリ側で警告を表示する
2. **削除方針**：物理削除ではなく論理削除（`is_deleted = TRUE`）を基本とする。参照整合性を保つために参照先エンティティの削除は論理削除で行う
3. **年月の扱い**：`year`（INT）と`month`（INT 1〜12）を分割して保存する。日付型ではなく年月管理のため
4. **工数カラムの役割分担**：`planned_mm`はCSV取り込み値（変更禁止）、`simulated_mm`はユーザーのシミュレーション値、`actual_mm`は取り込みの実績値（取り込み仕様別途検討。変更禁止）
5. **見込工数の導出**：`actual_mm` IS NOT NULL → `actual_mm`、それ以外 → `COALESCE(simulated_mm, planned_mm)` をアプリ層で計算する
6. **バージョン作成タイミング**：計画工数CSVのアップロード完了時、または実績工数の取り込み完了時（取り込み仕様は別途検討）に `forecast_versions` レコードを作成し、その時点の見込工数を `forecast_snapshots` に記録する
7. **稼働合計チェックのロジック**：同一の `(member_id, year, month)` のレコードを集計し、見込工数の合計が1.0人月超えを検出する
8. **案件単位の工数集計**：案件の工数は配下プロジェクトの月次工数を集計したサマリとして取得する（`matters`テーブル自体には工数カラムを持たない）
9. **プロジェクトの識別子**：`wbs_tmp`を主要な識別子とし、計画工数CSVとのマッチングに使用する。`code`は正式コードが確定後に設定する任意項目
