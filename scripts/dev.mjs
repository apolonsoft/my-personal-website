import { spawn } from "node:child_process";
import path from "node:path";
import process from "node:process";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const apiDir = path.join(rootDir, "apps", "api");

const services = [
	{
		name: "api",
		cmd: "uv",
		args: ["run", "pywrangler", "dev", "--port", "8787"],
		cwd: apiDir,
	},
	{
		name: "web",
		cmd: "npm",
		args: ["run", "dev", "--workspace=apps/web"],
		cwd: rootDir,
	},
];

const children = [];
let shuttingDown = false;

function pipePrefixed(stream, prefix, target) {
	if (!stream) return;
	const rl = readline.createInterface({ input: stream });
	rl.on("line", (line) => {
		target.write(`[${prefix}] ${line}\n`);
	});
}

function shutdown(exitCode = 0) {
	if (shuttingDown) return;
	shuttingDown = true;
	for (const child of children) {
		if (!child.killed) {
			child.kill("SIGTERM");
		}
	}
	setTimeout(() => process.exit(exitCode), 300).unref();
}

for (const svc of services) {
	const child = spawn(svc.cmd, svc.args, {
		cwd: svc.cwd,
		stdio: ["inherit", "pipe", "pipe"],
		env: process.env,
	});
	pipePrefixed(child.stdout, svc.name, process.stdout);
	pipePrefixed(child.stderr, svc.name, process.stderr);

	child.on("exit", (code) => {
		if (!shuttingDown) {
			console.error(`[${svc.name}] exited with code ${code ?? 0}`);
			shutdown(code ?? 1);
		}
	});
	children.push(child);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));
