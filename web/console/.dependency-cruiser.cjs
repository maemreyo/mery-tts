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
    }
  ],
  options: { tsPreCompilationDeps: true, doNotFollow: { path: "node_modules" } }
};
