import rss from "@astrojs/rss";
import { getPosts } from "../lib/posts";
import { SITE_TITLE, SITE_DESCRIPTION } from "../constants";

export const prerender = false;

export async function GET(context) {
	const posts = await getPosts(context.locals);
	return rss({
		title: SITE_TITLE,
		description: SITE_DESCRIPTION,
		site: context.site,
		items: posts.map((post) => ({
			...post.data,
			link: `/blog/${post.id}/`,
		})),
	});
}
