#!/usr/bin/env python3
"""
GitHub Enterprise Copilot 利用状況調査スクリプト
"""

import requests
import json
import csv
from datetime import datetime
import argparse
import os

class GitHubCopilotAnalyzer:
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def _get(self, path: str, params: dict = None) -> dict | list:
        url = f"{self.base_url}{path}"
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    # ── Enterprise レベル ──────────────────────────────────────

    def get_enterprise_usage(self, enterprise: str) -> dict:
        """Enterprise 全体の Copilot 使用状況（採用率含む）"""
        return self._get(f"/enterprises/{enterprise}/copilot/usage")

    def get_enterprise_billing(self, enterprise: str) -> dict:
        """Enterprise のシート数・請求情報"""
        return self._get(f"/enterprises/{enterprise}/copilot/billing")

    def get_enterprise_seats(self, enterprise: str) -> list:
        """Enterprise の全シート割り当て一覧"""
        seats, page = [], 1
        while True:
            data = self._get(
                f"/enterprises/{enterprise}/copilot/billing/seats",
                params={"per_page": 100, "page": page}
            )
            items = data.get("seats", [])
            if not items:
                break
            seats.extend(items)
            page += 1
        return seats

    # ── Organization レベル ────────────────────────────────────

    def get_org_usage(self, org: str) -> list:
        """Organization の日別 Copilot 使用状況"""
        return self._get(f"/orgs/{org}/copilot/usage")

    def get_org_billing(self, org: str) -> dict:
        """Organization のシート数・請求情報"""
        return self._get(f"/orgs/{org}/copilot/billing")

    def get_org_seats(self, org: str) -> list:
        """Organization の全シート割り当て一覧"""
        seats, page = [], 1
        while True:
            data = self._get(
                f"/orgs/{org}/copilot/billing/seats",
                params={"per_page": 100, "page": page}
            )
            items = data.get("seats", [])
            if not items:
                break
            seats.extend(items)
            page += 1
        return seats

    # ── 集計・レポート ──────────────────────────────────────────

    def summarize_usage(self, usage_data: list) -> dict:
        """日別データを集計してサマリを返す"""
        if not usage_data:
            return {}

        total_suggestions  = sum(d.get("total_suggestions_count", 0)  for d in usage_data)
        total_acceptances  = sum(d.get("total_acceptances_count", 0)  for d in usage_data)
        total_lines_sug    = sum(d.get("total_lines_suggested", 0)    for d in usage_data)
        total_lines_acc    = sum(d.get("total_lines_accepted", 0)     for d in usage_data)
        total_active_users = sum(d.get("total_active_users", 0)       for d in usage_data)

        acceptance_rate = (
            round(total_acceptances / total_suggestions * 100, 2)
            if total_suggestions > 0 else 0
        )
        line_acceptance_rate = (
            round(total_lines_acc / total_lines_sug * 100, 2)
            if total_lines_sug > 0 else 0
        )

        return {
            "period":                f"{usage_data[0]['day']} ～ {usage_data[-1]['day']}",
            "total_suggestions":     total_suggestions,
            "total_acceptances":     total_acceptances,
            "acceptance_rate_%":     acceptance_rate,
            "total_lines_suggested": total_lines_sug,
            "total_lines_accepted":  total_lines_acc,
            "line_acceptance_rate_%": line_acceptance_rate,
            "avg_daily_active_users": round(total_active_users / len(usage_data), 1),
        }

    def breakdown_by_language(self, usage_data: list) -> list:
        """言語別の提案数・採用数を集計"""
        lang_map = {}
        for day in usage_data:
            for breakdown in day.get("breakdown", []):
                lang = breakdown.get("language", "unknown")
                if lang not in lang_map:
                    lang_map[lang] = {"suggestions": 0, "acceptances": 0, "lines_suggested": 0, "lines_accepted": 0}
                lang_map[lang]["suggestions"]    += breakdown.get("suggestions_count", 0)
                lang_map[lang]["acceptances"]    += breakdown.get("acceptances_count", 0)
                lang_map[lang]["lines_suggested"] += breakdown.get("lines_suggested", 0)
                lang_map[lang]["lines_accepted"]  += breakdown.get("lines_accepted", 0)

        result = []
        for lang, v in sorted(lang_map.items(), key=lambda x: x[1]["suggestions"], reverse=True):
            rate = round(v["acceptances"] / v["suggestions"] * 100, 2) if v["suggestions"] > 0 else 0
            result.append({
                "language": lang,
                **v,
                "acceptance_rate_%": rate
            })
        return result

    # ── 出力 ───────────────────────────────────────────────────

    def export_csv(self, data: list, filename: str):
        if not data:
            print(f"  [skip] データなし: {filename}")
            return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"  [CSV] {filename}")

    def print_summary(self, label: str, summary: dict):
        print(f"\n{'='*50}")
        print(f"  {label}")
        print(f"{'='*50}")
        for k, v in summary.items():
            print(f"  {k:<30}: {v}")


