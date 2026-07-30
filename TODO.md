# 📋 Validator Service Implementation Roadmap for Codex

This document serves as the master step-by-step task list for developing, dockerizing, and deploying the **Validator** visual jailbreak detection service.

---

## 🎯 Architecture Overview

- **Service Purpose:** Accepts a Buddian video page URL (e.g., `https://buddian.com/app/video?id=241`) and a subject description. Extracts direct `.mp4`, uses TwelveLabs to analyze video contents visually, and uses OpenAI to determine if the video violates a protected description.
- **Port & Reverse Proxy:** Listens locally inside Docker at `0.0.0.0:${PORT}` mapped to host `127.0.0.1:${PORT}`. An external Nginx instance proxies `https://validator.prampta.com` to `http://localhost:${PORT}`.
- **Deployment Strategy:** Git-based remote deployment via `deploy.sh` over SSH. Remote container execution via Docker Compose.

---

## 📂 Phase 1: Repository Structure & Environment Configuration

- [ ] **1.1 `.gitignore` Setup**
  - Add `.env` to `.gitignore`.
  - Add `__pycache__/`, `.pytest_cache/`, `.venv/`, `.DS_Store` to `.gitignore`.

- [ ] **1.2 Create `.env.example`**
  - Define all required variables with clear inline comments and placeholder values.
  - Required Keys:
    ```env
    # ==========================================
    # Deployment Configuration
    # ==========================================
    DEPLOY_HOST=your.server.com
    DEPLOY_USER=deployuser
    DEPLOY_DIR=/var/www/validator
    PORT=8080

    # ==========================================
    # External API Credentials
    # ==========================================
    OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
    TWELVELABS_API_KEY=tlk_xxxxxxxxxxxxxxxxxxxxxxxx

    # ==========================================
    # Application Options
    # ==========================================
    TWELVELABS_INDEX_ID=idx_optional_or_default
    DEBUG=false
    ```

- [ ] **1.3 Create `.env` (Local template)**
  - Copy `.env.example` to `.env` with exact matching key order and populate real secrets for dev/deploy.

---

## 🐍 Phase 2: Application Implementation (Python / Web UI)

- [ ] **2.1 Dependencies (`requirements.txt`)**
  - Include: `streamlit`, `twelvelabs`, `openai`, `requests`, `beautifulsoup4`, `python-dotenv`, `uvicorn`, `pydantic`.

- [ ] **2.2 Direct MP4 URL Parser Module (`app/extractor.py`)**
  - Input: Buddian URL (e.g. `https://buddian.com/app/video?id=241`).
  - Logic:
    - If input is already a direct `.mp4` link, return it immediately.
    - Fetch HTML using `requests`.
    - Extract direct `.mp4` source URL using BeautifulSoup/Regex looking for `<video src="...">` or standard Buddian storage pattern (`/storage/generations/.../*.mp4`).
    - Fallback: Handle standard edge cases gracefully with clear error messages.

- [ ] **2.3 TwelveLabs Visual Extraction Module (`app/twelvelabs_client.py`)**
  - Function: Analyze video content using TwelveLabs API (e.g., Pegasus/Marengo model or Generate/Analyze endpoint).
  - Return: A comprehensive physical description string of the primary person/subject visible on screen (hair, eyes, clothing, gender, facial traits).

- [ ] **2.4 OpenAI Arbitration Module (`app/openai_client.py`)**
  - Function: Compare TwelveLabs visual description against the user-provided "Protected Description".
  - Prompting: Enforce strict verdict evaluation.
  - Return: 
    - `DECLINE` (if the visual subject matches the protected description).
    - `APPROVE` (if the visual subject clearly differs).

