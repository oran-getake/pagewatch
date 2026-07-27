import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var model: HomeViewModel
    @State private var showsAddWatch = false

    var body: some View {
        Group {
            if model.isLoading && model.watches.isEmpty {
                ProgressView("確認しています")
            } else if model.watches.isEmpty {
                ContentUnavailableView(
                    "監視ページはまだありません",
                    systemImage: "eye.slash",
                    description: Text("変更を知りたいWebページを登録してください。")
                )
            } else {
                List {
                    Section {
                        HStack {
                            Label(
                                "変更あり \(model.changedCount)件",
                                systemImage: "bell.badge"
                            )
                            Spacer()
                            if let date = model.latestCheckedAt {
                                Text(date, style: .relative)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    Section("登録中") {
                        ForEach(model.watches) { watch in
                            NavigationLink(value: watch) {
                                WatchRow(watch: watch)
                            }
                            .swipeActions(edge: .leading) {
                                Button {
                                    Task { await model.check(watch) }
                                } label: {
                                    Label("確認", systemImage: "arrow.clockwise")
                                }
                                .tint(.blue)
                            }
                        }
                        .onDelete { offsets in
                            Task { await model.delete(at: offsets) }
                        }
                    }
                }
                .refreshable {
                    await model.load()
                }
                .navigationDestination(for: WatchItem.self) { watch in
                    WatchDetailView(watch: watch)
                }
            }
        }
        .navigationTitle("PageWatch")
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button {
                    Task { await model.checkAll() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .disabled(model.watches.isEmpty || model.isLoading)
                .accessibilityLabel("一括更新")
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showsAddWatch = true
                } label: {
                    Image(systemName: "plus")
                }
                .accessibilityLabel("Webページを登録")
            }
        }
        .sheet(isPresented: $showsAddWatch) {
            NavigationStack {
                AddWatchView()
            }
        }
        .task {
            if model.watches.isEmpty {
                await model.load()
            }
        }
        .alert(
            "確認できませんでした",
            isPresented: Binding(
                get: { model.errorMessage != nil },
                set: { if !$0 { model.errorMessage = nil } }
            )
        ) {
            Button("閉じる", role: .cancel) {
                model.errorMessage = nil
            }
        } message: {
            Text(model.errorMessage ?? "")
        }
    }
}

private struct WatchRow: View {
    let watch: WatchItem

    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(statusColor)
                .frame(width: 10, height: 10)
            VStack(alignment: .leading, spacing: 4) {
                Text(watch.title)
                    .font(.headline)
                    .lineLimit(1)
                HStack {
                    Text(statusLabel)
                    if let date = watch.lastCheckedAt {
                        Text("·")
                        Text(date, style: .relative)
                    }
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
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

    private var statusColor: Color {
        switch watch.lastCheckStatus {
        case "changed": .orange
        case "unchanged": .green
        case "error": .red
        case "paused": .gray
        default: .blue
        }
    }
}

