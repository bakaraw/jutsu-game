import { defineConfig } from "vite";
import path from "node:path";

export default defineConfig({
	resolve: { alias: { "@shared": path.resolve(import.meta.dirname, "../shared") } },
	server: { fs: { allow: [".."] } },
});
