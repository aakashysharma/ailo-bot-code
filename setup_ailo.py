#!/usr/bin/env python3
"""
AILO System Setup and Configuration
Sets up the complete AILO career counselor system with LM Studio integration
"""

import subprocess
import sys
import json
from pathlib import Path


def check_lm_studio_running():
    """Check if LM Studio server is accessible."""
    try:
        import requests
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        return response.status_code == 200
    except:
        return False


def create_config_file():
    """Create configuration file for AILO."""
    config = {
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
            "enabled": True
        },
        "chatbot": {
            "max_context_docs": 5,
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }
    
    config_path = Path("ailo_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuration file created: {config_path}")
    return config_path


def install_dependencies():
    """Install required Python packages."""
    print("\n📦 Installing dependencies...")
    
    packages = [
        "aiohttp",
        "tqdm",
        "schedule",
        "requests",
        "pyarrow",
        "pandas",
        "numpy"
    ]
    
    for package in packages:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True
            )
            print(f"  ✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {package} - {e}")


def create_systemd_service():
    """Create systemd service file for automatic updates (Linux/macOS)."""
    service_content = """[Unit]
Description=AILO Data Update Scheduler
After=network.target

[Service]
Type=simple
User=%USER%
WorkingDirectory=%WORKING_DIR%
ExecStart=%PYTHON% %WORKING_DIR%/ailo_scheduler.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
"""
    
    working_dir = Path.cwd()
    python_path = sys.executable
    
    service_content = service_content.replace("%USER%", "your_username")
    service_content = service_content.replace("%WORKING_DIR%", str(working_dir))
    service_content = service_content.replace("%PYTHON%", python_path)
    
    service_file = Path("ailo-scheduler.service")
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"\n✅ Systemd service file created: {service_file}")
    print("\nTo install the service (Linux):")
    print(f"  1. Edit {service_file} and replace 'your_username' with your username")
    print(f"  2. sudo cp {service_file} /etc/systemd/system/")
    print("  3. sudo systemctl daemon-reload")
    print("  4. sudo systemctl enable ailo-scheduler")
    print("  5. sudo systemctl start ailo-scheduler")


def create_launchd_plist():
    """Create launchd plist for automatic updates (macOS)."""
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>no.ailo.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>%PYTHON%</string>
        <string>%WORKING_DIR%/ailo_scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>%WORKING_DIR%</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>%WORKING_DIR%/scheduler_logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>%WORKING_DIR%/scheduler_logs/stderr.log</string>
</dict>
</plist>
"""
    
    working_dir = Path.cwd()
    python_path = sys.executable
    
    plist_content = plist_content.replace("%PYTHON%", python_path)
    plist_content = plist_content.replace("%WORKING_DIR%", str(working_dir))
    
    plist_file = Path("no.ailo.scheduler.plist")
    with open(plist_file, 'w') as f:
        f.write(plist_content)
    
    print(f"\n✅ LaunchDaemon plist created: {plist_file}")
    print("\nTo install (macOS):")
    print(f"  1. cp {plist_file} ~/Library/LaunchAgents/")
    print("  2. launchctl load ~/Library/LaunchAgents/no.ailo.scheduler.plist")
    print("  3. launchctl start no.ailo.scheduler")


def create_readme():
    """Create comprehensive README for the AILO system."""
    readme_content = """# 🤖 AILO - AI-powered Learning Oracle

AILO er en AI-drevet karriererådgiver basert på data fra utdanning.no, kjørende lokalt med LM Studio.

## 🚀 Quick Start

### 1. Start LM Studio
1. Åpne LM Studio
2. Last ned modellen: `gemma-3n-E4B-it-MLX-bf16`
3. Start lokal server (Local Server i LM Studio)
4. Bekreft at serveren kjører på `http://localhost:1234`

### 2. Første gangs oppsett
```bash
# Installer avhengigheter
python setup_ailo.py

# Last ned data (første gang)
python main.py

# Start AILO chatbot
python ailo_chatbot.py
```

### 3. Automatiske oppdateringer
```bash
# Start scheduler (oppdaterer data hver natt kl 00:00)
python ailo_scheduler.py

# Eller sett custom tid
python ailo_scheduler.py --time 02:30

# Kjør oppdatering nå
python ailo_scheduler.py --run-now
```

## 📁 Filstruktur

```
ailo-bot-code/
├── ailo_chatbot.py          # Hovedchatbot
├── ailo_scheduler.py         # Automatisk oppdatering
├── setup_ailo.py            # Oppsett script
├── main.py                  # Data pipeline
├── ailo_config.json         # Konfigurasjon
├── utdanning_data/          # Nedlastet data
│   ├── raw/                 # Rå API data
│   ├── processed/           # Prosessert data
│   └── logs/                # Logger
└── scheduler_logs/          # Scheduler logger
```

## 💬 Bruke AILO

### Interaktiv chat
```bash
python ailo_chatbot.py
```

