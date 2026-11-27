export const profile = {
	name: "Ahmad",
	location: "Tehran",
	timeZone: "Asia/Tehran",
	introduction: "I’m Ahmad, a developer based in Tehran. I build interfaces, design systems, and the tools that bring them to life.",
};

export const SITE_TITLE = `${profile.name} — Developer & Designer`;
export const SITE_DESCRIPTION = profile.introduction;

export const skills = [
	{
		title: "Frontend development",
		description: "Fast, accessible websites with a close eye on the details.",
		tools: "Astro, React, TypeScript",
		icon: "code",
		surface: "bg-powder-blue",
	},
	{
		title: "Interface design",
		description: "Clear layouts and reusable components that feel good to use.",
		tools: "Figma, CSS, Design systems",
		icon: "layout",
		surface: "bg-mint-wash",
	},
	{
		title: "Backend engineering",
		description: "Reliable APIs and data models behind the interface.",
		tools: "Node.js, PostgreSQL, REST",
		icon: "layers",
		surface: "bg-blush-tint",
	},
] as const;
