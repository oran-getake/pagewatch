import SwiftUI

@main
struct PageWatchApp: App {
    @StateObject private var homeModel = HomeViewModel()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(homeModel)
        }
    }
}