### Eksempel samtale
```
Du: Hei! Jeg vil bli sykepleier. Hva må jeg gjøre?

AILO: Hei! Flott at du vil bli sykepleier! 🏥

For å bli sykepleier i Norge trenger du:

1. **Utdanning:**
   - 3-årig bachelorprogram i sykepleie
   - Tilbys ved universiteter og høyskoler over hele landet
   - Krav: Generell studiekompetanse (videregående)

2. **Opptakskrav:**
   - Karakterer fra videregående
   - Spesifikk karaktergrense varierer mellom skoler
   - Ofte konkurranseutsatt (mange søkere)

3. **Praksis:**
   - Mye praksis i utdanningen
   - Både sykehus og kommunehelsetjeneste

Hvilken type sykepleie interesserer deg mest? 
Eller vil du vite mer om spesifikke skoler?
```

### Kommandoer i chatbot
- `exit` / `quit` - Avslutt
- `clear` - Tøm samtalehistorikk  
- `save` - Lagre samtale til fil

## ⚙️ Konfigurasjon

Rediger `ailo_config.json`:

```json
{
  "lm_studio": {
    "url": "http://localhost:1234/v1",
    "model": "gemma-3n-E4B-it-MLX-bf16"
  },
  "scheduler": {
    "update_time": "00:00",
    "enabled": true
  }
}
```

## 🔄 Data Pipeline

Pipeline består av tre faser:

1. **Download** - Last ned data fra API
2. **Process** - Prosesser og normaliser data
3. **Extract** - Lag vektoriseringsklart datasett

```bash
# Kjør komplett pipeline
python main.py

# Kun nedlasting
python main.py --download-only

# Kun prosessering
python main.py --process-only
```

## 🤖 Systemtjeneste (Automatisk oppstart)

### macOS
```bash
# Installer LaunchAgent
cp no.ailo.scheduler.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/no.ailo.scheduler.plist
```

### Linux
```bash
# Installer systemd service
sudo cp ailo-scheduler.service /etc/systemd/system/
sudo systemctl enable ailo-scheduler
sudo systemctl start ailo-scheduler
```

## 📊 Sjekke status

```bash
# Se scheduler logger
tail -f scheduler_logs/scheduler_*.log

# Se data pipeline logger  
tail -f utdanning_data/logs/pipeline_*.log

# Sjekk siste oppdatering
ls -lt utdanning_data/raw/
```

## 🛠️ Feilsøking

### LM Studio forbindelse feil
```
✅ Sjekk at LM Studio kjører
✅ Sjekk at Local Server er startet
✅ Bekreft URL: http://localhost:1234
✅ Test i nettleser: http://localhost:1234/v1/models
```

### Ingen data i knowledge base
```
✅ Kjør data pipeline: python main.py
✅ Sjekk utdanning_data/processed/text_for_llm/
✅ Se logs i utdanning_data/logs/
```

### Scheduler kjører ikke
```
✅ Test manuelt: python ailo_scheduler.py --run-now
✅ Sjekk scheduler_logs/
✅ Verifiser systemtjeneste status
```

## 📝 Tips

1. **Første samtale**: Start med brede spørsmål, la AILO guide deg
2. **Vær spesifikk**: Jo mer spesifikke spørsmål, jo bedre svar
3. **Følg opp**: Still oppfølgingsspørsmål for dypere innsikt
4. **Lagre viktige samtaler**: Bruk `save` kommando

## 🎯 Hva AILO kan hjelpe med

- ✅ Utdanningsvalg (videregående, høyere utdanning)
- ✅ Karriereveiledning og yrkesvalg
- ✅ Lønn og arbeidsmarkedsinformasjon
- ✅ Lærlingsplasser og godkjente lærebedrifter
- ✅ Sammenligning av utdanninger og yrker
- ✅ Veien fra utdanning til jobb

## 📚 Datakilder

All data kommer fra offisielle norske kilder:
- utdanning.no (Utdanningsdirektoratet)
- Over 150+ API endpoints
- Oppdateres automatisk hver natt

## 🔐 Personvern

- ✅ Kjører 100% lokalt (ingen data sendes ut)
- ✅ Samtaler lagres kun på din maskin
- ✅ Full kontroll over dine data

## 🆘 Support

Ved problemer:
1. Sjekk logs i `scheduler_logs/` og `utdanning_data/logs/`
2. Test LM Studio forbindelse manuelt
3. Kjør data pipeline på nytt
4. Se issue tracker på GitHub

---

**Laget med ❤️ for norske elever og studenter**
"""
    
    readme_file = Path("AILO_README.md")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ README created: {readme_file}")


def main():
    """Main setup function."""
    print("=" * 60)
    print("🤖 AILO System Setup")
    print("   AI-powered Learning Oracle")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print("✅ Python version OK")
    
    # Install dependencies
    install_dependencies()
    
    # Create configuration
    create_config_file()
    
    # Create service files
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        create_launchd_plist()
    elif system == "Linux":
        create_systemd_service()
    
    # Create README
    create_readme()
    
    # Check LM Studio
    print("\n🔍 Checking LM Studio...")
    if check_lm_studio_running():
        print("✅ LM Studio server is running!")
    else:
        print("⚠️  LM Studio server not detected")
        print("   Please start LM Studio and the local server")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start LM Studio with gemma-3n-E4B-it-MLX-bf16 model")
    print("  2. Run data pipeline: python main.py")
    print("  3. Start chatbot: python ailo_chatbot.py")
    print("  4. Enable automatic updates: python ailo_scheduler.py")
    print()
    print("📖 See AILO_README.md for detailed instructions")
    print()


if __name__ == "__main__":
    main()
