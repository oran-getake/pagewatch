import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var homeModel: HomeViewModel
    @State private var usage: AccountUsage?
    @State private var errorMessage: String?
    @State private var confirmsDataDeletion = false

    var body: some View {
        List {
            Section("利用状況") {
                LabeledContent("登録件数") {
                    if let usage {
                        Text("\(usage.registered) / \(usage.limit)")
                    } else {
                        ProgressView()
                    }
                }
            }
            Section("サポート") {
                Link(
                    "利用規約",
                    destination: URL(string: "https://example.com/terms")!
                )
                Link(
                    "プライバシーポリシー",
                    destination: URL(string: "https://example.com/privacy")!
                )
                Link(
                    "お問い合わせ",
                    destination: URL(string: "https://example.com/contact")!
                )
            }
            Section("アプリ情報") {
                LabeledContent("バージョン", value: "1.0")
                Text("登録したWebページの文字変更を確認します。画像、動画、広告、レイアウト変更は初版の対象外です。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            Section {
                Button("登録データをすべて削除", role: .destructive) {
                    confirmsDataDeletion = true
                }
            } footer: {
                Text("登録URL、取得本文、変更履歴、匿名端末情報を削除します。")
            }
        }
        .navigationTitle("設定")
        .task {
            do {
                usage = try await APIClient.shared.usage()
            } catch {
                errorMessage = error.localizedDescription
            }
        }
        .confirmationDialog(
            "登録データをすべて削除しますか？",
            isPresented: $confirmsDataDeletion,
            titleVisibility: .visible
        ) {
            Button("すべて削除", role: .destructive) {
                Task {
                    do {
                        try await APIClient.shared.deleteAccount()
                        usage = AccountUsage(registered: 0, limit: 5)
                        await homeModel.load()
                    } catch {
                        errorMessage = error.localizedDescription
                    }
                }
            }
            Button("キャンセル", role: .cancel) {}
        } message: {
            Text("この操作は元に戻せません。")
        }
        .alert("削除できませんでした", isPresented: Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )) {
            Button("閉じる", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "")
        }
    }
}
