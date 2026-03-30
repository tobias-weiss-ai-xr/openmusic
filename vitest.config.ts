import { defineConfig } from 'vitest/config'

// Workspace-aware Vitest config: run tests in all packages with src/**/*
export default defineConfig({
  test: {
    // Include tests in all packages under packages/*/src
    include: [
      'packages/**/src/**/*.test.ts',
      'packages/**/src/**/*.spec.ts',
      'packages/**/src/**/*.test.tsx',
      'packages/**/src/**/*.spec.tsx',
    ],
    // Use Node environment by default for TS packages
    environment: 'node',
  },
})
