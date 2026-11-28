export const profile = {
	name: "Apolonsoft",
	introduction: "We are Apolonsoft. We build interfaces, design systems, AI-powered applications, and the tools that bring them to life.",
};

export const SITE_TITLE = `${profile.name} — Developers & Designers`;
export const SITE_DESCRIPTION = profile.introduction;

export const skills = [
	{
		title: "Frontend development",
		description: "Fast, accessible websites with a close eye on the details.",
		tools: "Astro, React, Next.js, Angular, Vue.js, Nuxt.js, TypeScript",
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
		tools: "Node.js, Express, Nest, Python, FastAPI, Flask, Django, DRF, PHP, Laravel, Go, Gin, PostgreSQL, MySQL, Redis, RabbitMQ, REST",
		icon: "layers",
		surface: "bg-blush-tint",
	},
	{
		title: "AI engineering",
		description: "Intelligent workflows, LLM integrations, and AI-powered applications.",
		tools: "LLMs, RAG, AI Agents",
		icon: "sparkles",
		surface: "bg-soft-lilac",
	},
] as const;
