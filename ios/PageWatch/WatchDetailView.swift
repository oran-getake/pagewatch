import SwiftUI

struct WatchDetailView: View {
    @EnvironmentObject private var homeModel: HomeViewModel
    @Environment(\.openURL) private var openURL
    @State private var watch: WatchItem
    @State private var changes: [ChangeSummary] = []
    @State private var errorMessage: String?
    @State private var isLoading = false

    init(watch: WatchItem) {
        _watch = State(initialValue: watch)
    }

    var body: some View {
        List {
            Section {
                LabeledContent("状態", value: statusLabel)
                LabeledContent(
                    "カテゴリー",
                    value: WatchCategory(rawValue: watch.category)?.label ?? "その他"
                )
                LabeledContent(
                    "確認頻度",
                    value: WatchFrequency(rawValue: watch.frequency)?.label ?? "1日1回"
                )
                if let checked = watch.lastCheckedAt {
                    LabeledContent("最終確認") {
                        Text(checked.formatted(date: .abbreviated, time: .shortened))
                    }
                }
                if let error = watch.lastError {
                    Text(error)
                        .font(.footnote)
                        .foregroundStyle(.red)
                }
                Button("元ページを開く") {
                    if let url = URL(string: watch.url) {
                        openURL(url)
                    }
                }
            }

            Section("変更履歴") {
                if isLoading {
                    ProgressView()
                } else if changes.isEmpty {
                    Text("変更履歴はまだありません。")
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(changes) { change in
                        NavigationLink {
                            ChangeDetailView(
                                watchID: watch.id,
                                summary: change
                            )
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(change.changedAt.formatted(
                                    date: .abbreviated,
                                    time: .shortened
                                ))
                                Text(change.addedText.isEmpty
                                     ? "削除された文章があります"
                                     : change.addedText)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(2)
                            }
                        }
                    }
                }
            }

            Section {
                Button(watch.isActive ? "監視を一時停止" : "監視を再開") {
                    Task { await toggleActive() }
                }
                Button("今すぐ確認") {
                    Task {
                        await homeModel.check(watch)
                        if let updated = homeModel.watches.first(where: {
                            $0.id == watch.id
                        }) {
                            watch = updated
                        }
                        await loadChanges()
                    }
                }
                .disabled(!watch.isActive)
            }
        }
        .navigationTitle(watch.title)
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await loadChanges()
        }
        .alert("エラー", isPresented: Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )) {
            Button("閉じる", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "")
        }
    }

    private var statusLabel: String {
        switch watch.lastCheckStatus {
        case "changed": "変更あり"
        case "unchanged": "変更なし"
        case "error": "取得失敗"
        case "paused": "停止中"
        default: "未確認"
        }
    }

    private func loadChanges() async {
        isLoading = true
        defer { isLoading = false }
        do {
            changes = try await APIClient.shared.changes(watchID: watch.id)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func toggleActive() async {
        do {
            watch = try await APIClient.shared.updateWatch(
                id: watch.id,
                payload: WatchUpdateRequest(isActive: !watch.isActive)
            )
            await homeModel.load()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

