# GitHub Copilot 利用状況調査ツール

GitHub Enterprise / GitHub.com の Copilot 利用状況を GitHub API 経由で取得・集計・CSV 出力するスクリプトです。

## 機能

- **採用率（Acceptance Rate）** の集計（提案数ベース・行数ベース）
- **言語別内訳**（Python / TypeScript / Go など）の採用率分析
- **日別アクティブユーザー数（DAU）** の推移取得
- **シート割り当て状況**（割り当て済み・最終利用日）の一覧出力
- **Enterprise / Organization** 両レベルに対応
- **GitHub Enterprise Server（GHES）** にも対応（`--base-url` オプション）

## 必要要件

- Python 3.9 以上
- GitHub Enterprise オーナー権限 または Billing Manager 権限
- GitHub Personal Access Token（PAT）

## インストール

```bash
git clone https://github.com/your-org/copilot-analyzer.git
cd copilot-analyzer
pip install -r requirements.txt
```

## 事前準備：Personal Access Token の作成

GitHub の **Settings → Developer settings → Personal access tokens → Fine-grained tokens** にアクセスし、以下のスコープを付与した PAT を作成してください。

| スコープ | 用途 |
|---|---|
| `manage_billing:copilot` | シート・請求情報の読み取り |
| `read:org` | Organization メンバー情報 |
| `read:enterprise` | Enterprise 情報 |
| `copilot` | 使用状況データの読み取り |

> **注意**: Classic Token を使用する場合は `admin:org` および `manage_billing:copilot` スコープを付与してください。

## 使い方

### GitHub.com の Organization を調査する

```bash
python copilot_analyzer.py \
  --token ghp_xxxxxxxxxxxx \
  --org   your-org-name
```

### GitHub.com の Enterprise を調査する

```bash
python copilot_analyzer.py \
  --token      ghp_xxxxxxxxxxxx \
  --enterprise your-enterprise-slug
```

### GitHub Enterprise Server（GHES）を調査する

```bash
python copilot_analyzer.py \
  --token      ghp_xxxxxxxxxxxx \
  --base-url   https://github.your-company.com/api/v3 \
  --enterprise your-enterprise \
  --org        your-org-name \
  --output-dir ./report
```

### すべてのオプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--token` | （必須） | GitHub PAT |
| `--enterprise` | なし | Enterprise スラッグ |
| `--org` | なし | Organization 名 |
| `--base-url` | `https://api.github.com` | API エンドポイント（GHES の場合に変更） |
| `--output-dir` | `./copilot_report` | CSV 出力先ディレクトリ |

> `--enterprise` と `--org` は両方同時に指定可能です。

## 出力ファイル

実行すると `--output-dir` で指定したディレクトリに以下の CSV が生成されます。

| ファイル名 | 内容 |
|---|---|
| `enterprise_daily_YYYYMMDD_HHMMSS.csv` | Enterprise の日別：提案数・採用数・アクティブユーザー数 |
| `enterprise_by_language_YYYYMMDD_HHMMSS.csv` | Enterprise の言語別採用率 |
| `enterprise_seats_YYYYMMDD_HHMMSS.csv` | Enterprise のシート割り当て一覧・最終利用日 |
| `org_daily_YYYYMMDD_HHMMSS.csv` | Organization の日別データ |
| `org_by_language_YYYYMMDD_HHMMSS.csv` | Organization の言語別採用率 |
| `org_seats_YYYYMMDD_HHMMSS.csv` | Organization のシート割り当て一覧 |

## 取得できる主な指標

| 指標 | 説明 |
|---|---|
| **採用率（Acceptance Rate）** | 提案されたコード候補のうち採用された割合（件数ベース） |
| **行採用率（Line Acceptance Rate）** | 提案行数に対する採用行数の割合 |
| **DAU（Daily Active Users）** | 日別のアクティブユーザー数 |
| **言語別採用率** | 各プログラミング言語ごとの提案数・採用率 |
| **シート稼働率** | 割り当てシートのうち実際に使用されている割合 |

## 実行結果の例

```
==================================================
  Enterprise サマリ (your-enterprise)
==================================================
  period                        : 2024-11-01 ～ 2024-11-28
  total_suggestions             : 154320
  total_acceptances             : 61728
  acceptance_rate_%             : 40.0
  total_lines_suggested         : 892100
  total_lines_accepted          : 312235
  line_acceptance_rate_%        : 35.0
  avg_daily_active_users        : 87.3

  シート総数: 120
  アクティブシート: 95
```

## 注意事項

- **データ保持期間**: 使用状況データは最大 **28 日分**のみ取得可能です（Enterprise プランは最大 365 日の場合あり）。
- **API レート制限**: GitHub API のレート制限（認証済み：5,000 req/h）に注意してください。シート数が多い場合はページネーションにより複数リクエストが発生します。
- **GHES バージョン**: GitHub Enterprise Server は **v3.8 以降** で Copilot API に対応しています。それ以前のバージョンでは一部エンドポイントが利用できません。
- **権限**: Enterprise オーナーまたは Billing Manager 権限が必要です。Organization レベルのみであれば Organization オーナー権限で利用可能です。

## ライセンス

MIT License
