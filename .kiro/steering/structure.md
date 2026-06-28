# ディレクトリ構造

## トップレベル

```
project_management_app/
├── frontend/          # React + Vite フロントエンド
├── backend/           # FastAPI バックエンド
├── CLAUDE.md
└── .kiro/
```

## フロントエンド（`frontend/`）

```
frontend/
├── src/
│   ├── components/     # 再利用可能なUIコンポーネント
│   ├── pages/          # ページレベルのコンポーネント（ルーティング単位）
│   ├── api/            # バックエンドAPIのクライアント関数
│   ├── types/          # TypeScript型定義（バックエンドのスキーマと対応）
│   ├── hooks/          # カスタムReact Hooks
│   ├── utils/          # ユーティリティ関数
│   └── App.tsx
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## バックエンド（`backend/`）

```
backend/
├── app/
│   ├── main.py          # FastAPIエントリポイント・CORS設定
│   ├── database.py      # DB接続設定・セッション管理
│   ├── config.py        # 環境変数・アプリ設定
│   ├── routers/         # エンドポイント定義（機能単位でファイル分割）
│   ├── models/          # SQLAlchemy ORMモデル
│   ├── schemas/         # Pydanticスキーマ（リクエスト/レスポンス定義）
│   └── services/        # ビジネスロジック（ルーターから分離）
├── alembic/             # DBマイグレーション
│   ├── versions/
│   └── env.py
├── tests/
├── requirements.txt
└── .env.example
```

## ファイル命名規則

| レイヤー | 規則 | 例 |
|---------|------|----|
| Reactコンポーネント | PascalCase.tsx | `WorkloadTable.tsx` |
| Reactページ | PascalCase.tsx（`pages/`配下） | `ProjectDetail.tsx` |
| APIクライアント | camelCase.ts | `projectApi.ts` |
| TypeScript型定義 | camelCase.ts | `workloadTypes.ts` |
| Python Router | snake_case.py | `project_router.py` |
| Python Model | snake_case.py | `workload_model.py` |
| Python Schema | snake_case.py | `workload_schema.py` |
| Python Service | snake_case.py | `workload_service.py` |
