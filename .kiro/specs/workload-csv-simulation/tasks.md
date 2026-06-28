# Implementation Plan

---

- [ ] 1. Foundation — バックエンド基盤の構築

- [x] 1.1 FastAPIプロジェクト初期化と依存パッケージ設定
  - `backend/` ディレクトリに FastAPI・SQLAlchemy 2.x・Pydantic v2・Alembic・python-multipart・Ruff をインストールし、依存を固定する
  - `backend/app/main.py` でアプリを起動し、ルーター登録の雛形と CORS 設定（開発用）を追加する
  - `backend/app/database.py` で SQLite 接続の SQLAlchemy エンジン・セッションファクトリを設定し、FastAPI の DI（`Depends`）で注入できる `get_db()` 関数を用意する
  - `GET /health` に対して HTTP 200 が返ることで完了を確認できる
  - _Requirements: （基盤タスク）_

- [x] 1.2 SQLAlchemyモデル定義（9エンティティ）
  - `backend/app/models/` 配下に departments・teams・team_members・members・matters・projects・monthly_workloads・forecast_versions・forecast_snapshots を各ファイルに定義する
  - `projects.matter_id` は NULLABLE FK（`ON DELETE SET NULL`）として定義し、NULL = 案件未紐づけを表す
  - `monthly_workloads.planned_mm / simulated_mm / actual_mm` はいずれも `NUMERIC(5,2) NULLABLE` で定義し、`(member_id, project_id, year, month)` の複合ユニーク制約を設ける
  - `forecast_snapshots` に `(version_id, member_id, project_id, year, month)` の複合ユニーク制約を設ける
  - 全モデルを Python でエラーなく import できることで完了を確認できる
  - _Requirements: 5.4, 6.1_

- [x] 1.3 Alembicマイグレーション設定と初期スキーマ適用
  - Alembic を初期化し `alembic.ini` と `env.py` を SQLAlchemy のモデルを参照するよう設定する
  - 全9テーブルを対象とした初期マイグレーションファイルを自動生成する
  - `alembic upgrade head` を実行して SQLite DB に全テーブルが作成されることを確認する
  - 生成された DB ファイルをツールで開いて9テーブルが揃っていることで完了を確認できる
  - _Requirements: （基盤タスク）_

---

- [ ] 2. (P) Foundation — フロントエンド基盤の構築

- [x] 2.1 React + Vite + TypeScriptプロジェクト初期化とAnt Design設定
  - `frontend/` ディレクトリに Vite + React + TypeScript テンプレートでプロジェクトを作成し、Ant Design 5.x・Axios・React Router をインストールする
  - ESLint + Prettier を設定し `npm run lint` がエラーなく通る状態にする
  - React Router でページパス（`/workload`・`/upload/plan`・`/matters`・`/projects`・`/forecast-versions`）を定義する
  - `npm run dev` でブラウザにデフォルトページが表示されることで完了を確認できる
  - _Boundary: frontend/src/_

- [x] 2.2 サイドバーナビゲーション付きアプリレイアウトの実装
  - Ant Design `<Layout>` + `<Sider>` + `<Menu>` でサイドバーナビゲーションを実装する
  - メニュー項目：「見込工数確認・シミュレーション」「案件・プロジェクト」「見込工数バージョン」「アップロード（計画工数CSV）」
  - 各メニュー項目クリックで対応するページコンポーネントにルーティングされ、選択状態がハイライトされる
  - ブラウザでサイドバーとコンテンツエリアの2カラムレイアウトが表示されることで完了を確認できる
  - _Boundary: frontend/src/components/layout/AppLayout.tsx_

- [x] 2.3 TypeScript型定義とAPIクライアントの実装
  - `frontend/src/types/` に workloadTypes・matterTypes・projectTypes・commonTypes を定義する（`any` 型使用禁止）
  - `frontend/src/api/` に workloadApi・matterApi・projectApi・departmentApi・forecastVersionApi の各呼び出し関数を Axios で実装する
  - Axios のベース URL を環境変数 `VITE_API_BASE_URL` から取得し、HTTP エラーを共通ハンドラで処理する
  - `tsc --noEmit` がエラーなく通ることで型定義の完了を確認できる
  - _Requirements: 2.1_
  - _Boundary: frontend/src/types/, frontend/src/api/_

