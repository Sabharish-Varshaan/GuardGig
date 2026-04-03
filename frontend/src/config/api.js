import { NativeModules, Platform } from "react-native";

function resolveFallbackHost() {
	const scriptURL = String(NativeModules?.SourceCode?.scriptURL || "");
	const match = scriptURL.match(/https?:\/\/([^/:]+):\d+/i);
	const scriptHost = match?.[1];

	if (scriptHost && scriptHost !== "127.0.0.1" && scriptHost !== "localhost") {
		return scriptHost;
	}

	return Platform.OS === "android" ? "10.0.2.2" : "127.0.0.1";
}

function normalizeBaseUrl(raw) {
	const trimmed = String(raw || "").trim();

	if (!trimmed) {
		return "";
	}

	const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;

	try {
		const parsed = new URL(withProtocol);
		return `${parsed.protocol}//${parsed.host}`;
	} catch (_error) {
		return "";
	}
}

const envBase = normalizeBaseUrl(process.env.EXPO_PUBLIC_API_BASE_URL);
const resolvedBase = (envBase || `http://${resolveFallbackHost()}:8000`).replace(/\/+$/, "");

export const API_BASE_URL = resolvedBase;
