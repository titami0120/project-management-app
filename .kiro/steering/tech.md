# 技術スタック

## フロントエンド

| 項目 | 技術 | バージョン |
|------|------|----------|
| フレームワーク | React | 18.x |
| ビルドツール | Vite | 5.x |
| 言語 | TypeScript | 5.x |
| UIコンポーネント | Ant Design | 5.x |
| スタイリング | Ant Design のデフォルト（追加CSSは最小限） |
| APIクライアント | Axios |
| 状態管理 | React Context（小規模）/ Zustand（複雑化した場合） |

## バックエンド

| 項目 | 技術 | バージョン |
|------|------|----------|
| フレームワーク | FastAPI | 0.110.x 以降 |
| 言語 | Python | 3.11 以降 |
| ORM | SQLAlchemy | 2.x（非同期対応） |
| バリデーション | Pydantic v2 |
| DBマイグレーション | Alembic |

## データベース

| フェーズ | 技術 |
|---------|------|
| 初期開発 | SQLite |
| 本番・拡張時 | PostgreSQL（SQLAlchemy接続先の変更のみで移行する） |

## 開発ツール

- **Ruff**：Pythonのリンター・フォーマッター
- **ESLint + Prettier**：TypeScriptのリント・フォーマット

## コーディング規約

### Python（バックエンド）
- 命名規則：`snake_case`
- 型ヒント必須（すべての関数引数・戻り値に付与する）
- エンドポイントはRouterで機能単位に分割する（`routers/`配下）
- ビジネスロジックはServiceに分離し、Routerには書かない

### TypeScript（フロントエンド）
- 命名規則：コンポーネントはPascalCase、関数・変数はcamelCase
- 型定義は`types/`ディレクトリに集約する
- `any`型の使用禁止
- APIレスポンスの型は`types/`に定義し、バックエンドのPydanticスキーマと対応させる
