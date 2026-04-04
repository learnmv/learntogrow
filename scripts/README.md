# Question Generation Scripts

## Overview

These scripts generate questions using the dev API endpoint and store them in the `learntogrow_dev` database.

## Files

- `generate_questions.py` - Main generation script with parallel API calls
- `run_generator.sh` - Wrapper script for cronjob execution with logging

## Setup

### 1. Install Dependencies

```bash
cd scripts
pip install httpx sqlalchemy psycopg2-binary
```

### 2. Environment Variables (Required)

```bash
export DATABASE_URL="postgresql://admin:admin@123@10.0.0.131:30432/learntogrow_dev"
export API_BASE_URL="http://localhost:8000"  # Optional, defaults to localhost:8000
```

**Note:** `DATABASE_URL` is now required. The script will exit with an error if not provided.

### 3. Usage

**Generate 100 questions with 6 parallel calls:**
```bash
python3 generate_questions.py --count 100 --parallel 6
```

**Generate continuously (infinite mode):**
```bash
python3 generate_questions.py --parallel 6 --infinite
```

**Generate for specific standard:**
```bash
python3 generate_questions.py --standard-id 5 --count 50 --parallel 3
```

**With specific difficulty:**
```bash
python3 generate_questions.py --count 100 --difficulty 0.5 --parallel 6
```

## Cronjob Setup

### Option 1: Crontab (User)

```bash
# Edit crontab
crontab -e

# Add line to run every hour
crontab -e
0 * * * * /home/sysadmin/learntogrow/scripts/run_generator.sh 60 6
```

### Option 2: Systemd Timer (Recommended for production)

**Create service file:** `/etc/systemd/system/learntogrow-generator.service`

```ini
[Unit]
Description=LearnToGrow Question Generator
After=network.target

[Service]
Type=oneshot
User=sysadmin
WorkingDirectory=/home/sysadmin/learntogrow
ExecStart=/home/sysadmin/learntogrow/scripts/run_generator.sh 100 6
Environment=DATABASE_URL=postgresql://admin:admin@123@10.0.0.131:30432/learntogrow_dev
Environment=API_BASE_URL=http://localhost:8000
```

**Create timer file:** `/etc/systemd/system/learntogrow-generator.timer`

```ini
[Unit]
Description=Run LearnToGrow question generator every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable learntogrow-generator.timer
sudo systemctl start learntogrow-generator.timer

# Check status
sudo systemctl list-timers --all
sudo systemctl status learntogrow-generator.timer
```

## Log Files

Logs are written to `/var/log/learntogrow/question_generator.log`

View logs:
```bash
tail -f /var/log/learntogrow/question_generator.log
```

## Performance Tuning

- **parallel 6**: Makes 6 concurrent API calls (safe with current DB pool of 10)
- **Ollama timeout**: 300s (5 minutes) per request
- **Batch processing**: Questions are processed in batches of `parallel` size

## Monitoring

Check generation progress:
```bash
# Count questions in database
psql -U admin -d learntogrow_dev -c "SELECT COUNT(*) FROM questions;"

# Questions by standard
psql -U admin -d learntogrow_dev -c "SELECT standard_id, COUNT(*) FROM questions GROUP BY standard_id;"
```
