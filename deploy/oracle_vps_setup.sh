# Oracle Cloud Free Tier — LeadIQ v3 Deployment
# Ubuntu 22.04 LTS on Always-Free ARM VM (1GB RAM, 4 cores)

# ── STEP 1: Create VM on Oracle Cloud ──────────────────────────────────
# 1. Go to console.oracle.com → Compute → Instances → Create
# 2. Image: Ubuntu 22.04 LTS
# 3. Shape: VM.Standard.A1.Flex (ARM, 1GB RAM, 4 cores)
# 4. Networking: Create new VCN with default settings
# 5. Add SSH key pair (or use cloud shell)
# 6. Boot — wait for public IP

# ── STEP 2: SSH into your VM ───────────────────────────────────────────
ssh opc@<your-public-ip>

# ── STEP 3: Install dependencies ──────────────────────────────────────
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget

# ── STEP 4: Clone or upload project ────────────────────────────────────
# Option A: Clone from GitHub
git clone https://github.com/yourusername/leadiq.git
cd leadiq

# Option B: Upload from local machine
# scp -r ./leadiq opc@<your-ip>:/home/opc/

# ── STEP 5: Create virtual environment (RAM-safe) ──────────────────────
python3 -m venv venv
source venv/bin/activate

# ── STEP 6: Install dependencies (lightweight only) ────────────────────
# Core packages only — no Neo4j, no Redis, no heavy ML libs
pip install \
    httpx \
    beautifulsoup4 \
    lxml \
    rich \
    fastapi \
    uvicorn \
    pydantic \
    python-multipart \
    requests

# Optional (only if RAM allows)
# pip install neo4j redis pandas numpy

# ── STEP 7: Configure environment ──────────────────────────────────────
cat > .env << 'EOF'
PYTHONUNBUFFERED=1
# Add your tokens here
# GITHUB_TOKEN=ghp_xxxxxxxxxxxx
# OPENAI_API_KEY=sk-xxxxxxxxxxxx
EOF

# ── STEP 8: Test the pipeline ───────────────────────────────────────────
python3 -c "
from backend.collectors.hn import HNCollector
import asyncio
results = asyncio.run(HNCollector().collect())
print(f'HN: {len(results)} leads')
"

# ── STEP 9: Run with systemd (auto-restart, auto-start) ────────────────
sudo bash -c 'cat > /etc/systemd/system/leadiq.service << EOF
[Unit]
Description=LeadIQ v3 Pipeline
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/leadiq
Environment=PATH=/home/opc/leadiq/venv/bin
EnvironmentFile=/home/opc/leadiq/.env
ExecStart=/home/opc/leadiq/venv/bin/python3 -m uvicorn backend.mcp_server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable leadiq
sudo systemctl start leadiq

# ── STEP 10: Verify ─────────────────────────────────────────────────────
sudo systemctl status leadiq
curl http://localhost:8000/health

# ── STEP 11: Setup cron for periodic collection ───────────────────────
# Run pipeline every 15 minutes (lightweight)
(crontab -l 2>/dev/null; echo "*/15 * * * * /home/opc/leadiq/venv/bin/python3 /home/opc/leadiq/scripts/run_world_class_pipeline.py >> /home/opc/leadiq/logs/cron.log 2>&1") | crontab -

mkdir -p /home/opc/leadiq/logs

# ── STEP 12: Open firewall (Oracle Cloud Security List) ────────────────
# Go to: Compute → Instances → Your Instance → Subnet → Security Lists
# Add inbound rule: Port 8000, Source 0.0.0.0/0

# ── Access from browser ───────────────────────────────────────────────
# http://<your-public-ip>:8000
# http://<your-public-ip>:8000/docs (Swagger UI)

# ── Useful commands ────────────────────────────────────────────────────
# View logs:       sudo journalctl -u leadiq -f
# Restart:        sudo systemctl restart leadiq
# Stop:           sudo systemctl stop leadiq
# Check RAM:       free -h
# Check disk:     df -h
# Monitor CPU:    htop