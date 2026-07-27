from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "PageWatch_実装仕様・配置・設計書.pdf"
FONT_DIR = ROOT / "assets" / "fonts"

BLUE = HexColor("#2155CD")
NAVY = HexColor("#102A43")
SKY = HexColor("#EAF2FF")
MINT = HexColor("#E8F7F0")
ORANGE = HexColor("#FFF2DE")
RED = HexColor("#C23B3B")
GRAY = HexColor("#607080")
LIGHT_GRAY = HexColor("#F3F5F7")
LINE = HexColor("#D7DEE7")


pdfmetrics.registerFont(TTFont("NotoSansJP", str(FONT_DIR / "NotoSansJP-Regular.ttf")))
pdfmetrics.registerFont(
    TTFont("NotoSansJP-Bold", str(FONT_DIR / "NotoSansJP-Bold.ttf"))
)
pdfmetrics.registerFontFamily(
    "NotoSansJP",
    normal="NotoSansJP",
    bold="NotoSansJP-Bold",
)


def styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleJP",
            parent=sample["Title"],
            fontName="NotoSansJP-Bold",
            fontSize=27,
            leading=38,
            textColor=NAVY,
            spaceAfter=8 * mm,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleJP",
            parent=sample["Normal"],
            fontName="NotoSansJP",
            fontSize=12,
            leading=19,
            textColor=GRAY,
        ),
        "h1": ParagraphStyle(
            "H1JP",
            parent=sample["Heading1"],
            fontName="NotoSansJP-Bold",
            fontSize=18,
            leading=24,
            textColor=NAVY,
            spaceBefore=2 * mm,
            spaceAfter=5 * mm,
        ),
        "h2": ParagraphStyle(
            "H2JP",
            parent=sample["Heading2"],
            fontName="NotoSansJP-Bold",
            fontSize=12.5,
            leading=18,
            textColor=BLUE,
            spaceBefore=4 * mm,
            spaceAfter=2.5 * mm,
        ),
        "body": ParagraphStyle(
            "BodyJP",
            parent=sample["BodyText"],
            fontName="NotoSansJP",
            fontSize=9.2,
            leading=15,
            textColor=NAVY,
            spaceAfter=2.5 * mm,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "SmallJP",
            parent=sample["BodyText"],
            fontName="NotoSansJP",
            fontSize=7.6,
            leading=11.5,
            textColor=GRAY,
            wordWrap="CJK",
        ),
        "table": ParagraphStyle(
            "TableJP",
            parent=sample["BodyText"],
            fontName="NotoSansJP",
            fontSize=7.6,
            leading=11,
            textColor=NAVY,
            wordWrap="CJK",
        ),
        "table_head": ParagraphStyle(
            "TableHeadJP",
            parent=sample["BodyText"],
            fontName="NotoSansJP-Bold",
            fontSize=7.8,
            leading=11,
            textColor=colors.white,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "callout": ParagraphStyle(
            "CalloutJP",
            parent=sample["BodyText"],
            fontName="NotoSansJP",
            fontSize=9,
            leading=14,
            textColor=NAVY,
            wordWrap="CJK",
        ),
    }


S = styles()


def p(value: str, style: str = "body") -> Paragraph:
    return Paragraph(value, S[style])


def bullet(value: str) -> Paragraph:
    return Paragraph(f"• {value}", S["body"])


def make_table(
    headers: list[str],
    rows: list[list[str]],
    widths: list[float],
) -> Table:
    data = [[p(item, "table_head") for item in headers]]
    data.extend([[p(item, "table") for item in row] for row in rows])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    for row_index in range(1, len(data)):
        if row_index % 2 == 0:
            table.setStyle(
                TableStyle(
                    [("BACKGROUND", (0, row_index), (-1, row_index), LIGHT_GRAY)]
                )
            )
    return table


