# Publishing @royalsolution/ontosight to npm

Maintainers only. Requires npm login with publish access to the **`@royalsolution`** scope.

## Prerequisites

1. **Create the npm organization** (one-time): https://www.npmjs.com/org/create — name it **`royalsolution`**. Add your npm user as an **owner** (or use the account that creates the org). Without this org, publish fails with:
   ```
   npm error 404 Not Found - PUT ... - Scope not found
   ```
2. Publish `ontosight` and `ontosight-codegraph` to PyPI (see sibling `PUBLISH.md` files).
3. Set `ontosightCodegraphVersion` in `package.json` to match the PyPI release.

## Publish

```bash
cd packages/ontosight
npm login          # account must be an @royalsolution org owner/member with publish rights
npm whoami
npm run test:cli
npm publish --access public
```

`publishConfig.access` is already `public` in `package.json`; `--access public` is still required on first publish of a scoped package.

## Troubleshooting

| Error | Cause | Fix |
|-------|--------|-----|
| `Scope not found` (404 on PUT) | `@royalsolution` org does not exist on npm | Create org at https://www.npmjs.com/org/create |
| `403 Forbidden` | Logged-in user is not in the org | Add user under org **Members** with publish permission |
| `403` version already exists | Same semver published before | `npm version patch --no-git-tag-version` and retry |
