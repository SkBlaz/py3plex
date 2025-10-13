# Codecov Badge Setup Instructions

## Issue Fixed

The Codecov badge was showing "unknown" because the GitHub Actions workflow was missing the required token for Codecov v4.

## Changes Made

1. **Updated `.github/workflows/tests.yml`**:
   - Added `token: ${{ secrets.CODECOV_TOKEN }}` to the codecov-action@v4 step
   - This allows the workflow to upload coverage data to Codecov

2. **Updated `README.md`**:
   - Changed badge URL from `https://codecov.io/gh/SkBlaz/py3plex/branch/master/graph/badge.svg`
   - To: `https://codecov.io/gh/SkBlaz/py3plex/graph/badge.svg`
   - Removed branch-specific path to use default branch automatically

## Required Action: Add Codecov Token

To make the badge work, you need to add the `CODECOV_TOKEN` secret to your GitHub repository:

### Step 1: Get Your Codecov Token

1. Go to https://codecov.io/
2. Log in (you can use your GitHub account)
3. Navigate to your repository: `SkBlaz/py3plex`
4. Go to Settings → General
5. Copy the "Repository Upload Token"

### Step 2: Add Token to GitHub Secrets

1. Go to your GitHub repository: https://github.com/SkBlaz/py3plex
2. Click on **Settings** (repository settings, not your account settings)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Name: `CODECOV_TOKEN`
6. Value: Paste the token you copied from Codecov
7. Click **Add secret**

### Step 3: Verify It Works

1. Push a commit or create a pull request
2. Wait for the tests workflow to complete
3. Check that the coverage is uploaded successfully in the workflow logs
4. The badge in the README should now show the actual coverage percentage instead of "unknown"

## Alternative: Codecov App (No Token Required)

If you prefer not to use a token, you can install the Codecov GitHub App:

1. Go to https://github.com/apps/codecov
2. Click "Install" or "Configure"
3. Grant access to the `SkBlaz/py3plex` repository
4. Remove the `token:` line from `.github/workflows/tests.yml`

The app approach is easier but requires GitHub App permissions.

## Verification

After adding the token, the next test run should:
- Upload coverage data successfully
- Show a message like "Coverage uploaded to Codecov" in the workflow logs
- Update the badge to show the actual coverage percentage (e.g., "85%")

## Troubleshooting

**If the badge still shows "unknown":**
- Check that the `CODECOV_TOKEN` secret is set correctly in GitHub
- Verify the workflow ran successfully and uploaded coverage
- Check the Codecov website to see if coverage data was received
- Allow a few minutes for the badge to update after coverage is uploaded

**If you see "403 Forbidden" errors:**
- The token may be incorrect or expired
- Regenerate the token in Codecov settings and update the GitHub secret

## More Information

- Codecov Documentation: https://docs.codecov.com/docs
- GitHub Actions Secrets: https://docs.github.com/en/actions/security-guides/encrypted-secrets