- [ ] **2.5 Web Application UI (`app/main.py`)**
  - Build UI using Streamlit (or lightweight FastAPI + HTML).
  - UI Elements:
    - Title: `🛡️ Validator — Visual Jailbreak Detection`
    - Input 1: Video URL text box.
    - Input 2: Protected Description text area.
    - Submit Button: `Validate Generation`.
    - Status Feed: Live progress indicators for Extraction → TwelveLabs Scanning → OpenAI Arbitration.
    - Final Banner: Prominent Red **DECLINE** or Green **APPROVE** display with reasoning summary.

---

## 🐳 Phase 3: Dockerization

- [ ] **3.1 `Dockerfile`**
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE ${PORT}
  CMD ["python", "-m", "streamlit", "run", "app/main.py", "--server.port=8080", "--server.address=0.0.0.0"]

```

* [ ] **3.2 `compose.yml**`
```yaml
services:
  validator:
    build: .
    container_name: validator-service
    restart: always
    ports:
      - "127.0.0.1:${PORT}:${PORT}"
    env_file:
      - .env
    environment:
      - PORT=${PORT}

```



---

## 🚀 Phase 4: `deploy.sh` Script

* [ ] **4.1 Implementation Requirements for `deploy.sh**`
* Shebang: `#!/usr/bin/env bash`
* Strict Error Handling: `set -euo pipefail`
* Path Resolution: Use `realpath` on `${BASH_SOURCE[0]}` to locate `.env` relative to the script's directory (works from any execution directory or via symlinks).


* [ ] **4.2 CLI Options & Arguments**
* Support `-h` / `--help`: Display clear usage documentation and exit cleanly.
* Support `-m "COMMIT_MESSAGE"`: Automatically run `git add .`, `git commit -m "MESSAGE"`, and `git push` before triggering deployment.


* [ ] **4.3 `.env` Validation**
* If `.env` does NOT exist OR if any required key (`DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_DIR`, `PORT`, `OPENAI_API_KEY`, `TWELVELABS_API_KEY`) is missing/empty:
* Print error message listing missing keys.
* **Abort immediately with non-zero exit code.**
* NO default or fallback values allowed.




* [ ] **4.4 Remote Deployment Steps over SSH**
1. Determine current local git branch (`git rev-parse --abbrev-ref HEAD`).
2. Verify remote git branch matches.
3. Execute `git pull` on remote server (`ssh $DEPLOY_USER@$DEPLOY_HOST "cd $DEPLOY_DIR && git pull origin $BRANCH"`).
4. Compare local `.env` vs remote `.env` (e.g. via `md5sum` or `cmp`).
* If remote `.env` is missing or different, copy local `.env` to `$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_DIR/.env`.


5. Restart container on remote server:
* `ssh $DEPLOY_USER@$DEPLOY_HOST "cd $DEPLOY_DIR && docker compose up -d --build --remove-orphans"`





---

## 📑 Phase 5: `logs.sh` Script

* [ ] **5.1 Implementation Requirements for `logs.sh**`
* Shebang: `#!/usr/bin/env bash`
* Path Resolution: Use `realpath` on `${BASH_SOURCE[0]}` to locate `.env` in the script directory.
* Support `-h` / `--help`: Display usage guide (e.g., `./logs.sh [-f] [--tail N]`) and exit cleanly.
* `.env` Check: Strict validation for `.env` existence and required keys (`DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_DIR`). Fail immediately if missing.
* Log Streaming Wrapper: Forward all arguments directly to remote Docker Compose logs:
```bash
ssh -t "${DEPLOY_USER}@${DEPLOY_HOST}" "cd ${DEPLOY_DIR} && docker compose logs$@"

```





---

## ✅ Phase 6: Verification & Final Audit

* [ ] Verify `deploy.sh -h` prints help screen.
* [ ] Verify `deploy.sh` without `.env` fails with a explicit error.
* [ ] Test deployment via `./deploy.sh -m "feat: complete validator initial implementation"`.
* [ ] Run `./logs.sh -f` to stream remote container logs.
* [ ] Test live URL `https://validator.prampta.com` against a sample visual jailbreak link and confirm `DECLINE` verdict.

```