# ── エントリポイント ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GitHub Copilot 利用状況レポート")
    parser.add_argument("--token",      required=True,  help="GitHub PAT")
    parser.add_argument("--enterprise", default=None,   help="Enterprise スラッグ")
    parser.add_argument("--org",        default=None,   help="Organization 名")
    parser.add_argument("--base-url",   default="https://api.github.com", help="GHE Server URL (例: https://github.example.com/api/v3)")
    parser.add_argument("--output-dir", default="./copilot_report", help="出力ディレクトリ")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    analyzer = GitHubCopilotAnalyzer(args.token, args.base_url)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Enterprise レポート
    if args.enterprise:
        print(f"\n[Enterprise: {args.enterprise}]")
        try:
            usage    = analyzer.get_enterprise_usage(args.enterprise)
            billing  = analyzer.get_enterprise_billing(args.enterprise)
            seats    = analyzer.get_enterprise_seats(args.enterprise)
            summary  = analyzer.summarize_usage(usage)
            by_lang  = analyzer.breakdown_by_language(usage)

            analyzer.print_summary(f"Enterprise サマリ ({args.enterprise})", summary)
            print(f"\n  シート総数: {billing.get('total_seats', 'N/A')}")
            print(f"  アクティブシート: {billing.get('seat_breakdown', {}).get('active_this_cycle', 'N/A')}")

            analyzer.export_csv(usage,   f"{args.output_dir}/enterprise_daily_{ts}.csv")
            analyzer.export_csv(by_lang, f"{args.output_dir}/enterprise_by_language_{ts}.csv")
            analyzer.export_csv(seats,   f"{args.output_dir}/enterprise_seats_{ts}.csv")

        except requests.HTTPError as e:
            print(f"  [Error] {e}")

    # Organization レポート
    if args.org:
        print(f"\n[Organization: {args.org}]")
        try:
            usage   = analyzer.get_org_usage(args.org)
            billing = analyzer.get_org_billing(args.org)
            seats   = analyzer.get_org_seats(args.org)
            summary = analyzer.summarize_usage(usage)
            by_lang = analyzer.breakdown_by_language(usage)

            analyzer.print_summary(f"Organization サマリ ({args.org})", summary)
            print(f"\n  シート総数: {billing.get('total_seats', 'N/A')}")

            analyzer.export_csv(usage,   f"{args.output_dir}/org_daily_{ts}.csv")
            analyzer.export_csv(by_lang, f"{args.output_dir}/org_by_language_{ts}.csv")
            analyzer.export_csv(seats,   f"{args.output_dir}/org_seats_{ts}.csv")

        except requests.HTTPError as e:
            print(f"  [Error] {e}")

    if not args.enterprise and not args.org:
        print("--enterprise または --org を指定してください")


if __name__ == "__main__":
    main()