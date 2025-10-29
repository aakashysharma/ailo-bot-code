# 🤖 AILO System - Complete Guide

## Overview

AILO (AI Learning and Opportunity Advisor) is a locally-running AI career counselor that uses Norwegian educational data from utdanning.no and runs on your local LM Studio with the Gemma model.

## 📦 System Components

### 1. **ailo_chatbot.py**
Interactive chatbot that provides career counseling
- Loads knowledge base from processed data
- Communicates with LM Studio
- Maintains conversation history
- Provides context-aware responses

### 2. **ailo_scheduler.py**
Automatic data update scheduler
- Runs data pipeline at midnight (or custom time)
- Keeps knowledge base fresh
- Logs all updates
- Can run as system service

### 3. **setup_ailo.py**
One-time setup script
- Installs dependencies
- Creates configuration files
- Sets up system services (macOS/Linux)
- Generates documentation

### 4. **start_ailo.py**
Quick start launcher
- Checks if data exists
- Verifies LM Studio connection
- Runs data pipeline if needed
- Launches chatbot

## 🚀 Installation & Setup

### Step 1: Initial Setup
```bash
# Run setup script
python setup_ailo.py
```

This will:
- Install required Python packages
- Create `ailo_config.json`
- Generate service files for automatic updates
- Create AILO_README.md

### Step 2: Configure LM Studio
1. Open LM Studio
2. Download and load: `gemma-3n-E4B-it-MLX-bf16`
3. Go to "Local Server" tab
4. Click "Start Server"
5. Verify it's running on `http://localhost:1234`

### Step 3: Download Data
```bash
# Run complete data pipeline
python main.py

# This will:
# - Download data from 150+ API endpoints
# - Process and normalize the data
# - Create vectorization-ready dataset
# - Takes 10-30 minutes depending on connection
```

### Step 4: Start AILO
```bash
# Quick start (recommended)
python start_ailo.py

# Or run chatbot directly
python ailo_chatbot.py
```

## 💬 Using AILO Chatbot

### Example Conversations

**Utdanningsvalg:**
```
Du: Jeg er interessert i teknologi og vil jobbe med datamaskiner. 
    Hva slags utdanning kan passe for meg?

AILO: Det er mange spennende utdanningsveier innen teknologi! 
      Her er noen alternativer:

      1. **Bachelor i informatikk/datateknologi**
         - 3 år på universitet/høyskole
         - Bred grunnlag i programmering og systemutvikling
         - Høy etterspørsel i arbeidsmarkedet
      
      2. **Ingeniørutdanning (data/elektronikk)**
         - 3-5 år (bachelor/master)
         - Mer teknisk fokus
         - Godt betalt

      3. **Fagbrev (IKT-servicemedarbeider)**
         - 2 år videregående + 2 år lære
         - Raskere vei til jobb
         - Praktisk erfaring

      Hva slags type arbeid ser du for deg? Mer programmering, 
      support, eller hardware?
```

**Lønnsinformasjon:**
```
Du: Hvor mye tjener en sykepleier i Norge?

AILO: Basert på statistikk fra utdanning.no:

      **Sykepleier - Gjennomsnittlig lønn:**
      - Median: 530,000 kr/år (44,000 kr/mnd)
      - Nedre kvartil: 470,000 kr
      - Øvre kvartil: 590,000 kr

      Faktorer som påvirker lønn:
      - ✅ Erfaring (ansiennitet)
      - ✅ Spesialisering (f.eks. intensivsykepleier)
      - ✅ Sektor (privat vs. offentlig)
      - ✅ Arbeidssted (sykehus vs. kommune)

      Vil du vite mer om spesialisering eller utdanningsløp?
```

### Chat Commands
- `exit` / `quit` / `avslutt` - End conversation
- `clear` - Clear conversation history
- `save` - Save conversation to JSON file

## 🔄 Automatic Updates

### Enable Nightly Updates

**Option 1: Run in foreground (for testing)**
```bash
python ailo_scheduler.py
```

**Option 2: Custom time**
```bash
# Run at 2:30 AM instead of midnight
python ailo_scheduler.py --time 02:30
```

**Option 3: Run update now**
```bash
python ailo_scheduler.py --run-now
```

### Install as System Service

**macOS:**
```bash
# Copy launchd plist
cp no.ailo.scheduler.plist ~/Library/LaunchAgents/

# Load and start
launchctl load ~/Library/LaunchAgents/no.ailo.scheduler.plist
launchctl start no.ailo.scheduler

# Check status
launchctl list | grep ailo
```

**Linux:**
```bash
# Edit service file first (replace username)
nano ailo-scheduler.service

# Install service
sudo cp ailo-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ailo-scheduler
sudo systemctl start ailo-scheduler

# Check status
sudo systemctl status ailo-scheduler
```

## ⚙️ Configuration

Edit `ailo_config.json`:

