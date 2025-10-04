import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";
import typescriptEslint from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [
    {
        ignores: [
            ".next/**/*",
            "node_modules/**/*",
            "out/**/*",
            "eslint.config.js",
            "eslint.config.mjs",
            "postcss.config.mjs",
            "next.config.ts",
            "tailwind.config.js"
        ]
    },
    ...compat.extends("next/core-web-vitals"),
    {
        plugins: {
            "@typescript-eslint": typescriptEslint,
        },

        languageOptions: {
            parser: tsParser,
            ecmaVersion: 2022,
            sourceType: "module",

            parserOptions: {
                project: "./tsconfig.json",
                ecmaFeatures: {
                    jsx: true,
                },
            },
        },

        rules: {
            // TypeScript Rules - Strict Configuration
            "@typescript-eslint/no-explicit-any": "error",
            "@typescript-eslint/prefer-nullish-coalescing": "error",
            "@typescript-eslint/prefer-optional-chain": "error",
            "@typescript-eslint/no-non-null-assertion": "error",
            "@typescript-eslint/no-unnecessary-condition": "off",
            "@typescript-eslint/no-unnecessary-type-assertion": "error",
            "@typescript-eslint/prefer-readonly": "off",
            "@typescript-eslint/require-array-sort-compare": "off",
            "@typescript-eslint/switch-exhaustiveness-check": "error",
            "@typescript-eslint/consistent-type-definitions": "off",
            "@typescript-eslint/consistent-type-imports": "off",
            "@typescript-eslint/no-import-type-side-effects": "off",
            "@typescript-eslint/no-unused-vars": ["error", {
                argsIgnorePattern: "^_",
                varsIgnorePattern: "^_",
                caughtErrorsIgnorePattern: "^_"
            }],
            "@typescript-eslint/no-shadow": "error",
            "@typescript-eslint/no-use-before-define": "error",
            "@typescript-eslint/prefer-as-const": "error",
            "@typescript-eslint/explicit-function-return-type": "off",
            "@typescript-eslint/explicit-module-boundary-types": "off",
            "@typescript-eslint/no-floating-promises": "error",
            "@typescript-eslint/await-thenable": "error",
            "@typescript-eslint/no-misused-promises": "error",

            // Disable conflicting base ESLint rules
            "no-unused-vars": "off",
            "no-shadow": "off",
            "no-use-before-define": "off",

            // React Hooks
            "react-hooks/exhaustive-deps": "warn",

            // General Code Quality
            "max-depth": ["error", 6],
            "max-lines": ["error", 800],
            "max-nested-callbacks": ["error", 5],
            "max-params": ["error", 6],
            "no-console": "off",
            "no-debugger": "error",
            "no-alert": "error",
            "no-eval": "error",
            "no-implied-eval": "error",
            "no-new-func": "error",
            "no-script-url": "error",
            "no-sequences": "error",
            "no-void": "error",
            "no-with": "error",
            "radix": "error",
            "vars-on-top": "error",
            "wrap-iife": "error",
            "yoda": "error",
        },
    },
];