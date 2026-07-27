import SwiftUI

struct ChangeDetailView: View {
    let watchID: String
    let summary: ChangeSummary
    @Environment(\.openURL) private var openURL
    @State private var detail: ChangeDetail?
    @State private var errorMessage: String?

    var body: some View {
        Group {
            if let detail {
                List {
                    Section("追加された文章") {
                        DiffText(
                            text: detail.addedText,
                            emptyMessage: "追加された文章はありません。",
                            color: .green
                        )
                    }
                    Section("削除された文章") {
                        DiffText(
                            text: detail.removedText,
                            emptyMessage: "削除された文章はありません。",
                            color: .red
                        )
                    }
                    Section("変更前") {
                        Text(detail.beforeText)
                            .textSelection(.enabled)
                    }
                    Section("変更後") {
                        Text(detail.afterText)
                            .textSelection(.enabled)
                    }
                    Section {
                        Button("元ページを開く") {
                            if let url = URL(string: detail.sourceUrl) {
                                openURL(url)
                            }
                        }
                    }
                }
            } else if let errorMessage {
                ContentUnavailableView(
                    "変更内容を取得できません",
                    systemImage: "exclamationmark.triangle",
                    description: Text(errorMessage)
                )
            } else {
                ProgressView("変更内容を取得しています")
            }
        }
        .navigationTitle(summary.changedAt.formatted(
            date: .abbreviated,
            time: .shortened
        ))
        .navigationBarTitleDisplayMode(.inline)
        .task {
            do {
                detail = try await APIClient.shared.change(
                    watchID: watchID,
                    changeID: summary.id
                )
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }
}

private struct DiffText: View {
    let text: String
    let emptyMessage: String
    let color: Color

    var body: some View {
        Text(text.isEmpty ? emptyMessage : text)
            .foregroundStyle(text.isEmpty ? .secondary : color)
            .textSelection(.enabled)
    }
}

