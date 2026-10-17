/// <reference types="vite/client" />

// Strongly-typed environment variables. Declaring the shape here means every
// access to `import.meta.env.VITE_*` is type-checked across the codebase.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_NAME: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