def callout(title: str, body: str, color: colors.Color = SKY) -> Table:
    content = [
        p(f"<b>{title}</b>", "callout"),
        p(body, "callout"),
    ]
    table = Table([[content]], colWidths=[166 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0.7, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def architecture_drawing() -> Drawing:
    drawing = Drawing(470, 250)

    def box(
        x: float,
        y: float,
        width: float,
        height: float,
        title: str,
        detail: str,
        fill: colors.Color,
    ) -> None:
        drawing.add(
            Rect(
                x,
                y,
                width,
                height,
                rx=8,
                ry=8,
                fillColor=fill,
                strokeColor=BLUE,
                strokeWidth=1,
            )
        )
        drawing.add(
            String(
                x + width / 2,
                y + height - 19,
                title,
                fontName="NotoSansJP-Bold",
                fontSize=10,
                textAnchor="middle",
                fillColor=NAVY,
            )
        )
        drawing.add(
            String(
                x + width / 2,
                y + 13,
                detail,
                fontName="NotoSansJP",
                fontSize=7,
                textAnchor="middle",
                fillColor=GRAY,
            )
        )

    box(5, 155, 100, 55, "iPhone", "SwiftUI / Keychain", SKY)
    box(180, 155, 110, 55, "API Service", "FastAPI / HTTPS", MINT)
    box(180, 35, 110, 55, "PostgreSQL", "登録・本文・差分・ジョブ", ORANGE)
    box(355, 185, 105, 45, "Cron Service", "1時間ごとに起動", SKY)
    box(355, 105, 105, 45, "Worker Service", "確認処理を常駐実行", MINT)
    box(355, 25, 105, 45, "公開Webページ", "robots.txt / HTML", ORANGE)

    for x1, y1, x2, y2 in (
        (105, 182, 180, 182),
        (235, 155, 235, 90),
        (355, 207, 290, 70),
        (355, 127, 290, 70),
        (407, 105, 407, 70),
    ):
        drawing.add(Line(x1, y1, x2, y2, strokeColor=BLUE, strokeWidth=1.2))
    drawing.add(
        String(
            140,
            190,
            "HTTPS",
            fontName="NotoSansJP",
            fontSize=7,
            textAnchor="middle",
            fillColor=GRAY,
        )
    )
    drawing.add(
        String(
            328,
            75,
            "job",
            fontName="NotoSansJP",
            fontSize=7,
            textAnchor="middle",
            fillColor=GRAY,
        )
    )
    return drawing


def page_header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.line(22 * mm, height - 15 * mm, width - 22 * mm, height - 15 * mm)
    canvas.setFont("NotoSansJP", 7)
    canvas.setFillColor(GRAY)
    canvas.drawString(22 * mm, height - 11 * mm, "PageWatch / v0.1.0")
    canvas.drawRightString(
        width - 22 * mm,
        10 * mm,
        f"{doc.page}",
    )
    canvas.restoreState()


def build_story() -> list:
    story: list = []

    story.extend(
        [
            Spacer(1, 32 * mm),
            p("PageWatch", "title"),
            p("実装仕様・配置・設計書", "title"),
            Spacer(1, 4 * mm),
            p(
                "登録したWebページを定期確認し、前回から変わった文章だけを"
                "分かりやすく表示するiPhoneアプリ",
                "subtitle",
            ),
            Spacer(1, 22 * mm),
            callout(
                "この版の到達点",
                "元の簡易仕様を実装可能な単位へ分解し、Railway API・Worker・"
                "Cron・PostgreSQLとSwiftUIアプリのソースを作成した。"
                "匿名端末認証、ジョブ分離、SSRF防止、重複実行防止を設計へ追加している。",
                MINT,
            ),
            Spacer(1, 55 * mm),
            p("Version 0.1.0 / 2026-07-26", "small"),
            p("初版実装・TestFlight前段階", "small"),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("1. 結論と範囲", "h1"),
            p(
                "PageWatch初版は、iPhone単体ではなく、API・常駐Worker・定期起動"
                "Cron・PostgreSQLを一組として動かす。登録、一覧、停止、削除、手動確認、"
                "自動確認、文章差分、変更前後表示までを実装対象とする。",
            ),
            make_table(
                ["項目", "初版の確定値", "理由"],
                [
                    ["登録上限", "1匿名端末5件", "サーバー負荷と対象サイト負荷を限定"],
                    [
                        "確認頻度",
                        "24時間 / 8時間 / 4時間",
                        "1日1回・3回・6回を同じ仕組みで扱う",
                    ],
                    ["手動確認", "1URLにつき5分間隔", "連打と過剰アクセスを防止"],
                    [
                        "比較対象",
                        "公開ページの文字",
                        "画像・動画・細かな配置は初版対象外",
                    ],
                    ["保存", "初回と変更時の全文", "変更なし本文を重複保存しない"],
                    ["認証", "匿名Bearer token", "ログインなしでも他端末から隔離"],
                ],
                [34 * mm, 55 * mm, 77 * mm],
            ),
            Spacer(1, 5 * mm),
            callout(
                "公開前に残る作業",
                "Railwayへの配置、正式URL設定、Apple署名、実機・TestFlight試験、"
                "利用規約とプライバシーページ、対象サイトの自動取得可否確認。",
                ORANGE,
            ),
            PageBreak(),
            p("2. システム配置", "h1"),
            architecture_drawing(),
            p(
                "APIは登録と結果返却に専念する。外部ページの取得はWorkerだけが行う。"
                "Cronは期限到来分をジョブ化して終了するため、予定時刻の判定と重い取得処理が"
                "分離される。",
            ),
            make_table(
                ["Service", "Start command", "外部公開"],
                [
                    [
                        "API",
                        "alembic upgrade head && uvicorn app.main:app "
                        "--host 0.0.0.0 --port $PORT",
                        "する",
                    ],
                    ["Worker", "python -m app.worker", "しない"],
                    ["Cron", "python -m app.jobs.enqueue_due", "しない"],
                    ["PostgreSQL", "Railway管理", "しない"],
                ],
                [28 * mm, 110 * mm, 28 * mm],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("3. 画面配置", "h1"),
            p("ホーム", "h2"),
            make_table(
                ["位置", "要素", "動作"],
                [
                    ["上部左", "一括更新", "有効な登録URLを順番に手動確認"],
                    ["上部右", "＋", "URL登録画面を開く"],
                    ["概要", "変更あり件数・最終確認", "現在の監視状況を要約"],
                    ["一覧", "状態点・名称・結果・時刻", "タップで監視詳細"],
                    ["行スワイプ", "確認 / 削除", "個別更新または関連データ削除"],
                ],
                [28 * mm, 57 * mm, 81 * mm],
            ),
            p("監視詳細と変更詳細", "h2"),
            make_table(
                ["画面", "上からの配置"],
                [
                    [
                        "監視詳細",
                        "状態 → カテゴリー → 頻度 → 最終確認 → エラー → 元ページ → "
                        "変更履歴 → 一時停止/再開 → 今すぐ確認",
                    ],
                    [
                        "変更詳細",
                        "追加文章 → 削除文章 → 変更前全文 → 変更後全文 → 元ページ",
                    ],
                    [
                        "設定",
                        "登録数 → 利用規約 → プライバシー → 問い合わせ → アプリ情報",
                    ],
                ],
                [35 * mm, 131 * mm],
            ),
            Spacer(1, 5 * mm),
            callout(
                "状態色",
                "変更あり=橙、変更なし=緑、取得失敗=赤、停止中=灰、未確認=青。"
                "色だけに依存せず、必ず状態名も併記する。",
                SKY,
            ),
            PageBreak(),
            p("4. 実装の流れ", "h1"),
            make_table(
                ["工程", "実装内容", "完了判定"],
                [
                    [
                        "1. 安全境界",
                        "匿名token、URL正規化、DNS・IP検査",
                        "内部URLと未認証アクセスを拒否",
                    ],
                    [
                        "2. 登録・Queue",
                        "5件上限、重複防止、初回job",
                        "登録とjobが同時に保存",
                    ],
                    [
                        "3. 取得・差分",
                        "robots、HTML抽出、hash、行差分",
                        "初回/同一/変更の3ケースが成立",
                    ],
                    [
                        "4. API",
                        "一覧、詳細、停止、削除、履歴",
                        "所有端末以外から404",
                    ],
                    [
                        "5. SwiftUI",
                        "Keychain、画面、job polling",
                        "実機で一連操作が成立",
                    ],
                    [
                        "6. 公開",
                        "Railway、TestFlight、法務URL",
                        "7日試験とApp Store申告完了",
                    ],
                ],
                [30 * mm, 72 * mm, 64 * mm],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("5. API設計", "h1"),
            make_table(
                ["Method", "Path", "役割"],
                [
                    ["POST", "/api/devices/anonymous", "匿名端末token発行"],
                    ["POST", "/api/watches", "URL登録・初回job作成"],
                    ["GET", "/api/watches", "登録一覧"],
                    ["PATCH", "/api/watches/{id}", "名称・分類・頻度・停止更新"],
                    ["DELETE", "/api/watches/{id}", "関連データを含め削除"],
                    ["POST", "/api/watches/{id}/check", "手動job作成、202返却"],
                    ["GET", "/api/check-jobs/{id}", "job状態"],
                    ["GET", "/api/watches/{id}/changes", "変更履歴50件"],
                    [
                        "GET",
                        "/api/watches/{id}/changes/{change_id}",
                        "追加・削除・変更前後",
                    ],
                    ["DELETE", "/api/account", "匿名端末と全関連データを削除"],
                    ["GET", "/health", "DB接続を含む死活確認"],
                ],
                [20 * mm, 83 * mm, 63 * mm],
            ),
            p("主要なHTTPエラー", "h2"),
            make_table(
                ["HTTP", "条件", "表示"],
                [
                    ["401", "tokenなし・無効", "認証情報が無効"],
                    ["404", "所有対象・履歴がない", "見つからない"],
                    ["409", "5件上限・重複・停止中", "具体的な理由"],
                    ["422", "URL・入力不正", "修正内容"],
                    ["429", "5分以内の再確認", "残り秒数"],
                ],
                [20 * mm, 70 * mm, 76 * mm],
            ),
            PageBreak(),
            p("6. データ設計", "h1"),
            make_table(
                ["テーブル", "保存内容", "増加条件"],
                [
                    ["users", "匿名token hash", "新しい端末"],
                    ["watch_targets", "URL・状態・次回確認", "URL登録"],
                    ["snapshots", "本文・hash・HTTP状態", "初回または変更"],
                    ["changes", "前後snapshot・追加・削除", "変更時のみ"],
                    ["check_logs", "結果・error・日時", "確認ごと"],
                    ["check_jobs", "待機・実行・完了", "初回・手動・定期"],
                ],
                [35 * mm, 87 * mm, 44 * mm],
            ),
            p("重要制約", "h2"),
            bullet("同一端末の同じ正規化URLは1件だけ。"),
            bullet("1つの監視対象でqueued/runningのjobは1件だけ。"),
            bullet("削除時はsnapshot、change、log、jobを連鎖削除。"),
            bullet("WorkerはFOR UPDATE SKIP LOCKEDで1件を確保。"),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("7. セキュリティ設計", "h1"),
            p(
                "自由入力URLは、Railway内部やクラウドメタデータへの接続口になり得る。",
                "body",
            ),
            make_table(
                ["段階", "検査"],
                [
                    ["1", "HTTP/HTTPSだけ許可"],
                    ["2", "URL内のユーザー名・パスワードを拒否"],
                    ["3", "80/443以外を拒否"],
                    ["4", "localhost、.local、.internal等を拒否"],
                    ["5", "DNSの全解決結果が公開IPか確認"],
                    ["6", "検査済みIPへ接続し、TLSは元ホスト名で検証"],
                    ["7", "リダイレクト先も最初から再検査"],
                    ["8", "15秒・2MB・3転送で打ち切り"],
                ],
                [24 * mm, 142 * mm],
            ),
            Spacer(1, 5 * mm),
            callout(
                "対象サイトへの配慮",
                "robots.txtを確認し、ログイン・CAPTCHAを回避しない。元ページへの"
                "リンクを残し、初版では文章の変更確認に必要な範囲だけを保存する。",
                ORANGE,
            ),
            PageBreak(),
            p("8. 失敗の局所化", "h1"),
            make_table(
                ["失敗", "影響範囲", "回復"],
                [
                    ["1サイトが遅い", "Workerの1job", "timeout後に次job"],
                    ["不正URL", "その登録要求", "422で拒否"],
                    ["対象サイト拒否", "その監視対象", "error理由を保存"],
                    [
                        "Worker停止",
                        "確認処理",
                        "10分超のrunningを回収して再処理",
                    ],
                    ["Cron失敗", "新規定期job", "次回Cronで再判定"],
                    ["API再起動", "操作中の通信", "DB上の登録・jobは維持"],
                    ["PostgreSQL停止", "全機能", "healthcheck失敗、DB復旧"],
                ],
                [43 * mm, 56 * mm, 67 * mm],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("9. テストと完成条件", "h1"),
            p(
                "自動テストはURL安全性、本文抽出、差分、匿名認証、所有者分離、"
                "登録・停止・再開・削除、snapshot保存条件を対象とする。",
            ),
            make_table(
                ["層", "現在の確認", "公開前の追加"],
                [
                    ["Python", "18 tests / lint / compile", "PostgreSQL実DB"],
                    ["Migration", "SQLite upgrade・差分なし", "Railway PostgreSQL"],
                    ["API", "TestClient結合試験", "公開HTTPSからの疎通"],
                    ["Worker", "mock HTMLで初回・同一・変更", "代表5サイトで7日"],
                    ["iOS", "source・plist・配置作成", "Mac/Xcode・実機・TestFlight"],
                ],
                [30 * mm, 65 * mm, 71 * mm],
            ),
            p("初版公開判定", "h2"),
            bullet("RailwayのAPI・Worker・Cron・PostgreSQLが継続稼働。"),
            bullet("代表5サイトで7日間の誤検知・取得失敗を記録。"),
            bullet("TestFlight実機試験を完了。"),
            bullet("利用規約、プライバシー、App Store申告が実装と一致。"),
            PageBreak(),
            p("10. 公開前チェックリスト", "h1"),
            make_table(
                ["状態", "作業"],
                [
                    ["□", "Release API URLをRailway HTTPSへ変更"],
                    ["□", "Bundle IDとApple署名Teamを正式値へ変更"],
                    ["□", "User-Agentの連絡URLを正式サポートURLへ変更"],
                    ["□", "利用規約・プライバシー・問い合わせURLを作成"],
                    ["□", "アプリアイコンとApp Storeスクリーンショット"],
                    ["□", "代表5サイト・7日間の試験運用"],
                    ["□", "TestFlightで登録・変更・停止・削除を実機確認"],
                    ["□", "設定画面から全登録データを削除できることを確認"],
                    ["□", "対象サイトの利用規約とrobots.txtを確認"],
                    ["□", "App Privacy回答を実装と一致"],
                ],
                [20 * mm, 146 * mm],
            ),
            Spacer(1, 7 * mm),
            callout(
                "次の実作業",
                "RailwayでPostgreSQLを作り、同じGitHubリポジトリからAPI・Worker・"
                "Cronの3サービスを配置する。APIの公開URLが確定した時点で"
                "Release.xcconfigへ反映し、Xcodeで実機確認へ進む。",
                MINT,
            ),
        ]
    )
    return story


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="PageWatch 実装仕様・配置・設計書",
        author="PageWatch Project",
        subject="PageWatch v0.1.0 implementation and architecture",
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )
    doc.addPageTemplates(
        PageTemplate(id="PageWatch", frames=[frame], onPage=page_header_footer)
    )
    doc.build(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    build()
