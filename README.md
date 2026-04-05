GitHub Enterprise の管理者権限
Personal Access Token（PAT）または GitHub App のトークン

必要スコープ: manage_billing:copilot, read:org, read:enterprise

## 環境準備
pip install requests

## PATの準備
GitHub の Settings → Developer settings → Personal access tokens → Fine-grained tokens で以下のスコープを付与：
スコープ用途manage_billing:copilotシート・請求情報の読み取り
read:orgOrganization メンバー情報
read:enterpriseEnterprise 情報
copilot使用状況データ

## 実行例
```
# GitHub.com の Organization を調査
python copilot_analyzer.py \
  --token ghp_xxxxxxxxxxxx \
  --org  your-org-name

# GitHub Enterprise Server (GHES) の場合
python copilot_analyzer.py \
  --token ghp_xxxxxxxxxxxx \
  --base-url https://github.your-company.com/api/v3 \
  --enterprise your-enterprise \
  --org your-org-name \
  --output-dir ./report
```

## 出力ファイル
ファイル    内容
enterprise_daily_*.csv  日別の提案数・採用数・アクティブユーザー数
enterprise_by_language_*.csv    言語別の採用率
enterprise_seats_*.csv  ユーザーごとのシート割り当て状況・最終利用日
org_daily_*.csvOrganization 単位の日別データ

* データ保持期間: GitHub の使用状況データは最大 28日分 のみ取得可能です（Enterprise は最大 365日の場合あり）
* 権限: Enterprise オーナー、または Billing Manager 権限が必要です
* GHES バージョン: GitHub Enterprise Server は 3.8 以降 で Copilot API に対応しています

