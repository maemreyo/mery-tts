module.exports = {
  forbidden: [
    {
      name: "no-feature-to-feature-imports",
      comment: "Features communicate through shared contracts, not direct imports.",
      severity: "error",
      from: { path: "^src/features/([^/]+)/" },
      to: { path: "^src/features/([^/]+)/", pathNot: "^src/features/$1/" }
    },
    {
      name: "generated-api-is-quarantined",
      comment: "Generated API code must not import app code.",
      severity: "error",
      from: { path: "^src/api/generated/" },
      to: { path: "^src/(features|shared)/" }
    },
    {
      name: "components-use-wrappers-not-generated-api",
      comment: "Feature UI uses wrappers/hooks instead of generated endpoints directly.",
      severity: "error",
      from: { path: "^src/features/" },
      to: { path: "^src/api/generated/" }
    },
    {
      name: "shared-does-not-import-features",
      comment: "Shared modules must stay reusable and cannot depend on feature code.",
      severity: "error",
      from: { path: "^src/shared/" },
      to: { path: "^src/features/" }
    },
    {
      name: "runtime-does-not-import-test-support",
      comment: "Production code must not depend on MSW, Vitest setup, or test-only helpers.",
      severity: "error",
      from: { path: "^src/(api|features|shared|main\\.tsx|styles\\.css)" },
      to: { path: "^src/test/|/__tests__/" }
    },
    {
      name: "generated-api-only-through-shared-wrapper",
      comment: "Generated client access is centralized in shared/api/meryApi.ts for stable feature contracts.",
      severity: "error",
      from: { path: "^src/(features|shared)/(?!api/meryApi\\.ts)" },
      to: { path: "^src/api/generated/" }
    }
  ],
  options: { tsPreCompilationDeps: true, doNotFollow: { path: "node_modules" } }
};
