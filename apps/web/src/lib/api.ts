export interface ApiPost {
	id: number;
	slug: string;
	title: string;
	description: string;
	content: string;
	category: string;
	hero_image_key: string | null;
	hero_image_url: string;
	image_alt: string;
	published: boolean;
	pub_date: string;
	updated_date: string | null;
	created_at: string;
}

function getApiBaseUrl(locals?: App.Locals): string {
	return (
		locals?.runtime?.env?.API_URL ||
		import.meta.env.API_URL ||
		"http://127.0.0.1:8787"
	).replace(/\/+$/, "");
}

function getPublicApiBaseUrl(locals?: App.Locals): string {
	return (
		locals?.runtime?.env?.PUBLIC_API_URL ||
		import.meta.env.PUBLIC_API_URL ||
		getApiBaseUrl(locals)
	).replace(/\/+$/, "");
}

export async function apiFetch(
	locals: App.Locals | undefined,
	path: string,
	init?: RequestInit,
): Promise<Response> {
	const normalizedPath = path.startsWith("/") ? path : `/${path}`;
	const serviceBinding = locals?.runtime?.env?.API;

	if (!import.meta.env.DEV && serviceBinding) {
		return serviceBinding.fetch(
			new Request(`https://api.internal${normalizedPath}`, init),
		);
	}

	return fetch(`${getApiBaseUrl(locals)}${normalizedPath}`, init);
}

export function resolveImageUrl(
	locals: App.Locals | undefined,
	heroImageUrl: string,
): string {
	if (heroImageUrl.startsWith("/api/")) {
		return `${getPublicApiBaseUrl(locals)}${heroImageUrl}`;
	}
	return heroImageUrl;
}
