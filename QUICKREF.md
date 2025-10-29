# 🤖 AILO Quick Reference Card

## 🆕 Version 1.1 - Source Citation Update
**AILO now ONLY uses data from utdanning.no and ALWAYS cites sources!**
- ✅ Fixed: URLs now properly map API endpoints to web pages
- ✅ Added: Both web URL and API source attribution
See `SOURCE_CITATION_GUIDE.md` and `URL_CONSTRUCTION_GUIDE.md` for details.

## Quick Commands

```bash
# 🚀 FIRST TIME SETUP
python setup_ailo.py              # Install everything

# 📥 DOWNLOAD DATA
python main.py                    # Full pipeline (10-30 min)
python main.py --download-only    # Only download

# 💬 START CHATBOT
python start_ailo.py              # Quick start (recommended)
python ailo_chatbot.py            # Direct start

# 🔄 AUTOMATIC UPDATES
python ailo_scheduler.py          # Run at midnight
python ailo_scheduler.py --time 02:30  # Custom time
python ailo_scheduler.py --run-now     # Update now

# 🧪 TEST SOURCE CITATIONS
python test_source_citations.py   # Verify AILO cites sources

# 📊 RUN EVALUATION FRAMEWORK
python run_evaluation.py          # Interactive evaluation
python ailo_evaluation_framework.py --max-questions 30  # Quick test
python ailo_evaluation_framework.py  # Full evaluation (all questions)

# 📊 CHECK STATUS
ls -lh utdanning_data/processed/text_for_llm/
tail -f scheduler_logs/scheduler_*.log
```

## Chat Commands

While in AILO chatbot:
- `exit` or `quit` → Exit chatbot
- `clear` → Clear conversation
- `save` → Save conversation to file

## Configuration File

`ailo_config.json`:
```json
{
  "lm_studio": {
    "url": "http://localhost:1234/v1",
    "model": "gemma-3n-E4B-it-MLX-bf16"
  },
  "chatbot": {
    "max_context_docs": 5,
    "temperature": 0.5,
    "max_tokens": 1500,
    "strict_source_mode": true,
    "require_citations": true
  }
}
```

**⚠️ IMPORTANT:** AILO only uses data from utdanning.no and ALWAYS cites sources!

## Example Questions for AILO

```
✅ "Hvordan bli sykepleier?"
✅ "Hva er forskjellen mellom bachelor og master?"
✅ "Hvor mye tjener en lærer?"
✅ "Lærlingsplasser i Bergen innen bygg og anlegg"
✅ "Sammenlign ingeniør og håndverker"
✅ "Utdanninger innen IT og programmering"
✅ "Hva er opptakskravene for medisin?"
✅ "Jobbmuligheter etter bachelor i økonomi"
```

**Note:** AILO will provide sources like: `(Kilde: https://utdanning.no/...)`

## File Structure

```
ailo-bot-code/
├── ailo_chatbot.py          ← Main chatbot
├── ailo_scheduler.py         ← Auto updates
├── setup_ailo.py            ← Setup script
├── start_ailo.py            ← Quick launcher
├── ailo_config.json         ← Configuration
├── main.py                  ← Data pipeline
├── utdanning_data/          ← Downloaded data
│   ├── raw/                 ← API responses
│   ├── processed/           ← Processed data
│   │   └── text_for_llm/    ← Knowledge base
│   └── logs/                ← Pipeline logs
└── scheduler_logs/          ← Scheduler logs
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ❌ Can't connect to LM Studio | Start LM Studio → Local Server → Start |
| ❌ No data found | Run: `python main.py` |
| ❌ Generic answers without sources | Increase `max_context_docs` in config |
| ❌ Slow responses | Decrease `max_context_docs` or use smaller model |
| ❌ Scheduler not running | Check logs: `cat scheduler_logs/*.log` |
| ❌ Missing source citations | Lower temperature to 0.3-0.5 in config |

**📖 Source Citation:** See `SOURCE_CITATION_GUIDE.md` for details on how AILO cites sources

## System Requirements

- ✅ Python 3.8+
- ✅ LM Studio with Gemma model
- ✅ 5-10 GB disk space for data
- ✅ 8 GB+ RAM (16 GB recommended)
- ✅ macOS/Linux (Windows compatible)

## LM Studio Setup

1. Download LM Studio from lmstudio.ai
2. Search: "gemma-3n-E4B-it-MLX-bf16"
3. Download model
4. Load model
5. Go to "Local Server" tab
6. Click "Start Server"
7. Verify: http://localhost:1234

## Installation Steps

```bash
# 1. Clone/download project
cd ailo-bot-code

# 2. Install dependencies
pip install -r requirements_ailo.txt

# 3. Run setup
python setup_ailo.py

# 4. Download data
python main.py

# 5. Start chatbot
python start_ailo.py
```

## Automatic Updates (macOS)

```bash
# Install launchd service
cp no.ailo.scheduler.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/no.ailo.scheduler.plist

# Check if running
launchctl list | grep ailo
```

## Automatic Updates (Linux)

```bash
# Edit and install systemd service
sudo cp ailo-scheduler.service /etc/systemd/system/
sudo systemctl enable ailo-scheduler
sudo systemctl start ailo-scheduler

# Check status
sudo systemctl status ailo-scheduler
```

## Performance Tips

**Faster responses:**
- Reduce `max_context_docs` to 3
- Use smaller/faster model
- Reduce `max_tokens` to 500

**Better accuracy:**
- Increase `max_context_docs` to 10
- Use larger model
- Increase `max_tokens` to 2000

**Less resource usage:**
- Schedule updates at night
- Use lower `temperature` (0.5)
- Limit conversation history

## Support

📖 Full documentation: `AILO_GUIDE.md`
📋 Detailed README: `AILO_README.md`
💾 Backup conversations regularly
🔄 Update data weekly for best results

---

**AILO - Helping Norwegians navigate education and careers 🎓**