---

- [ ] 3. Core — CSVインポート機能（バックエンド）

- [x] 3.1 CSVバリデーション実装（ヘッダー検証・全行バリデーション・エラー収集）
  - Shift-JIS エンコードでCSVファイルを読み込み、`csv.DictReader` でパースする処理を `CsvImportService` に実装する
  - 必須19列（所属部門コード・所属部門名・社員コード・氏名・WBS仮コード・WBS名称・会計年度・4月〜3月）のヘッダー存在確認を行い、欠如時は `row_no: null` のエラーを返す
  - 全行を走査して会計年度（整数・1900〜2100）・月次工数12列（数値・0以上）・必須文字列（空白不可）をバリデーションし、全エラーを `list[CsvValidationError]` に収集する
  - エラーが1件でも存在する場合は `CsvValidationException` を raise して DB 操作フェーズに進まない
  - 複数エラーを含む CSV をパースしたとき全エラーが一括収集され `row_no・column・message` を持つことで完了を確認できる
  - _Requirements: 1.6, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  - _Boundary: CsvImportService_

- [x] 3.2 マスタデータupsert実装（部門・要員・プロジェクトのFK依存順序）
  - `departments`：`code` をキーとして upsert、`is_deleted` は変更しない
  - `members`：`employee_code` をキーとして upsert、`department_id` を所属部門コードから解決する
  - `projects`：`wbs_tmp` をキーとして upsert、`matter_id = NULL` で新規登録し、WBSコードが空の場合は `code` を更新しない
  - SQLAlchemy `insert().on_conflict_do_update()` で upsert を実装し、FK依存順（departments → members → projects）で実行する
  - 新規/更新それぞれの件数を `ImportCount` 形式で返すことで完了を確認できる
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  - _Boundary: CsvImportService_

- [x] 3.3 月次工数upsert実装（会計年度変換・0.00スキップ/更新ルール）
  - 会計年度 FY の 4〜12月は `year=FY`、1〜3月は `year=FY+1` に変換して `(member_id, project_id, year, month)` をキーとして処理する
  - DBレコードなし かつ 工数値 > 0.00 → `planned_mm` で INSERT する
  - DBレコードなし かつ 工数値 = 0.00 → スキップ（INSERT しない）
  - DBレコードあり → 工数値が 0.00 でも `planned_mm` を UPDATE する（`simulated_mm`・`actual_mm` は変更しない）
  - 0.00 の月が既存レコードを 0.00 に更新し、かつ新規レコードとして作成されないことで完了を確認できる
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - _Boundary: CsvImportService_

- [x] 3.4 見込工数バージョンとスナップショットの自動作成実装
  - マスタupsert・工数upsert 完了後、同一トランザクション内で `forecast_versions` に `trigger_type='plan_upload'` で INSERT し、`MAX(version_no) + 1` でバージョン番号を採番する
  - 全 `monthly_workloads` から `COALESCE(simulated_mm, planned_mm)` を計算し、NOT NULL のレコードを `forecast_snapshots` に一括 INSERT する
  - `forecast_versions` と `forecast_snapshots` が同じ `version_id` で紐づいて作成されることで完了を確認できる
  - _Requirements: 6.1, 6.2_
  - _Boundary: ForecastService_

- [x] 3.5 CSVアップロードAPIエンドポイントの実装
  - `POST /api/v1/workloads/plan/upload` を multipart/form-data で実装し、`UploadFile` でファイルを受け取って `CsvImportService.import_plan_csv()` に委譲する
  - バリデーション成功時：HTTP 200 と `CsvUploadResponse {version_no, summary}` を返す
  - バリデーション失敗時：HTTP 422 と `CsvUploadErrorResponse {errors[]}` を返す
  - 全 DB 操作を1トランザクションで囲い、例外発生時は全件ロールバックして HTTP 500 を返す
  - curl で正常 CSV を POST したとき HTTP 200 と件数サマリが返り、不正 CSV では HTTP 422 とエラー一覧が返ることで完了を確認できる
  - _Requirements: 1.6, 2.1, 2.2, 2.3, 2.4_
  - _Boundary: workload_router_

---

- [ ] 4. (P) Core — 見込工数・シミュレーションAPI（バックエンド）

