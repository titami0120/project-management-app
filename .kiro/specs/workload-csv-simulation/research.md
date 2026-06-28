# Research & Design Decisions

---

## Summary

- **Feature**: `workload-csv-simulation`
- **Discovery Scope**: New Feature（グリーンフィールド。既存コードベースなし）
- **Key Findings**:
  - `matter_id` を NULL 許容にすることで CSV 取り込みプロジェクトを案件未紐づけ状態で登録可能にする（Steering の NOT NULL 制約を緩和）
  - 見込工数マトリクスはバックエンドがフラットリストを返し、フロントエンドでピボット表示する設計が拡張性・保守性ともに優れる
  - CSV インポートはヘッダ検証 → 行検証 → DB upsert → バージョン作成の順序で 1 トランザクション内で完結させる

---

## Research Log

### matter_id の NULL 許容設計

- **Context**: 要件 4.5「CSVから新規登録されたプロジェクトは案件未紐づけの状態で登録する」が Steering data-model.md の `matter_id` 必須制約と矛盾する
- **Findings**:
  - CSVには案件情報が含まれない（Steering product.md の CSVカラム定義より）
  - プロジェクトを案件に紐づけるのは後工程（要件 7.3: 手動での案件紐づけ機能）
  - NULL 許容にすることで、未紐づけプロジェクトを「案件なし」として一覧・管理できる
- **Implications**: `projects.matter_id` を NULL 許容（NULLABLE FK）に変更する。案件サマリ集計は `matter_id IS NOT NULL` の条件付きで行う

### 見込工数マトリクスの集計アーキテクチャ

- **Context**: 要件 8.3「要員を行・月を列とするマトリクス形式」のデータ取得・整形をどこで行うか
- **Findings**:
  - Option A（バックエンドピボット）: SQLのピボット/GROUP BY で整形。フロントは受け取るだけ。月範囲が変わるとSQL変更が必要
  - Option B（フロントエンドピボット）: バックエンドはフラットリストを返す。フロントの `useWorkloadMatrix` フックで変換。柔軟性が高い
- **Selected**: Option B（フロントエンドピボット）
- **Rationale**: 月範囲が動的（ユーザーが指定）なため、SQL でのピボットは列数不定となり複雑。フロントでの変換の方が型安全かつ動的フィルタに対応しやすい

### CSV インポートのトランザクション戦略

- **Context**: CSV の行数が多い場合、一部失敗時の挙動を決める必要がある
- **Findings**:
  - 要件 1.6・3.7「エラーがあればいかなるデータも保存しない（全件ロールバック）」
  - upsert の順序依存：departments → members → projects → monthly_workloads（FK依存順）
  - バージョン作成・スナップショット記録も同一トランザクションに含める
- **Selected**: 検証フェーズ（バリデーション全件）を先に完結させ、エラーなしの場合のみ DB 操作フェーズに進む 2フェーズ設計
- **Rationale**: DB トランザクション外でのバリデーションにより、DB ロック時間を最小化しながら全件ロールバック保証を実現

### シミュレーション状態管理

- **Context**: 要件 9.4「リアルタイム再計算」をどこで保持するか
- **Findings**:
  - セルを変更するたびに API 呼び出しすると UX が遅い
  - 保存（要件 9.6）まではフロントエンドのローカル状態で管理し、保存時に一括 PUT が適切
- **Selected**: `useSimulation` カスタムフックにローカル変更差分（diff map）を保持し、保存時に `PUT /api/v1/workloads/simulate` で一括送信

---

## Architecture Pattern Evaluation

| Option | 説明 | Strengths | Risks / Limitations |
|--------|------|-----------|---------------------|
| 単一モノリス（FastAPI + React SPA） | バックエンド1プロセス、フロントSPA | シンプル、開発速度が高い | スケールに限界 |
| マイクロサービス | CSV処理サービスを分離 | スケーラブル | MVP には過剰 |

→ **単一モノリス** を選択（MVP スコープに適合）

---

## Design Decisions

### Decision: `matter_id` を NULLABLE FK に変更

- **Context**: CSV 取り込み時に案件情報がないため、projects.matter_id を必須にできない
- **Selected Approach**: `matter_id` を NULL 許容 FK に変更。NULL = 案件未紐づけ
- **Trade-offs**: 案件ありきの集計でNULLフィルタが必要になるが、柔軟性が高い

### Decision: 見込工数の導出をアプリ層で実施

- **Context**: `COALESCE(simulated_mm, planned_mm)` を SQL に書くかアプリ層に書くか
- **Selected Approach**: バックエンドの WorkloadService で Python コードとして計算し、API レスポンスに `forecast_mm` を含める
- **Rationale**: 将来的に `actual_mm` を含む3値合成ロジックに拡張する際、Python コードの方が変更が明示的

### Decision: CSV インポートの 2 フェーズ処理

- **Context**: バリデーションエラーがあれば全件ロールバック（要件 3.7）
- **Selected Approach**: Phase 1（バリデーション全行）→ Phase 2（DB 操作） の 2 フェーズ。DB 操作は 1 トランザクション
- **Trade-offs**: 大量行の場合はメモリに全行を保持する必要があるが、MVP 規模では問題なし

---

## Risks & Mitigations

- 大規模 CSV（数万行）でのメモリ・タイムアウト — MVPでは許容。将来はストリーミング処理を検討
- マトリクスのフロントエンド計算コスト — 表示期間を最大12か月・要員数を最大100人程度にフィルタで制限することで対応
- `matter_id` NULL 許容への変更が Steering の記述と齟齬を生じる — 設計フェーズで明示的に決定し design.md に記載

---

## References

- FastAPI ファイルアップロード: `UploadFile` + `python-multipart`
- SQLAlchemy 2.x bulk upsert: `Session.execute(insert().on_conflict_do_update(...))`
- Ant Design Upload コンポーネント: `<Upload>` / `<Dragger>`
- Ant Design Table: `expandable` rows for member → project drill-down
