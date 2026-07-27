import SwiftUI

struct AddWatchView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var model: HomeViewModel
    @State private var title = ""
    @State private var url = ""
    @State private var category = WatchCategory.other
    @State private var frequency = WatchFrequency.daily
    @State private var isSaving = false

    var body: some View {
        Form {
            Section("Webページ") {
                TextField("ページ名", text: $title)
                    .textInputAutocapitalization(.never)
                TextField("https://example.com/page", text: $url)
                    .keyboardType(.URL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
            }
            Section("分類と確認頻度") {
                Picker("カテゴリー", selection: $category) {
                    ForEach(WatchCategory.allCases) { category in
                        Text(category.label).tag(category)
                    }
                }
                Picker("確認頻度", selection: $frequency) {
                    ForEach(WatchFrequency.allCases) { frequency in
                        Text(frequency.label).tag(frequency)
                    }
                }
            }
            Section {
                Text("ログインが必要なページ、CAPTCHAのあるページ、自動取得を禁止しているページは監視できません。")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Webページを登録")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("キャンセル") {
                    dismiss()
                }
            }
            ToolbarItem(placement: .confirmationAction) {
                Button("登録") {
                    Task {
                        isSaving = true
                        let succeeded = await model.add(
                            title: title,
                            url: url,
                            category: category,
                            frequency: frequency
                        )
                        isSaving = false
                        if succeeded {
                            dismiss()
                        }
                    }
                }
                .disabled(!isValid || isSaving)
            }
        }
        .overlay {
            if isSaving {
                ProgressView()
            }
        }
    }

    private var isValid: Bool {
        !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && URL(string: url)?.scheme?.hasPrefix("http") == true
    }
}