- [x] 4.1 見込工数取得APIの実装
  - `GET /api/v1/workloads/forecast` にクエリパラメータ `dept_id`・`team_id`・`from`（YYYY-MM）・`to`（YYYY-MM）を実装する
  - `WorkloadService.get_forecast()` で `monthly_workloads` を要員・プロジェクトと JOIN し、`COALESCE(simulated_mm, planned_mm)` を Python 層で計算して `forecast_mm` として付与する
  - レスポンスは `ForecastWorkloadResponse {months[], rows[{member_id, member_name, monthly_sums, projects[{cells}]}]}` のフラットリスト形式で返す
  - 部門フィルタを指定したリクエストで対象部門の要員のみを含む JSON が返ることで完了を確認できる
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.7_
  - _Boundary: WorkloadService, workload_router_

- [x] 4.2 シミュレーション保存・リセットAPIの実装
  - `PUT /api/v1/workloads/simulate` でリクエストボディ `SimulationUpdateRequest {updates[]}` を受け取り、指定された `(member_id, project_id, year, month)` の `simulated_mm` を一括 UPDATE する
  - `DELETE /api/v1/workloads/simulate` でクエリパラメータ `member_id`・`project_id`（任意指定）に一致する `simulated_mm` を NULL にリセットする
  - `planned_mm`・`actual_mm` はいかなる場合も変更しない
  - PUT 後に GET で取得した `forecast_mm` がシミュレーション値を反映し、DELETE 後に `planned_mm` ベースの値に戻ることで完了を確認できる
  - _Requirements: 9.6, 9.7_
  - _Boundary: WorkloadService, workload_router_

- [x] 4.3 見込工数CSVダウンロードAPIの実装
  - `GET /api/v1/workloads/forecast/download` にクエリパラメータ `from`・`to`（YYYY-MM）を実装する
  - Python `csv` 標準ライブラリで CSV を生成し、列は 要員コード・要員名・WBS仮コード・プロジェクト名・年・月・見込工数（人月）とする
  - `Content-Disposition: attachment; filename="simulation_{from}_{to}.csv"` ヘッダーを付けて返す
  - ブラウザでエンドポイントにアクセスしたとき指定形式のファイル名で CSV がダウンロードされることで完了を確認できる
  - _Requirements: 9.8, 9.9_
  - _Boundary: WorkloadService, workload_router_

---

- [ ] 5. (P) Core — 案件・プロジェクト管理API（バックエンド）

- [x] 5.1 案件CRUD APIと重複コードチェックの実装
  - `GET /api/v1/matters` で案件一覧（配下プロジェクト数を含む）を返す
  - `POST /api/v1/matters` で案件を新規登録し、案件コード重複時は HTTP 409 を返す
  - 案件名・案件コードを必須フィールドとして Pydantic スキーマでバリデーションする
  - 重複コードで POST したとき HTTP 409 が返り、正常 POST で HTTP 201 と登録内容が返ることで完了を確認できる
  - _Requirements: 7.1, 7.2, 7.5_
  - _Boundary: matter_router_

- [x] 5.2 プロジェクト編集・案件紐づけAPIの実装
  - `GET /api/v1/projects` でプロジェクト一覧を返す（クエリパラメータ `unassigned=true` で `matter_id IS NULL` のみフィルタ）
  - `PUT /api/v1/projects/{id}` でプロジェクトの WBS名称・WBSコード・表示順を更新する
  - `PUT /api/v1/projects/{id}/matter` で `{"matter_id": int}` を受け取り、プロジェクトの案件紐づけを更新する
  - 案件未紐づけプロジェクトに案件を紐づけた後、`unassigned=true` のリストから消えることで完了を確認できる
  - _Requirements: 7.3, 7.4_
  - _Boundary: project_router_

- [x] 5.3 部門一覧・要員一覧・バージョン一覧APIの実装
  - `GET /api/v1/departments` で部門一覧を返す
  - `GET /api/v1/members` でクエリパラメータ `dept_id` による部門フィルタ付き要員一覧を返す
  - `GET /api/v1/forecast-versions` で見込工数バージョン一覧を作成日時降順で返す
  - 各エンドポイントに GET リクエストを送ったとき JSON 配列が正しく返ることで完了を確認できる
  - _Requirements: 6.3, 8.1, 8.2_
  - _Boundary: department_router, member_router, forecast_version_router_

