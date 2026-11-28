interface Env {
	ASSETS: Fetcher;
	API?: Fetcher;
	API_URL?: string;
	PUBLIC_API_URL?: string;
}

type Runtime = import("@astrojs/cloudflare").Runtime<Env>;

declare namespace App {
	interface Locals extends Runtime {}
}
