import { skills } from "../consts";

const iconPaths = {
	code: "m7.5 7-5 5 5 5m9-10 5 5-5 5m-3-14-3 18",
	layout: "M4.5 3.5h15a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2zM2.5 9.5h19M10 9.5v11",
	layers: "m12 2 10 5.5L12 13 2 7.5 12 2Zm-10 10L12 17.5 22 12M2 16.5 12 22l10-5.5",
};

export default function Skills() {
	return (
		<ul className="mt-8 grid gap-4 md:grid-cols-3 md:gap-6 xl:gap-8">
			{skills.map((skill) => (
				<li key={skill.title} className={`${skill.surface} flex min-h-48 flex-col justify-between gap-8 rounded-xl p-6 lg:min-h-52 lg:p-8`}>
					<div>
						<h3 className="text-[22px] leading-tight font-semibold tracking-[-0.035em]">{skill.title}</h3>
						<p className="mt-2 max-w-72 text-base leading-snug text-studio-ink/80">{skill.description}</p>
					</div>
					<div className="flex items-end justify-between gap-3">
						<p className="text-sm font-medium">{skill.tools}</p>
						<svg aria-hidden="true" width="29" height="29" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
							<path d={iconPaths[skill.icon]} />
						</svg>
					</div>
				</li>
			))}
		</ul>
	);
}