---

- [ ] 6. (P) Core — 計画工数アップロード画面（フロントエンド）
  - _Depends: 2.3_

- [x] 6.1 ドラッグ&ドロップCSVアップロードUIと拡張子バリデーション
  - Ant Design `<Upload.Dragger>` でドラッグ&ドロップとファイル選択ダイアログの両方に対応する
  - ファイル選択時に拡張子チェックを `beforeUpload` で行い、`.csv` 以外は「CSVファイル（.csv）を選択してください」を表示して処理を中断する
  - `.csv` ファイル選択後にアップロード実行ボタンを有効化し、処理中は `<Spin>` でローディング表示して再操作を無効にする
  - `.csv` ファイルを選択するとボタンが有効化され、`.xlsx` ファイルはエラーメッセージが表示されることで完了を確認できる
  - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - _Boundary: CsvUploadArea_

- [x] 6.2 アップロード結果・エラー一覧表示の実装
  - アップロード成功時は `notification.success` でバージョン番号を含む完了メッセージを表示し、`UploadResultPanel` に部門・要員・プロジェクト・工数レコードそれぞれの新規/更新件数を表形式で表示する
  - アップロード失敗時は `notification.error` を表示し、バリデーションエラー一覧（行番号・列名・メッセージ）を `<Table>` でスクロール可能な形式で表示する
  - バリデーションエラーのある CSV をアップロードしたとき行番号・列名・エラーメッセージが一覧表示されることで完了を確認できる
  - _Requirements: 1.5, 1.6_
  - _Boundary: UploadResultPanel_

---

- [ ] 7. (P) Core — 見込工数確認・シミュレーション画面（フロントエンド）
  - _Depends: 2.3_

- [x] 7.1 見込工数マトリクス表示の実装（フィルタ・展開行・警告色）
  - `WorkloadFilter` で部門/チームフィルタと年月範囲（開始・終了年月）を指定し、「表示」ボタンで `useWorkloadMatrix` がAPIを呼び出す
  - `useWorkloadMatrix` フックでバックエンドのフラットリストをピボット変換し、要員行（月次合計 `monthly_sums`）とプロジェクト内訳行のデータ構造を構築する
  - Ant Design `<Table>` の `expandable` で要員行クリック時にプロジェクト別内訳行を展開し、案件単位のサマリ集計も表示する
  - 要員の月次合計が 1.0 人月を超えるセルを `orange-1` 背景色で強調表示する
  - フィルタ指定して「表示」後、マトリクスに要員行が表示され 1.0 超過セルが視覚的に識別できることで完了を確認できる
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_
  - _Boundary: WorkloadMatrix, WorkloadFilter, useWorkloadMatrix_

- [x] 7.2 シミュレーションモードのインライン編集とリアルタイム再計算実装
  - `SimulationToolbar` にシミュレーションモード切り替えスイッチを実装し、ON 時に各セルを `<InputNumber>` に切り替える
  - `useSimulation` フックで変更差分を `Map<string, number | null>` として管理し、セル変更のたびにローカルで月次合計をリアルタイム再計算して表示する
  - 合計が 1.0 人月を超えた時点で警告色を更新し `notification.warning` を表示する（入力・保存はブロックしない）
  - シミュレーションモード中にセル値を変更すると、同一要員の月次合計列がリアルタイムに更新されることで完了を確認できる
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - _Boundary: SimulationToolbar, WorkloadCell, useSimulation_

- [x] 7.3 シミュレーション保存・リセット・CSVダウンロードの実装
  - 「保存」ボタンクリックで `useSimulation` の diff map を `PUT /api/v1/workloads/simulate` に送信し、成功後に diff をクリアしてデータを再取得する
  - 「リセット」ボタンクリックで `DELETE /api/v1/workloads/simulate` を呼び出し、成功後にデータを再取得して計画工数ベースの表示に戻す
  - 「CSVダウンロード」ボタンクリックで `GET /api/v1/workloads/forecast/download` を呼び出し、`simulation_YYYY-MM_YYYY-MM.csv` のファイル名でブラウザダウンロードを開始する
  - 保存後にページをリロードしても保存したシミュレーション値が表示され、リセット後に計画工数表示に戻ることで完了を確認できる
  - _Requirements: 9.6, 9.7, 9.8, 9.9_
  - _Boundary: SimulationToolbar, useSimulation_

