# Deployment Guide

This guide explains how to deploy WPGen and configure automated deployments for generated WordPress themes.

## Prerequisites

- Python >= 3.10
- Git
- GitHub account with personal access token
- (Optional) WordPress site with REST API enabled

## Required GitHub Secrets

When using GitHub Actions for deployment, configure these secrets in your repository settings (`Settings > Secrets and variables > Actions`):

### Core Secrets

- **`GITHUB_TOKEN`**: Automatically provided by GitHub Actions (no setup needed)
- **`ANTHROPIC_API_KEY`** or **`OPENAI_API_KEY`**: LLM provider API key

### Deployment Secrets (Optional)

For WordPress deployment via REST API:

- **`WP_SITE_URL`**: WordPress site URL (e.g., `https://example.com`)
- **`WP_USERNAME`**: WordPress admin username
- **`WP_APP_PASSWORD`**: WordPress application password (generate at `/wp-admin/profile.php`)

For FTP deployment:

- **`FTP_HOST`**: FTP server hostname
- **`FTP_USERNAME`**: FTP username
- **`FTP_PASSWORD`**: FTP password
- **`FTP_REMOTE_PATH`**: Remote path to themes directory

For SSH deployment:

- **`SSH_HOST`**: SSH server hostname
- **`SSH_USERNAME`**: SSH username
- **`SSH_PRIVATE_KEY`**: SSH private key
- **`SSH_REMOTE_PATH`**: Remote path to themes directory

## Deployment Methods

### 1. GitHub Actions (Recommended)

WPGen can create a GitHub Actions workflow that automatically deploys your theme.

**Enable in `config.yaml`:**

```yaml
deployment:
  enabled: true
  method: github_actions
```

**Generated workflow** (`.github/workflows/deploy-theme.yml`):

```yaml
name: Deploy WordPress Theme

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to WordPress
        uses: distributhor/workflow-webhook@v3
        env:
          webhook_url: ${{ secrets.WP_DEPLOY_WEBHOOK }}
          webhook_secret: ${{ secrets.WP_DEPLOY_SECRET }}
```

### 2. FTP Deployment

**Configuration:**

```yaml
deployment:
  enabled: true
  method: ftp
  ftp:
    host: ftp.example.com
    port: 21
    username: your-username  # Or use FTP_USERNAME env var
    remote_path: /public_html/wp-content/themes
```

### 3. SSH/SFTP Deployment

**Configuration:**

```yaml
deployment:
  enabled: true
  method: ssh
  ssh:
    host: example.com
    port: 22
    username: your-username  # Or use SSH_USERNAME env var
    remote_path: /var/www/html/wp-content/themes
    key_file: ~/.ssh/id_rsa  # Or use SSH_PRIVATE_KEY env var
```

### 4. WordPress REST API Direct Upload

**Configuration:**

```yaml
wordpress_api:
  enabled: true
  auto_deploy: true
  auto_activate: true
```

**Environment variables:**

```bash
export WP_SITE_URL=https://example.com
export WP_USERNAME=admin
export WP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

## Manual Deployment

### Local Testing

1. **Generate theme:**

```bash
python -m wpgen --prompt "Modern blog theme" --output output/
```

2. **Copy to WordPress:**

```bash
cp -r output/my-theme /var/www/html/wp-content/themes/
```

3. **Activate in WordPress admin:**

Navigate to `Appearance > Themes` and activate your theme.

### CI/CD Pipeline

**Example `.github/workflows/wpgen-ci.yml`:**

```yaml
name: Generate and Deploy Theme

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      prompt:
        description: 'Theme description'
        required: true
        default: 'Modern responsive blog theme'

jobs:
  generate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Generate theme
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python -m wpgen \
            --prompt "${{ github.event.inputs.prompt || 'Modern blog theme' }}" \
            --output output/ \
            --push-github

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: wordpress-theme
          path: output/
```

## Environment Variables

WPGen respects these environment variables:

### LLM Configuration

- `WPGEN_LLM_PROVIDER`: Override provider (`openai`, `anthropic`, `local-ollama`)
- `WPGEN_OPENAI_MODEL`: Override OpenAI model
- `WPGEN_ANTHROPIC_MODEL`: Override Anthropic model
- `WPGEN_OLLAMA_MODEL`: Override Ollama model

### API Keys

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GITHUB_TOKEN`: GitHub personal access token

### File Handling

- `WPGEN_MAX_UPLOAD_SIZE`: Max upload size in bytes (default: 25MB)
- `WPGEN_MAX_IMAGE_SIZE`: Max image size in bytes (default: 5MB)
- `WPGEN_MAX_PDF_PAGES`: Max PDF pages to process (default: 50)

## Troubleshooting

### Authentication Issues

**Problem**: `403 Forbidden` when pushing to GitHub

**Solution**: Ensure your GitHub token has `repo` scope:

```bash
# Verify token scopes
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### SSL Certificate Errors

**Problem**: SSL verification fails

**Solution**: Update your config.yaml:

```yaml
wordpress_api:
  verify_ssl: false  # For self-signed certificates
```

### Deployment Timeouts

**Problem**: Deployment times out

**Solution**: Increase timeout in config:

```yaml
wordpress_api:
  timeout: 120  # Increase to 120 seconds
```

### Permission Errors

**Problem**: Cannot write to themes directory

**Solution**: Check directory permissions:

```bash
# On server
chown -R www-data:www-data /var/www/html/wp-content/themes
chmod -R 755 /var/www/html/wp-content/themes
```

## Production Checklist

Before deploying to production:

- [ ] Change `web.secret_key` in config.yaml
- [ ] Set `web.debug` to `false`
- [ ] Configure CORS origins (don't use `*` in production)
- [ ] Enable SSL certificate verification
- [ ] Set up proper logging (JSON format recommended)
- [ ] Configure rate limiting for API endpoints
- [ ] Set up monitoring and alerting
- [ ] Back up your WordPress site before first deployment
- [ ] Test theme in staging environment first

## Support

For deployment issues:

1. Check logs: `logs/wpgen.log`
2. Enable debug logging: `logging.level: DEBUG` in config.yaml
3. Review GitHub Actions logs (if using CI/CD)
4. Open an issue: https://github.com/Blueibear/wpgen/issues