```json
{
  "lm_studio": {
    "url": "http://localhost:1234/v1",
    "model": "gemma-3n-E4B-it-MLX-bf16"
  },
  "data": {
    "output_dir": "utdanning_data",
    "url_list": "url_list.json"
  },
  "scheduler": {
    "update_time": "00:00",
    "enabled": true
  },
  "chatbot": {
    "max_context_docs": 5,
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Parameters Explained:

- **max_context_docs**: How many documents to include as context (more = more accurate but slower)
- **temperature**: Creativity (0.0 = focused, 1.0 = creative)
- **max_tokens**: Maximum response length

## 📊 Monitoring

### Check Logs

**Scheduler logs:**
```bash
tail -f scheduler_logs/scheduler_*.log
```

**Pipeline logs:**
```bash
tail -f utdanning_data/logs/pipeline_*.log
```

**Chatbot conversations:**
```bash
ls -lt ailo_conversation_*.json
```

### Data Status

```bash
# Count raw files
ls -1 utdanning_data/raw/*.json | wc -l

# Count processed files
find utdanning_data/processed -name "*.json" | wc -l

# Check vectorization dataset
ls -lh utdanning_data/processed/text_for_llm/vectorization_dataset.json
```

## 🛠️ Troubleshooting

### Issue: Cannot connect to LM Studio

**Solution:**
1. Open LM Studio
2. Check "Local Server" tab
3. Ensure server is started
4. Test: `curl http://localhost:1234/v1/models`
5. Check firewall settings

### Issue: No data in knowledge base

**Solution:**
```bash
# Run data pipeline
python main.py

# Check if data was created
ls utdanning_data/processed/text_for_llm/

# If still empty, check logs
cat utdanning_data/logs/pipeline_*.log
```

### Issue: AILO gives generic answers

**Possible causes:**
1. Knowledge base not loaded properly
2. LM Studio model not performing well
3. Context window too small

**Solutions:**
- Increase `max_context_docs` in config
- Try different model in LM Studio
- Ensure data pipeline completed successfully

### Issue: Scheduler not running

**Debug steps:**
```bash
# Test manually
python ailo_scheduler.py --run-now

# Check logs
cat scheduler_logs/scheduler_*.log

# macOS: Check launchd
launchctl list | grep ailo

# Linux: Check systemd
sudo systemctl status ailo-scheduler
```

## 🎯 Best Practices

### For Users:
1. **Be specific**: "Hva er opptakskravene for sykepleie ved UiO?" is better than "Fortell om sykepleie"
2. **Follow up**: Ask follow-up questions to dive deeper
3. **Use examples**: "Jeg liker biologi og vil hjelpe mennesker" gives better context
4. **Save important conversations**: Use `save` command for future reference

### For Administrators:
1. **Regular updates**: Ensure scheduler is running
2. **Monitor disk space**: Data files can grow over time
3. **Check logs weekly**: Look for errors or issues
4. **Test after LM Studio updates**: Verify compatibility
5. **Backup conversations**: Important consultations should be archived

## 📈 Performance Optimization

### Speed up responses:
- Reduce `max_context_docs` (trade accuracy for speed)
- Use smaller model in LM Studio
- Run on Mac with M-series chip for better MLX performance

### Improve accuracy:
- Increase `max_context_docs`
- Use larger model in LM Studio
- Ensure knowledge base is up to date

### Reduce resource usage:
- Lower `max_tokens`
- Schedule updates during off-hours
- Limit concurrent requests

## 🔐 Privacy & Security

- ✅ **100% local**: No data sent to external servers
- ✅ **Full control**: All data stays on your machine
- ✅ **No tracking**: Conversations are private
- ✅ **Secure**: LM Studio runs locally
- ✅ **Transparent**: Open source code

## 📚 Data Sources

All data comes from official Norwegian sources:
- **utdanning.no** - Utdanningsdirektoratet
- **150+ API endpoints** covering:
  - Educational programs
  - Occupations and careers
  - Salary statistics
  - Labor market data
  - Apprenticeship companies
  - Schools and institutions

## 🆘 Getting Help

1. **Check logs first**
2. **Run diagnostic**:
   ```bash
   python -c "from ailo_chatbot import AILOChatbot; import asyncio; asyncio.run(AILOChatbot().test_connection())"
   ```
3. **Re-run setup**:
   ```bash
   python setup_ailo.py
   ```
4. **Fresh data download**:
   ```bash
   rm -rf utdanning_data/raw/*
   python main.py
   ```

## 🎓 Example Use Cases

### For Students:
- Exploring career options
- Understanding education requirements
- Comparing different study programs
- Finding apprenticeship opportunities

### For Career Counselors:
- Quick access to updated information
- Consistent advice based on official data
- Supporting students in decision-making
- Providing salary and market insights

### For Parents:
- Understanding Norwegian education system
- Supporting children's career choices
- Learning about different career paths
- Getting objective, data-based information

---

**Happy counseling with AILO! 🤖🎓**
