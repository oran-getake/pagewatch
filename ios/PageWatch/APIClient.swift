import Foundation

enum APIClientError: LocalizedError {
    case invalidBaseURL
    case invalidResponse
    case server(String, Int)

    var errorDescription: String? {
        switch self {
        case .invalidBaseURL:
            "APIの接続先が設定されていません。"
        case .invalidResponse:
            "サーバーから正しい応答を受け取れませんでした。"
        case .server(let message, _):
            message
        }
    }
}

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private var accessToken: String?

    private init() {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.waitsForConnectivity = true
        session = URLSession(configuration: configuration)
        encoder.keyEncodingStrategy = .convertToSnakeCase
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)
            let fractional = ISO8601DateFormatter()
            fractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = fractional.date(from: value) {
                return date
            }
            let plain = ISO8601DateFormatter()
            plain.formatOptions = [.withInternetDateTime]
            if let date = plain.date(from: value) {
                return date
            }
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Invalid ISO-8601 date"
            )
        }
        accessToken = KeychainStore.readToken()
    }

    private var baseURL: URL {
        get throws {
            guard let raw = Bundle.main.object(
                forInfoDictionaryKey: "API_BASE_URL"
            ) as? String,
                  !raw.contains("YOUR-RAILWAY-DOMAIN"),
                  let url = URL(string: raw)
            else {
                throw APIClientError.invalidBaseURL
            }
            return url
        }
    }

    private func ensureAccessToken() async throws {
        if accessToken != nil {
            return
        }
        let response: DeviceTokenResponse = try await request(
            path: "/api/devices/anonymous",
            method: "POST",
            requiresAuthentication: false
        )
        try KeychainStore.saveToken(response.accessToken)
        accessToken = response.accessToken
    }

    private func request<T: Decodable>(
        path: String,
        method: String = "GET",
        body: Encodable? = nil,
        requiresAuthentication: Bool = true
    ) async throws -> T {
        if requiresAuthentication {
            try await ensureAccessToken()
        }
        let url = try baseURL.appending(path: path)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let accessToken, requiresAuthentication {
            request.setValue(
                "Bearer \(accessToken)",
                forHTTPHeaderField: "Authorization"
            )
        }
        if let body {
            request.httpBody = try encoder.encode(AnyEncodable(body))
            request.setValue(
                "application/json",
                forHTTPHeaderField: "Content-Type"
            )
        }
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard 200..<300 ~= httpResponse.statusCode else {
            let message = (try? decoder.decode(APIErrorBody.self, from: data).detail)
                ?? "サーバーでエラーが発生しました。"
            throw APIClientError.server(message, httpResponse.statusCode)
        }
        return try decoder.decode(T.self, from: data)
    }

    private func requestWithoutResponse(
        path: String,
        method: String
    ) async throws {
        try await ensureAccessToken()
        let url = try baseURL.appending(path: path)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue(
            "Bearer \(accessToken!)",
            forHTTPHeaderField: "Authorization"
        )
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard 200..<300 ~= httpResponse.statusCode else {
            let message = (try? decoder.decode(APIErrorBody.self, from: data).detail)
                ?? "サーバーでエラーが発生しました。"
            throw APIClientError.server(message, httpResponse.statusCode)
        }
    }

    func watches() async throws -> [WatchItem] {
        try await request(path: "/api/watches")
    }

    func createWatch(_ payload: WatchCreateRequest) async throws -> WatchItem {
        try await request(path: "/api/watches", method: "POST", body: payload)
    }

    func updateWatch(
        id: String,
        payload: WatchUpdateRequest
    ) async throws -> WatchItem {
        try await request(
            path: "/api/watches/\(id)",
            method: "PATCH",
            body: payload
        )
    }

    func deleteWatch(id: String) async throws {
        try await requestWithoutResponse(path: "/api/watches/\(id)", method: "DELETE")
    }

    func startCheck(id: String) async throws -> CheckJob {
        try await request(path: "/api/watches/\(id)/check", method: "POST")
    }

    func job(id: String) async throws -> CheckJob {
        try await request(path: "/api/check-jobs/\(id)")
    }

    func changes(watchID: String) async throws -> [ChangeSummary] {
        try await request(path: "/api/watches/\(watchID)/changes")
    }

    func change(watchID: String, changeID: String) async throws -> ChangeDetail {
        try await request(path: "/api/watches/\(watchID)/changes/\(changeID)")
    }

    func usage() async throws -> AccountUsage {
        try await request(path: "/api/account/usage")
    }

    func deleteAccount() async throws {
        try await requestWithoutResponse(path: "/api/account", method: "DELETE")
        accessToken = nil
        try KeychainStore.deleteToken()
    }
}

private struct AnyEncodable: Encodable {
    private let encodeValue: (Encoder) throws -> Void

    init(_ wrapped: Encodable) {
        encodeValue = { encoder in
            try wrapped.encode(to: encoder)
        }
    }

    func encode(to encoder: Encoder) throws {
        try encodeValue(encoder)
    }
}
