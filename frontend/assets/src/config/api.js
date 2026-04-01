import { NativeModules, Platform } from "react-native";

function resolveFallbackHost() {
	const scriptURL = NativeModules?.SourceCode?.scriptURL || "";
	const match = scriptURL.match(/https?:\/\/([^/:]+):\d+/i);
	const scriptHost = match?.[1];

	if (scriptHost && scriptHost !== "127.0.0.1" && scriptHost !== "localhost") {
		return scriptHost;
	}

	return Platform.OS === "android" ? "10.0.2.2" : "127.0.0.1";
}

const envBase = (process.env.EXPO_PUBLIC_API_BASE_URL || "").trim();
const resolvedBase = envBase || `http://${resolveFallbackHost()}:8000`;

export const API_BASE_URL = resolvedBase;
