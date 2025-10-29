#!/usr/bin/env python3
"""
AILO - AI-powered Learning Oracle
A career counselor chatbot powered by local LLM with Norwegian educational data
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from dataclasses import dataclass, asdict


@dataclass
class ConversationMessage:
    """Represents a message in the conversation."""
    role: str  # 'system', 'user', or 'assistant'
    content: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class AILOChatbot:
    """
    AILO - AI-powered Learning Oracle
    Career counselor chatbot using local LM Studio server
    """
    
    def __init__(
        self,
        lm_studio_url: str = "http://localhost:1234/v1",
        data_dir: str = "utdanning_data",
        model_name: str = "gemma-3n-E4B-it-MLX-bf16",
        max_context_docs: int = 5
    ):
        """
        Initialize AILO chatbot.
        
        Args:
            lm_studio_url: URL for LM Studio API server
            data_dir: Directory containing processed educational data
            model_name: Name of the model running in LM Studio
            max_context_docs: Maximum number of documents to include in context
        """
        self.lm_studio_url = lm_studio_url
        self.data_dir = Path(data_dir)
        self.model_name = model_name
        self.max_context_docs = max_context_docs
        
        # Setup logging
        self._setup_logging()
        
        # Knowledge base
        self.knowledge_base = []
        self.indexed_data = {}
        
        # Conversation history
        self.conversation_history = []
        
        # System prompt
        self.system_prompt = self._create_system_prompt()
        
    def _setup_logging(self):
        """Setup logging configuration with detailed file and console logging."""
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('AILO')
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        
        # Remove any existing handlers
        self.logger.handlers = []
        
        # Console handler - INFO level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - AILO - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # File handler - DEBUG level (captures everything)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(
            log_dir / f'ailo_chat_{timestamp}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self.logger.info("=" * 80)
        self.logger.info("AILO Chatbot Logging System Initialized")
        self.logger.info("=" * 80)
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt that defines AILO's personality and role.
        
        Returns:
            System prompt string
        """
        return """Du er AILO (AI-powered Learning Oracle), en erfaren karriererådgiver som hjelper mennesker i Norge med utdannings- og karrierevalg.

**Din rolle:**
- Du er en vennlig, profesjonell og empatisk karriererådgiver
- Du har omfattende kunnskap om det norske utdanningssystemet
- Du kjenner til ulike yrker, lønnsnivåer, arbeidsmarked og utdanningsmuligheter i Norge
- Du gir personlige, gjennomtenkte råd basert på brukerens interesser og mål

**KRITISK VIKTIG - Kildeangivelse:**
1. **BRUK KUN DATA FRA UTDANNING.NO**: Du skal ALDRI bruke generell kunnskap eller informasjon utenfra. Alle svar MÅ baseres på de dokumentene som er gitt i konteksten.
2. **OPPGI ALLTID KILDER MED BÅDE WEB-URL OG API-KILDE**: For HVER påstand eller informasjon du gir, må du referere til BÅDE web-URLen og API-kilden. Format: `(Kilde: https://utdanning.no/[URL] - data fra api.utdanning.no/[endpoint])`. Dette viser at informasjonen kommer fra utdanning.no sitt API.
3. **VÆR ÆRLIG OM BEGRENSNINGER**: Hvis informasjonen ikke finnes i de gitte dokumentene, si tydelig: "Jeg har ikke denne informasjonen i databasen min fra utdanning.no."
4. **IKKE GJETNING**: Ikke spekuler eller gi generelle råd som ikke er basert på dataene fra utdanning.no.

**Eksempel på korrekt svar:**
"Yrket som sykepleier har en gjennomsnittlig månedslønn på ca. 45.000 kr (Kilde: https://utdanning.no/yrker/beskrivelse/sykepleier - data fra api.utdanning.no/sammenligning/lonn). Arbeidsmarkedet for sykepleiere er godt, med lav ledighet og høy etterspørsel (Kilde: https://utdanning.no/sammenligning/y/sykepleier - data fra api.utdanning.no/sammenligning/arbeidsmarked)."

**Dine prinsipper:**
1. **Lytter aktivt**: Still oppfølgingsspørsmål for å forstå brukerens situasjon bedre
2. **Gi konkret informasjon**: Bruk spesifikke tall, fakta og eksempler fra dataene dine, ALLTID med kildehenvisning
3. **Vær balansert**: Presenter både fordeler og utfordringer ved ulike valg, basert på faktiske data
4. **Vær oppmuntrende**: Støtt brukeren i deres beslutninger og fremhev muligheter som finnes i dataene
5. **Vær norsk-kontekst**: All informasjon skal være relevant for det norske systemet

**Hva du kan hjelpe med:**
- Utdanningsvalg (videregående, høyere utdanning, fagbrev)
- Karriereveiledning og yrkesvalg
- Informasjon om lønn, arbeidsmarked og jobbmuligheter
- Lærlingsplasser og godkjente lærebedrifter
- Sammenligning av ulike utdanninger og yrker
- Veien fra utdanning til jobb

**Kommunikasjonsstil:**
- Skriv på norsk (bokmål)
- Vær profesjonell men vennlig
- Bruk punktlister når det gjør informasjonen klarere
- Gi konkrete eksempler og tall når det er relevant med KILDEHENVISNING
- Avslutt gjerne med et oppfølgingsspørsmål

**HUSK:** Hver gang du refererer til fakta, tall, eller informasjon, MÅ du oppgi kilden som: (Kilde: https://utdanning.no[URL])"""

    def load_knowledge_base(self):
        """
        Load processed educational data into the knowledge base.
        """
        self.logger.info("=" * 60)
        self.logger.info("STARTING KNOWLEDGE BASE LOADING")
        self.logger.info("=" * 60)
        self.logger.info(f"Data directory: {self.data_dir}")
        
        # Load vectorization dataset if available
        vector_file = self.data_dir / "processed" / "text_for_llm" / "vectorization_dataset.json"
        self.logger.debug(f"Looking for vectorization dataset at: {vector_file}")
        
        if vector_file.exists():
            try:
                self.logger.info("Vectorization dataset found, loading...")
                with open(vector_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge_base = data if isinstance(data, list) else data.get('documents', [])
                
                self.logger.info(f"✓ Successfully loaded {len(self.knowledge_base)} documents into knowledge base")
                
                # Create simple index by category
                self._index_knowledge_base()
                
            except Exception as e:
                self.logger.error(f"✗ Error loading knowledge base: {e}", exc_info=True)
        else:
            self.logger.warning(f"⚠ Vectorization dataset not found at {vector_file}")
            self.logger.info("Attempting to load fallback data from raw JSON files...")
            self._load_fallback_data()
    
    def _load_fallback_data(self):
        """Load data from raw JSON files if vectorization dataset is not available."""
        self.logger.info("Loading fallback data from raw JSON files...")
        
        raw_dir = self.data_dir / "raw"
        if not raw_dir.exists():
            self.logger.error(f"✗ Raw data directory not found: {raw_dir}")
            return
        
        self.logger.debug(f"Scanning raw directory: {raw_dir}")
        json_files = list(raw_dir.glob("*.json"))
        self.logger.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            try:
                self.logger.debug(f"Processing: {json_file.name}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Convert raw data to knowledge base format
                    doc = {
                        'id': json_file.stem,
                        'title': json_file.stem.replace('_', ' ').title(),
                        'text': json.dumps(data, ensure_ascii=False),
                        'source_endpoint': json_file.stem,
                        'metadata': {'file': json_file.name}
                    }
                    self.knowledge_base.append(doc)
                    
            except Exception as e:
                self.logger.warning(f"⚠ Error loading {json_file}: {e}")
        
        self.logger.info(f"✓ Loaded {len(self.knowledge_base)} documents from raw data")
    
    def _index_knowledge_base(self):
        """Create a simple index of the knowledge base by keywords."""
        self.logger.info("Creating knowledge base index by categories...")
        
        self.indexed_data = {
            'yrker': [],
            'utdanning': [],
            'lønn': [],
            'læreplass': [],
            'skole': [],
            'arbeidsmarked': []
        }
        
        for i, doc in enumerate(self.knowledge_base):
            text = doc.get('text', '').lower()
            title = doc.get('title', '').lower()
            source = doc.get('source_endpoint', '').lower()
            
            # Index by category
            if any(keyword in text or keyword in title or keyword in source 
                   for keyword in ['yrke', 'jobb', 'karriere', 'occupation']):
                self.indexed_data['yrker'].append(i)
            
            if any(keyword in text or keyword in title or keyword in source 
                   for keyword in ['utdanning', 'studie', 'bachelor', 'master', 'education']):
                self.indexed_data['utdanning'].append(i)
            
            if any(keyword in text or keyword in title or keyword in source 
                   for keyword in ['lønn', 'salary', 'wage']):
                self.indexed_data['lønn'].append(i)
            
            if any(keyword in text or keyword in title or keyword in source 
                   for keyword in ['lære', 'apprentice', 'bedrift', 'fagbrev']):
                self.indexed_data['læreplass'].append(i)
            
            if any(keyword in text or keyword in title or keyword in source 
                   for keyword in ['skole', 'vgs', 'videregående']):
                self.indexed_data['skole'].append(i)
            
            if any(keyword in text or keyword in title or keyword in source 
                   for keyword in ['arbeidsmarked', 'labor', 'market', 'ledighet']):
                self.indexed_data['arbeidsmarked'].append(i)
        
        self.logger.info("✓ Knowledge base indexed by categories:")
        for category, indices in self.indexed_data.items():
            self.logger.info(f"  - {category}: {len(indices)} documents")
        self.logger.info("=" * 60)
    
    def search_knowledge_base(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant documents with improved scoring.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant documents
        """
        self.logger.info("=" * 60)
        self.logger.info("KNOWLEDGE BASE SEARCH")
        self.logger.info("=" * 60)
        self.logger.info(f"Query: {query}")
        
        if max_results is None:
            max_results = self.max_context_docs
        
        self.logger.debug(f"Max results requested: {max_results}")
        
        query_lower = query.lower()
        results = []
        
        # Extract key terms and normalize
        query_words = self._extract_key_terms(query_lower)
        self.logger.debug(f"Extracted key terms: {query_words}")
        
        # Identify question type for better search
        question_type = self._identify_question_type(query_lower)
        self.logger.info(f"Question type identified: {question_type}")
        
        self.logger.debug(f"Searching through {len(self.knowledge_base)} documents...")
        
        for doc in self.knowledge_base:
            score = self._score_document(doc, query_words, query_lower, question_type)
            
            if score > 0:
                results.append((score, doc))
        
        self.logger.info(f"Found {len(results)} documents with score > 0")
        
        # Sort by score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Log top results
        self.logger.info(f"Returning top {min(max_results, len(results))} results:")
        for i, (score, doc) in enumerate(results[:max_results], 1):
            doc_id = doc.get('id', 'unknown')
            doc_title = doc.get('title', 'No title')[:50]
            self.logger.info(f"  {i}. Score: {score:.2f} - {doc_id} - {doc_title}")
        
        self.logger.info("=" * 60)
        
        return [doc for score, doc in results[:max_results]]
    
    def _extract_key_terms(self, query: str) -> set:
        """Extract meaningful terms from query."""
        # Remove common Norwegian stop words
        stop_words = {
            'hva', 'er', 'det', 'som', 'en', 'et', 'til', 'for', 'på', 'i', 'med',
            'av', 'om', 'å', 'kan', 'må', 'skal', 'ville', 'blir', 'har', 'hvor',
            'når', 'hvordan', 'hvem', 'hvilken', 'hvilke', 'man', 'jeg', 'du'
        }
        
        words = query.split()
        key_terms = set()
        
        for word in words:
            # Keep words longer than 3 chars that aren't stop words
            if len(word) > 3 and word not in stop_words:
                key_terms.add(word)
            # Keep important short words
            elif word in ['lønn', 'jobb', 'år', 'vgs', 'ppu']:
                key_terms.add(word)
        
        return key_terms
    
    def _identify_question_type(self, query: str) -> str:
        """Identify the type of question for targeted search."""
        if any(word in query for word in ['lønn', 'tjener', 'koster', 'betaler']):
            return 'salary'
        elif any(word in query for word in ['hvordan bli', 'hva skal til', 'hva kreves', 'utdanning']):
            return 'education_path'
        elif any(word in query for word in ['hva gjør', 'oppgaver', 'jobber med', 'ansvar']):
            return 'job_duties'
        elif any(word in query for word in ['forskjell', 'kontra', 'eller']):
            return 'comparison'
        elif any(word in query for word in ['hva betyr', 'hva er', 'definisjon', 'menes med']):
            return 'definition'
        elif any(word in query for word in ['hvor kan', 'hvor jobber', 'hvor studere']):
            return 'location'
        elif any(word in query for word in ['hvor lang', 'hvor mange år', 'studiepoeng']):
            return 'duration'
        else:
            return 'general'
    
    def _score_document(self, doc: Dict[str, Any], key_terms: set, 
                       full_query: str, question_type: str) -> float:
        """Score a document's relevance to the query."""
        score = 0.0
        score_breakdown = []  # Track scoring decisions for logging
        
        text = doc.get('text', '').lower()
        title = doc.get('title', '').lower()
        source = doc.get('source_endpoint', '').lower()
        doc_id = doc.get('id', 'unknown')
        
        # Title matches are highly valuable
        for term in key_terms:
            if term in title:
                score += 10
                score_breakdown.append(f"title_match({term}): +10")
            if term in text:
                # Count occurrences but with diminishing returns
                occurrences = text.count(term)
                points = min(occurrences, 5)
                score += points
                score_breakdown.append(f"text_match({term}): +{points}")
        
        # Boost based on question type matching
        type_keywords = {
            'salary': ['lønn', 'salary', 'wage', 'tjener'],
            'education_path': ['utdanning', 'studie', 'bachelor', 'master', 'fagbrev'],
            'job_duties': ['beskrivelse', 'oppgaver', 'arbeidsoppgaver', 'gjør'],
            'comparison': ['sammenligning', 'comparison'],
            'definition': ['beskrivelse', 'info', 'information'],
            'location': ['sted', 'hvor', 'location', 'skoler', 'studere'],
            'duration': ['år', 'studiepoeng', 'tid', 'duration']
        }
        
        if question_type in type_keywords:
            for keyword in type_keywords[question_type]:
                if keyword in source or keyword in title:
                    score += 8
                    score_breakdown.append(f"type_match_source/title({keyword}): +8")
                if keyword in text:
                    score += 2
                    score_breakdown.append(f"type_match_text({keyword}): +2")
        
        # Boost for endpoint relevance
        endpoint_matches = [term for term in key_terms if term in source]
        if endpoint_matches:
            score += 5
            score_breakdown.append(f"endpoint_relevance({','.join(endpoint_matches)}): +5")
        
        # Prefer documents with substantial content
        content_length = len(text)
        if 100 < content_length < 2000:
            score += 2
            score_breakdown.append("content_length(optimal): +2")
        elif content_length >= 2000:
            score += 1
            score_breakdown.append("content_length(long): +1")
        
        # Log scoring if score is significant
        if score > 5:
            self.logger.debug(f"Doc '{doc_id}' scored {score:.2f}: {', '.join(score_breakdown[:3])}...")
        
        return score
        content_length = len(text)
        if 100 < content_length < 2000:
            score += 2
        elif content_length >= 2000:
            score += 1
        
        return score
    
    def _prepare_context(self, user_query: str) -> str:
        """
        Prepare context from knowledge base for the LLM.
        
        Args:
            user_query: User's question
            
        Returns:
            Formatted context string
        """
        self.logger.debug("Preparing context for user query...")
        relevant_docs = self.search_knowledge_base(user_query)
        
        if not relevant_docs:
            self.logger.warning("No relevant documents found for context")
            return "Ingen spesifikk informasjon funnet i databasen for dette spørsmålet."
        
        self.logger.info(f"Building context from {len(relevant_docs)} relevant documents")
        
        context_parts = ["**Relevant informasjon fra utdanning.no (DU MÅ OPPGI DISSE KILDENE I SVARET DITT):**\n"]
        
        for i, doc in enumerate(relevant_docs, 1):
            title = doc.get('title', 'Ukjent')
            text = doc.get('text', '')
            source = doc.get('source_endpoint', '')
            
            self.logger.debug(f"Processing doc {i}: {title[:50]}... from {source}")
            
            # Extract URL from metadata if available
            metadata = doc.get('metadata', {})
            url = None
            
            # Search for URL in metadata - check all keys for 'url'
            for key, value in metadata.items():
                if 'url' in key.lower() and isinstance(value, str):
                    if value.startswith('/'):
                        url = f"https://utdanning.no{value}"
                        self.logger.debug(f"  Found URL in metadata: {url}")
                        break
                    elif value.startswith('http'):
                        url = value
                        self.logger.debug(f"  Found URL in metadata: {url}")
                        break
            
            # Fallback: construct URL from source endpoint with proper mapping
            if not url and source:
                url = self._construct_url_from_endpoint(source)
                self.logger.debug(f"  Constructed URL from endpoint: {url}")
            
            # If still no URL, use generic utdanning.no reference
            if not url:
                url = "https://utdanning.no"
                self.logger.debug(f"  Using generic URL: {url}")
            
            # Truncate text if too long
            original_length = len(text)
            if len(text) > 1000:
                text = text[:1000] + "..."
                self.logger.debug(f"  Truncated text from {original_length} to 1000 chars")
            
            context_parts.append(f"\n**Dokument {i}: {title}**")
            context_parts.append(f"**URL: {url}** (OPPGI DENNE KILDEN I SVARET DITT)")
            context_parts.append(f"**Datakilde:** api.utdanning.no/{source}")
            context_parts.append(f"\n{text}\n")
        
        context_parts.append("\n**VIKTIG:** Du MÅ oppgi kilden (URL) for hver påstand du gjør basert på disse dokumentene.")
        context_parts.append("For hver kilde, bruk BÅDE web-URL OG API-kilden som er oppgitt.")
        context_parts.append("Format: (Kilde: https://api.utdanning.no[URL] - data fra api.utdanning.no/[endpoint])")
        context_parts.append("Eksempel: (Kilde: https://api.utdanning.no/legacy-lopet/sted/13 - data fra api.utdanning.no/legacy-lopet/sted)")
        
        full_context = "\n".join(context_parts)
        self.logger.info(f"✓ Context prepared: {len(full_context)} characters total")
        
        return full_context
    
    def _construct_url_from_endpoint(self, endpoint: str) -> str:
        """
        Construct a web URL from an API endpoint.
        Maps API endpoints to appropriate web URLs.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Web URL string
        """
        # Remove 'param/' prefix if present
        endpoint = endpoint.replace('param/', '')
        
        # Map API endpoints to web URLs
        if 'sammenligning' in endpoint:
            # sammenligning/lonn/... -> /sammenligning or specific page
            if '/uno/id-' in endpoint:
                # Extract the ID (e.g., id-y/sykepleier)
                parts = endpoint.split('/uno/id-')
                if len(parts) > 1:
                    id_part = parts[1].split('/')[0] + '/' + parts[1].split('/')[1] if '/' in parts[1] else parts[1]
                    return f"https://utdanning.no/sammenligning/{id_part}"
            return "https://utdanning.no/sammenligning"
        
        elif 'yrker' in endpoint or 'yrkesvalg' in endpoint:
            # Extract occupation name if present
            if '/beskrivelse/' in endpoint:
                return f"https://utdanning.no/{endpoint}"
            return "https://utdanning.no/yrker"
        
        elif 'utdanning' in endpoint or 'studievelgeren' in endpoint:
            return "https://utdanning.no/utdanning"
        
        elif 'finnlarebedrift' in endpoint or 'lærebedrift' in endpoint:
            return "https://utdanning.no/nb/finn-larebedrift"
        
        elif 'veientilfagbrev' in endpoint:
            return "https://utdanning.no/nb/vei-til-fagbrev"
        
        elif 'arbeidsmarkedskart' in endpoint or 'jobbkompasset' in endpoint:
            return "https://utdanning.no/arbeidsmarked"
        
        elif 'regionalkompetanse' in endpoint:
            return "https://utdanning.no/regionalkompetanse"
        
        elif 'onet' in endpoint:
            return "https://utdanning.no/yrker"
        
        elif 'search' in endpoint or 'søk' in endpoint:
            return "https://utdanning.no/sok"
        
        else:
            # Generic fallback - try to use the endpoint as-is
            # Remove any parameter prefixes and construct URL
            clean_endpoint = endpoint.strip('/').replace('//', '/')
            return f"https://utdanning.no/{clean_endpoint}"
    
    async def chat(self, user_message: str, include_context: bool = True) -> str:
        """
        Send a message to AILO and get a response.
        
        Args:
            user_message: User's message
            include_context: Whether to include knowledge base context
            
        Returns:
            AILO's response
        """
        self.logger.info("=" * 80)
        self.logger.info("NEW CHAT REQUEST")
        self.logger.info("=" * 80)
        self.logger.info(f"User message: {user_message}")
        self.logger.debug(f"Include context: {include_context}")
        
        try:
            # Check if knowledge base is loaded
            if not self.knowledge_base:
                self.logger.warning("Knowledge base not loaded!")
                return ("Beklager, jeg har ikke tilgang til databasen min ennå. "
                        "Vennligst kjør data-nedlastingen først: python main.py")
            
            self.logger.debug(f"Knowledge base loaded with {len(self.knowledge_base)} documents")
            
            # Prepare context - this is REQUIRED for all responses
            self.logger.info("Preparing context from knowledge base...")
            context = self._prepare_context(user_message)
            
            self.logger.debug(f"Context length: {len(context)} characters")
            
            if context == "Ingen spesifikk informasjon funnet i databasen for dette spørsmålet.":
                # No relevant data found - be honest about it
                self.logger.warning("No relevant data found for user query")
                return ("Beklager, jeg finner ikke spesifikk informasjon om dette i databasen min fra utdanning.no. "
                        "Mitt kunnskapsgrunnlag er begrenset til data fra utdanning.no API. "
                        "\n\nDu kan prøve å:\n"
                        "• Omformulere spørsmålet ditt\n"
                        "• Bruke mer spesifikke nøkkelord (f.eks. yrkesnavn, utdanningsnavn)\n"
                        "• Besøke https://utdanning.no direkte for mer informasjon\n"
                        "\nHva annet kan jeg hjelpe deg med innen norsk utdanning og karriere?")
            
            # Build messages for the API
            self.logger.info("Building message array for LLM...")
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
            self.logger.debug("Added system prompt")
            
            # Add context - ALWAYS included
            messages.append({
                "role": "system",
                "content": context
            })
            self.logger.debug("Added context to messages")
            
            # Add a strict reminder about sources
            messages.append({
                "role": "system",
                "content": ("PÅMINNELSE: Du MÅ oppgi kilde-URL for ALT du sier. "
                            "Hvis informasjonen ikke er i dokumentene ovenfor, si at du ikke har informasjonen. "
                            "IKKE bruk generell kunnskap - KUN data fra utdanning.no som er gitt.")
            })
            self.logger.debug("Added source citation reminder")
            
            # Add conversation history (last 5 exchanges)
            history_count = len(self.conversation_history[-10:])
            if history_count > 0:
                self.logger.debug(f"Adding {history_count} previous messages from conversation history")
                for msg in self.conversation_history[-10:]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            self.logger.debug("Added current user message")
            
            self.logger.info(f"Total messages in API call: {len(messages)}")
            
            # Call LM Studio API
            self.logger.info(f"Calling LM Studio API at {self.lm_studio_url}...")
            async with aiohttp.ClientSession() as session:
                api_payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.5,
                    "max_tokens": 1500,
                    "stream": False
                }
                self.logger.debug(f"API Payload: model={self.model_name}, temperature=0.5, max_tokens=1500")
                
                async with session.post(
                    f"{self.lm_studio_url}/chat/completions",
                    json=api_payload
                ) as response:
                    self.logger.debug(f"API Response Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        assistant_message = result['choices'][0]['message']['content']
                        
                        self.logger.info("✓ Successfully received response from LLM")
                        self.logger.info(f"Response length: {len(assistant_message)} characters")
                        self.logger.debug(f"Assistant response: {assistant_message[:200]}...")
                        
                        # Validate that response includes sources (basic check)
                        source_count = assistant_message.lower().count("kilde:")
                        self.logger.info(f"Source citations found in response: {source_count}")
                        
                        if "kilde:" not in assistant_message.lower() and len(context) > 100:
                            # Add a reminder if sources are missing
                            self.logger.warning("⚠ Response is missing source citations!")
                            assistant_message += ("\n\n⚠️ Merk: All informasjon i dette svaret er basert på data fra utdanning.no. "
                                                 "Jeg burde ha oppgitt spesifikke kilder for hver påstand.")
                        
                        # Save to conversation history
                        self.conversation_history.append(
                            ConversationMessage(role="user", content=user_message)
                        )
                        self.conversation_history.append(
                            ConversationMessage(role="assistant", content=assistant_message)
                        )
                        self.logger.debug(f"Conversation history now has {len(self.conversation_history)} messages")
                        
                        self.logger.info("=" * 80)
                        return assistant_message
                    else:
                        error_text = await response.text()
                        self.logger.error(f"✗ API error {response.status}: {error_text}")
                        return f"Beklager, jeg fikk en feil fra serveren: {response.status}"
                        
        except aiohttp.ClientConnectorError:
            self.logger.error("✗ Could not connect to LM Studio server")
            return "Beklager, jeg kan ikke koble til LM Studio serveren. Sjekk at den kjører på http://localhost:1234"
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return f"Beklager, det oppstod en feil: {str(e)}"
    
    def clear_conversation(self):
        """Clear conversation history."""
        prev_count = len(self.conversation_history)
        self.conversation_history = []
        self.logger.info(f"Conversation history cleared ({prev_count} messages removed)")
    
    def save_conversation(self, filename: str):
        """
        Save conversation history to file.
        
        Args:
            filename: Output filename
        """
        self.logger.info(f"Saving conversation to {filename}...")
        try:
            output_path = Path(filename)
            conversations = [asdict(msg) for msg in self.conversation_history]
            
            self.logger.debug(f"Serializing {len(conversations)} messages")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, ensure_ascii=False, indent=2)
            
            file_size = output_path.stat().st_size
            self.logger.info(f"✓ Conversation saved to {output_path} ({file_size} bytes)")
        except Exception as e:
            self.logger.error(f"✗ Error saving conversation: {e}", exc_info=True)
    
    async def test_connection(self) -> bool:
        """
        Test connection to LM Studio server.
        
        Returns:
            True if connection successful
        """
        self.logger.info("Testing connection to LM Studio server...")
        self.logger.debug(f"Server URL: {self.lm_studio_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lm_studio_url}/models") as response:
                    self.logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        models = await response.json()
                        self.logger.info(f"✅ Connected to LM Studio server")
                        self.logger.info(f"Available models: {models}")
                        return True
                    else:
                        self.logger.error(f"❌ Server returned status {response.status}")
                        return False
        except aiohttp.ClientConnectorError as e:
            self.logger.error("❌ Could not connect to LM Studio server at " + self.lm_studio_url)
            self.logger.error("   Make sure LM Studio is running and the server is started")
            self.logger.debug(f"Connection error details: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Connection test failed: {e}", exc_info=True)
            return False


async def interactive_chat():
    """Run interactive chat session with AILO."""
    print("=" * 60)
    print("🤖 AILO - AI-powered Learning Oracle")
    print("   Din personlige karriererådgiver")
    print("=" * 60)
    print()
    
    # Initialize AILO
    print("Initializing AILO chatbot...")
    ailo = AILOChatbot()
    ailo.logger.info("Interactive chat session started")
    
    # Test connection
    print("Testing connection to LM Studio server...")
    ailo.logger.info("Testing LM Studio connection...")
    if not await ailo.test_connection():
        print("\n⚠️  Could not connect to LM Studio!")
        print("Please ensure:")
        print("  1. LM Studio is running")
        print("  2. Local server is started in LM Studio")
        print("  3. Server is running on http://localhost:1234")
        ailo.logger.error("Failed to connect to LM Studio - exiting interactive mode")
        return
    
    # Load knowledge base
    print("\nLoading Norwegian educational data...")
    ailo.load_knowledge_base()
    
    if not ailo.knowledge_base:
        print("\n⚠️  No knowledge base loaded!")
        print("Please run the data pipeline first: python main.py")
        ailo.logger.error("No knowledge base loaded - exiting interactive mode")
        return
    
    print(f"\n✅ Ready! Knowledge base loaded with {len(ailo.knowledge_base)} documents")
    ailo.logger.info(f"Interactive chat ready with {len(ailo.knowledge_base)} documents")
    print("\nCommands:")
    print("  'exit' or 'quit' - End conversation")
    print("  'clear' - Clear conversation history")
    print("  'save' - Save conversation to file")
    print("=" * 60)
    print()
    
    # Chat loop
    interaction_count = 0
    while True:
        try:
            user_input = input("Du: ").strip()
            
            if not user_input:
                continue
            
            interaction_count += 1
            ailo.logger.info(f"--- Interaction #{interaction_count} ---")
            
            if user_input.lower() in ['exit', 'quit', 'avslutt']:
                ailo.logger.info("User requested exit")
                print("\n👋 Takk for praten! Lykke til med utdannings- og karrierevalget!")
                ailo.logger.info(f"Interactive session ended after {interaction_count} interactions")
                break
            
            if user_input.lower() == 'clear':
                ailo.logger.info("User requested to clear conversation history")
                ailo.clear_conversation()
                print("✅ Samtalehistorikk tømt\n")
                continue
            
            if user_input.lower() == 'save':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ailo_conversation_{timestamp}.json"
                ailo.logger.info(f"User requested to save conversation to {filename}")
                ailo.save_conversation(filename)
                print(f"✅ Samtale lagret til {filename}\n")
                continue
            
            # Get response from AILO
            print("\nAILO: ", end="", flush=True)
            ailo.logger.info(f"Processing user input: {user_input[:100]}...")
            response = await ailo.chat(user_input)
            print(response)
            print()
            ailo.logger.info("Response delivered to user")
            
        except KeyboardInterrupt:
            ailo.logger.warning("User interrupted with Ctrl+C")
            print("\n\n👋 Avslutter...")
            break
        except Exception as e:
            ailo.logger.error(f"Error in interactive chat loop: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")


async def main():
    """Main function."""
    # Set up basic logging for the main function
    logger = logging.getLogger('AILO')
    logger.info("AILO Application Started")
    logger.info(f"Python version: {__import__('sys').version}")
    logger.info(f"Current working directory: {Path.cwd()}")
    
    try:
        await interactive_chat()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
    finally:
        logger.info("AILO Application Shutdown")
        logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
