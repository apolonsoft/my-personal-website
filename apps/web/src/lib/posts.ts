import { apiFetch, resolveImageUrl, type ApiPost } from "./api";

export interface BlogPostData {
	title: string;
	description: string;
	pubDate: Date;
	updatedDate?: Date;
	category: string;
	heroImage: string;
	imageAlt: string;
}

export interface BlogPostItem {
	id: string;
	data: BlogPostData;
	body: string;
}

function mapApiPost(locals: App.Locals | undefined, post: ApiPost): BlogPostItem {
	return {
		id: post.slug,
		data: {
			title: post.title,
			description: post.description,
			pubDate: new Date(post.pub_date),
			updatedDate: post.updated_date ? new Date(post.updated_date) : undefined,
			category: post.category,
			heroImage: resolveImageUrl(locals, post.hero_image_url),
			imageAlt: post.image_alt,
		},
		body: post.content,
	};
}

export async function getPosts(locals?: App.Locals): Promise<BlogPostItem[]> {
	try {
		const res = await apiFetch(locals, "/api/posts");
		if (!res.ok) {
			console.error(`Failed to fetch posts from API: ${res.status}`);
			return [];
		}
		const posts = (await res.json()) as ApiPost[];
		return posts
			.map((post) => mapApiPost(locals, post))
			.sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
	} catch (error) {
		console.error("Error fetching posts from API:", error);
		return [];
	}
}

export async function getPostBySlug(
	locals: App.Locals | undefined,
	slug: string,
): Promise<BlogPostItem | null> {
	if (!slug) {
		return null;
	}
	try {
		const res = await apiFetch(locals, `/api/posts/${encodeURIComponent(slug)}`);
		if (res.status === 404) {
			return null;
		}
		if (!res.ok) {
			console.error(`Failed to fetch post '${slug}' from API: ${res.status}`);
			return null;
		}
		const post = (await res.json()) as ApiPost;
		return mapApiPost(locals, post);
	} catch (error) {
		console.error(`Error fetching post '${slug}' from API:`, error);
		return null;
	}
}
