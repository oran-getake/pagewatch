import Foundation
import Combine

@MainActor
final class HomeViewModel: ObservableObject {
    @Published private(set) var watches: [WatchItem] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    var changedCount: Int {
        watches.filter { $0.lastCheckStatus == "changed" }.count
    }

    var latestCheckedAt: Date? {
        watches.compactMap(\.lastCheckedAt).max()
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            watches = try await APIClient.shared.watches()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func add(
        title: String,
        url: String,
        category: WatchCategory,
        frequency: WatchFrequency
    ) async -> Bool {
        do {
            let item = try await APIClient.shared.createWatch(
                WatchCreateRequest(
                    title: title,
                    url: url,
                    category: category.rawValue,
                    frequency: frequency.rawValue
                )
            )
            watches.insert(item, at: 0)
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func delete(at offsets: IndexSet) async {
        let targets = offsets.map { watches[$0] }
        for watch in targets {
            do {
                try await APIClient.shared.deleteWatch(id: watch.id)
                watches.removeAll { $0.id == watch.id }
            } catch {
                errorMessage = error.localizedDescription
            }
        }
    }

    func check(_ watch: WatchItem) async {
        do {
            var job = try await APIClient.shared.startCheck(id: watch.id)
            for _ in 0..<30 where ["queued", "running"].contains(job.status) {
                try await Task.sleep(for: .seconds(1))
                job = try await APIClient.shared.job(id: job.id)
            }
            await load()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func checkAll() async {
        for watch in watches where watch.isActive {
            await check(watch)
        }
    }
}