---

- [ ] 8. (P) Core — 案件・プロジェクト管理画面（フロントエンド）
  - _Depends: 2.3_

- [x] 8.1 案件一覧・新規登録フォームの実装
  - `MatterListPage` に案件一覧テーブル（案件名・案件コード・顧客名・PM・ステータス・配下PJ数）を表示する
  - 「+ 新規案件登録」ボタンクリックで `MatterFormModal` を開き、案件名（必須）・案件コード（必須）・顧客名・PM・ステータスを入力できるフォームを実装する
  - 案件コード重複時は API の HTTP 409 を受けてフォームに「案件コードが重複しています」をインライン表示する
  - 正常登録後に `Modal` が閉じて一覧テーブルに新規案件が追加表示されることで完了を確認できる
  - _Requirements: 7.1, 7.2, 7.5_
  - _Boundary: MatterListPage, MatterFormModal_

- [x] 8.2 プロジェクト管理・案件紐づけ画面の実装
  - `ProjectManagementPage` にプロジェクト一覧テーブル（案件未紐づけを含む全プロジェクト）を表示する
  - `ProjectEditModal` でWBS名称・WBSコード・表示順の編集フォームを実装する
  - `ProjectAssignModal` で案件未紐づけプロジェクトを選択し、指定した案件に一括紐づけする機能を実装する
  - 案件未紐づけプロジェクトを案件に紐づけた後、一覧の案件列に案件名が表示されることで完了を確認できる
  - _Requirements: 7.3, 7.4_
  - _Boundary: ProjectManagementPage, ProjectEditModal, ProjectAssignModal_

---

- [x] 9. (P) Core — 見込工数バージョン一覧画面（フロントエンド）
  - `ForecastVersionPage` に見込工数バージョン一覧を作成日時の降順で表示する
  - 表示列：バージョン番号・作成日時・作成契機（「計画工数CSVアップロード」）
  - CSVアップロード後にバージョン一覧を確認すると最新バージョンが先頭に追加されていることで完了を確認できる
  - _Depends: 2.3_
  - _Requirements: 6.3_
  - _Boundary: ForecastVersionPage_

---

- [ ] 10. Validation — バックエンドテスト

- [x] 10.1 CSVバリデーションのユニットテスト
  - 必須ヘッダー19列それぞれが欠如した場合に `row_no: null` のエラーが返ることを検証する
  - 会計年度の型エラー・範囲外（0・2101）・月次工数列の負値・文字列・必須文字列の空白など、行バリデーションのエラーパターンを網羅する
  - 複数エラーが同時に存在するとき全エラーが一括収集されることを確認する
  - `pytest` を実行してバリデーション関連テストが全件グリーンになることで完了を確認できる
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 10.2 CSVインポートの統合テスト（ロールバック検証・upsert検証）
  - バリデーションエラーを含む CSV をアップロードした後、DB に何も登録されていないことを確認する（全件ロールバック）
  - 正常な CSV をアップロードした後、departments・members・projects・monthly_workloads・forecast_versions・forecast_snapshots が期待通りに登録されることを確認する
  - 同じ CSV を2回アップロードしたとき、重複 INSERT ではなく upsert（新規0件・更新N件）になることを確認する
  - 全月 0.00 の行をアップロードしたとき、マスタは登録されるが monthly_workloads レコードは作成されないことを確認する
  - `pytest` を実行して統合テストが全件グリーンになることで完了を確認できる
  - _Requirements: 1.6, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2_

- [x] 10.3 フロントエンドhooksのユニットテスト（オプション）
  - `useWorkloadMatrix` がAPIレスポンスを正しくピボット変換し、月次合計と 1.0 超過フラグを正しく計算することを検証する
  - `useSimulation` の差分管理・保存リクエスト変換・リセット後のクリアが期待通りに動作することを検証する
  - `vitest` でフロントエンドhooksテストが全件グリーンになることで完了を確認できる
  - _Requirements: 8.3, 8.4, 8.5, 9.3, 9.4_
