# Git Configuration for Dual Remotes

## Add Git Aliases

Add these aliases to your `~/.gitconfig` file for convenient dual remote management:

```ini
[alias]
    # Push to both GitLab and GitHub
    push-all = !git push origin && git push github
    
    # Push current branch to both remotes
    push-both = !git push origin HEAD && git push github HEAD
    
    # Show remote status
    remotes-status = !git remote -v && echo "" && git status
    
    # Sync from GitLab to GitHub
    sync-to-github = !git push github
    
    # Sync from GitHub to GitLab
    sync-to-gitlab = !git push origin
```

Setting new remote paths is also quite easy: 

```bash
# Add a new remote
git remote add <name> <url>
#e.g.
git remote add github git@github.com:lutze/probable-octo-broccoli.git

# Update the GitHub path
git remote set-url github git@github.com:lutze/probable-octo-broccoli.git

# Update the GitLab path
git remote set-url origin git@gitlab.com:lms-evo/lms-core-poc.git

```

## Usage Examples

```bash
# Push current branch to both remotes
git push-all

# Push specific branch to both remotes
git push origin main && git push github main

# Check remote status
git remotes-status

# Sync to GitHub only
git sync-to-github
```

## Alternative: Global Git Config

You can also add these aliases globally:

```bash
# Add push-all alias
git config --global alias.push-all '!git push origin && git push github'

# Add remotes-status alias
git config --global alias.remotes-status '!git remote -v && echo "" && git status'
```

## Recommended Workflow

1. **Development**: Work normally on GitLab as primary
2. **Pushing**: Use `git push-all` or the `push-to-both.sh` script
3. **Status**: Use `git remotes-status` to check both remotes
4. **CI/CD**: GitLab handles all testing and deployment

This setup gives you the flexibility to maintain both repositories with minimal effort.
