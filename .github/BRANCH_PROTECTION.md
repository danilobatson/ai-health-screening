# GitHub Branch Protection Configuration
# These settings should be applied to the main branch via GitHub UI or API

## Recommended Branch Protection Rules for `main`:

### Required Status Checks:
- ✅ `quality-gates (backend)`
- ✅ `quality-gates (frontend)`
- ✅ `quality-gates (security)`
- ✅ `quality-gates (integration)`

### Protection Settings:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require a pull request before merging
- ✅ Require approvals: 1 (for team environments)
- ✅ Dismiss stale reviews when new commits are pushed
- ✅ Restrict pushes that create files larger than 100MB

### Advanced Settings:
- ✅ Do not allow bypassing the above settings
- ✅ Restrict who can push to matching branches (admin only)

## How This Works with Vercel:

1. **Developer creates PR** → Quality gates run automatically
2. **Quality gates pass** → PR can be merged
3. **PR merged to main** → Vercel automatically deploys
4. **Deployment completes** → Post-deployment health checks run
5. **Health checks pass** → Deployment confirmed successful

## To Apply These Rules:

### Via GitHub UI:
1. Go to repository Settings → Branches
2. Add rule for `main` branch
3. Configure protection settings as listed above

### Via GitHub CLI:
```bash
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["quality-gates (backend)","quality-gates (frontend)","quality-gates (security)","quality-gates (integration)"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

## Benefits:
- 🛡️ **Zero bad deployments**: Quality gates prevent broken code from reaching production
- ⚡ **Fast feedback**: Developers know immediately if their code has issues
- 🚀 **Automated deployment**: Vercel handles deployment once quality is assured
- 📊 **Compliance**: Enterprise-level process with audit trail
