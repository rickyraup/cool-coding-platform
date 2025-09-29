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
            // TypeScript Rules - Relaxed for deployment
            "@typescript-eslint/no-explicit-any": "warn",
            "@typescript-eslint/prefer-nullish-coalescing": "warn",
            "@typescript-eslint/prefer-optional-chain": "warn",
            "@typescript-eslint/no-non-null-assertion": "warn",
            "@typescript-eslint/no-unnecessary-condition": "off",
            "@typescript-eslint/no-unnecessary-type-assertion": "warn",
            "@typescript-eslint/prefer-readonly": "off",
            "@typescript-eslint/require-array-sort-compare": "off",
            "@typescript-eslint/switch-exhaustiveness-check": "warn",
            "@typescript-eslint/consistent-type-definitions": "off",
            "@typescript-eslint/consistent-type-imports": "off",
            "@typescript-eslint/no-import-type-side-effects": "off",
            "@typescript-eslint/no-unused-vars": ["warn", {
                argsIgnorePattern: "^_",
                varsIgnorePattern: "^_",
                caughtErrorsIgnorePattern: "^_"
            }],
            "@typescript-eslint/no-shadow": "warn",
            "@typescript-eslint/no-use-before-define": "warn",
            "@typescript-eslint/prefer-as-const": "warn",
            "@typescript-eslint/explicit-function-return-type": "off",
            "@typescript-eslint/explicit-module-boundary-types": "off",
            "@typescript-eslint/no-floating-promises": "warn",
            "@typescript-eslint/await-thenable": "warn",
            "@typescript-eslint/no-misused-promises": "warn",

            // Disable conflicting base ESLint rules
            "no-unused-vars": "off",
            "no-shadow": "off", 
            "no-use-before-define": "off",

            // General Code Quality
            "complexity": ["warn", 20],
            "max-depth": ["warn", 6],
            "max-lines": ["warn", 800],
            "max-lines-per-function": ["warn", 150],
            "max-nested-callbacks": ["warn", 5],
            "max-params": ["warn", 6],
            "no-console": "off",
            "no-debugger": "error",
            "no-alert": "warn",
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