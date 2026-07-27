import Foundation

enum WatchCategory: String, Codable, CaseIterable, Identifiable {
    case job
    case product
    case realEstate = "real_estate"
    case ticket
    case notice
    case other

    var id: String { rawValue }

    var label: String {
        switch self {
        case .job: "求人"
        case .product: "商品"
        case .realEstate: "不動産"
        case .ticket: "チケット"
        case .notice: "お知らせ"
        case .other: "その他"
        }
    }
}

enum WatchFrequency: String, Codable, CaseIterable, Identifiable {
    case daily
    case threeDaily = "three_daily"
    case sixDaily = "six_daily"

    var id: String { rawValue }

    var label: String {
        switch self {
        case .daily: "1日1回"
        case .threeDaily: "1日3回"
        case .sixDaily: "1日6回"
        }
    }
}

struct WatchItem: Codable, Identifiable, Hashable {
    let id: String
    var title: String
    let url: String
    var category: String
    var frequency: String
    var isActive: Bool
    var lastCheckStatus: String
    var lastError: String?
    var lastCheckedAt: Date?
    var nextCheckAt: Date?
    let createdAt: Date
    var updatedAt: Date
}

struct WatchCreateRequest: Encodable {
    let title: String
    let url: String
    let category: String
    let frequency: String
}

struct WatchUpdateRequest: Encodable {
    var title: String? = nil
    var category: String? = nil
    var frequency: String? = nil
    var isActive: Bool? = nil
}

struct DeviceTokenResponse: Decodable {
    let accessToken: String
    let tokenType: String
}

struct CheckJob: Codable, Identifiable {
    let id: String
    let watchTargetId: String
    let source: String
    let status: String
    let attempts: Int
    let runAfter: Date
    let startedAt: Date?
    let finishedAt: Date?
    let errorMessage: String?
    let createdAt: Date
}

struct ChangeSummary: Codable, Identifiable, Hashable {
    let id: String
    let addedText: String
    let removedText: String
    let diffTruncated: Bool
    let changedAt: Date
}

struct ChangeDetail: Codable, Identifiable {
    let id: String
    let addedText: String
    let removedText: String
    let diffTruncated: Bool
    let changedAt: Date
    let beforeText: String
    let afterText: String
    let sourceUrl: String
}

struct APIErrorBody: Decodable {
    let detail: String
}

struct AccountUsage: Decodable {
    let registered: Int
    let limit: Int
}
