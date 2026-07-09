# PREREQUISITES — Manual Setup Before Orchestrator Runs

This guide walks through every step you need to do yourself before the orchestrator agent takes over. Nothing here requires coding — just installing tools, logging into accounts, and running a few verification commands.

## Quick Status

| Tool | Status | Action Needed |
|---|---|---|
| Python 3.13 | ✅ Installed | None |
| uv | ✅ Installed | None |
| Node.js 24 | ✅ Installed | None |
| npm | ✅ Installed | None |
| Docker Desktop | ✅ Installed | None |
| Git 2.50 | ✅ Installed | None |
| AWS CLI v2 | ✅ Installed | Needs configuration |
| Terraform | ❌ Not installed | Install below |
| GitHub account | ? | Create if needed |
| AWS account | ✅ Exists | Needs IAM user + CLI keys |

---

## Step 1: Install Terraform

Terraform provisions all AWS infrastructure (S3, SQS, DynamoDB, EC2, ECS, Lambda). The orchestrator uses it extensively.

1. Go to https://developer.hashicorp.com/terraform/install
2. Download the **Windows AMD64** zip
3. Extract the `terraform.exe` file
4. Move it to a folder in your PATH (e.g., `C:\Program Files\terraform\` or `C:\Users\hifia\AppData\Local\Programs\`)
5. Or simply place it in `C:\Users\hifia\Projects\ProjectCerberus\` (project root) for convenience
6. Open a **new** PowerShell window and verify:

```powershell
terraform --version
# Should print: Terraform v1.x.x
```

If you see `"not recognized"`, the folder containing `terraform.exe` is not in your PATH. Use the project-root placement trick to avoid PATH issues.

---

## Step 2: Configure AWS CLI

Your AWS account exists but needs API credentials.

1. Open your browser and log into the **AWS Management Console**
2. Navigate to **IAM → Users → Create user**
   - User name: `project-cerberus-cli`
   - Check "Provide user access to the AWS Management Console" → **NO** (programmatic only)
3. Click **Next** → **Attach policies directly**
4. Search and check **`AdministratorAccess`** (yes, full access — this is a learning sandbox)
   > *For production you'd lock this down. For learning, AdminAccess avoids permission rabbit holes.*
5. Click **Next** → **Create user**
6. Click the created user → **Security credentials** tab → **Create access key**
7. Choose **Command Line Interface (CLI)** → check the acknowledgement → **Next**
8. Copy the **Access Key ID** and **Secret Access Key** somewhere safe

Now configure the CLI:

```powershell
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: paste the key
- **AWS Secret Access Key**: paste the secret
- **Default region name**: `us-east-1`
- **Default output format**: `json`

Verify it works:

```powershell
aws sts get-caller-identity
# Should print your UserId, Account, and Arn
```

---

## Step 3: Initialize Git Repository

The monorepo lives in `ProjectCerberus`. Initialize it locally:

```powershell
cd C:\Users\hifia\Projects\ProjectCerberus
git init
git add -A
git commit -m "Initial scaffold"
```

---

## Step 4: Set Up GitHub Remote

1. Go to https://github.com/new
2. Repository name: `ProjectCerberus` (or whatever you like)
3. Keep it **Private** (you don't want your AWS resources exposed)
4. Do NOT check any "Add a README" / ".gitignore" / "license" boxes
5. Click **Create repository**
6. Follow the "…or push an existing repository from the command line" section:

```powershell
git remote add origin https://github.com/<your-username>/ProjectCerberus.git
git branch -M main
git push -u origin main
```

> If git asks for authentication, use a **Personal Access Token** instead of a password:
> 1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
> 2. Generate new token with `repo` permissions
> 3. Use the token as password when git prompts

---

## Step 5: (Optional but Recommended) Verify Docker Works

```powershell
docker --version
docker run hello-world
```

Should print Docker version and a hello-world message. If Docker Desktop isn't running, start it from the Start Menu first.

---

## Step 6: Final Verification Checklist

Run this in PowerShell:

```powershell
echo "=== TOOL CHECK ==="
python --version
uv --version
node --version
npm --version
docker --version
git --version
aws --version
terraform --version

echo ""
echo "=== AWS CHECK ==="
aws sts get-caller-identity

echo ""
echo "=== GIT CHECK ==="
git status
git remote -v
```

You should see all version numbers printed, your AWS account ID, and a clean git status.

---

## Handoff to Orchestrator

Once all checks pass, tell the orchestrator:

> "I've completed the prerequisites from PREREQUISITES.md. The environment is ready. Proceed with Phase 0."

Or if you're continuing in this session, just say **"Ready"** and the orchestrator will start.
