# 🤖 AILO - AI-powered Learning Oracle

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
