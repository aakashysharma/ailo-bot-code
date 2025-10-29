#!/usr/bin/env python3
"""
AILO Evaluation Framework
Comprehensive testing framework to evaluate AILO's ability to answer real user questions
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ailo_chatbot import AILOChatbot


@dataclass
class QuestionEvaluation:
    """Evaluation result for a single question."""
    question: str
    response: str
    has_source: bool
    has_relevant_content: bool
    response_length: int
    is_honest_about_limitation: bool
    contains_data: bool
    score: float
    category: str
    keywords_found: List[str]
    processing_time: float
    

class AILOEvaluationFramework:
    """
    Comprehensive evaluation framework for AILO chatbot.
    Tests real user questions and provides detailed scoring.
    """
    
    def __init__(self, questions_file: str = "questions.txt"):
        """
        Initialize the evaluation framework.
        
        Args:
            questions_file: Path to file containing test questions
        """
        self.questions_file = Path(questions_file)
        self.ailo = None
        self.evaluations: List[QuestionEvaluation] = []
        
        # Question categories and keywords
        self.categories = {
            "job_duties": ["hva gjør", "hva jobber", "hvem samarbeider", "hva kan man gjøre", "oppgaver"],
            "salary": ["hvor mye tjener", "hva tjener", "lønn", "koster", "betaler"],
            "education_path": ["hvordan bli", "hvordan får man", "hva skal til", "hva må til", 
                              "hva kreves", "hvilken utdanning", "hvordan utdanne", "hvor lang tid"],
            "requirements": ["hvor mange poeng", "hva er snittet", "opptakskrav", "må man ha"],
            "comparison": ["forskjellen på", "forskjell mellom", "eller", "kontra"],
            "definition": ["hva betyr", "hva er", "hva menes med", "definisjon"],
            "job_locations": ["hvor jobber", "hvor kan man jobbe", "hvor kan jeg jobbe"],
            "study_locations": ["hvor kan jeg studere", "hvilke skoler", "hvor studere"],
            "career_options": ["hva kan man bli", "hva kan jeg bli", "jobbmuligheter"],
            "study_duration": ["hvor lenge", "hvor mange år", "hvor mange studiepoeng"],
            "work_conditions": ["hvordan er det å", "hvordan jobber", "hvor mye jobber"],
            "authorization": ["hvem kan kalle seg", "når kan man kalle", "beskyttet tittel", "er det vanskelig"],
        }
        
        # Keywords that indicate relevant Norwegian education content
        self.relevance_keywords = [
            "utdanning", "studere", "skole", "fagbrev", "læreplass", "bachelor", "master",
            "yrke", "jobb", "karriere", "lønn", "kr", "arbeidsmarked", "kompetanse",
            "opptakskrav", "poeng", "snitt", "videregående", "vgs", "universitet",
            "høyskole", "år", "studiepoeng", "sertifikat", "autorisasjon", "norge"
        ]
    
    async def initialize(self) -> bool:
        """Initialize AILO and check prerequisites."""
        print("🚀 Initializing AILO Evaluation Framework...")
        print("=" * 70)
        
        # Initialize AILO
        self.ailo = AILOChatbot()
        
        # Test connection
        print("Testing LM Studio connection...")
        if not await self.ailo.test_connection():
            print("❌ FAILED: Could not connect to LM Studio")
            return False
        print("✅ LM Studio connected\n")
        
        # Load knowledge base
        print("Loading knowledge base...")
        self.ailo.load_knowledge_base()
        
        if not self.ailo.knowledge_base:
            print("❌ FAILED: No knowledge base loaded")
            print("   Please run: python main.py")
            return False
        
        print(f"✅ Knowledge base loaded: {len(self.ailo.knowledge_base)} documents\n")
        
        return True
    
    def load_questions(self) -> List[str]:
        """Load questions from file."""
        print(f"Loading questions from {self.questions_file}...")
        
        with open(self.questions_file, 'r', encoding='utf-8') as f:
            questions = [line.strip() for line in f if line.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_questions = []
        for q in questions:
            q_clean = q.strip('"').strip()
            if q_clean and q_clean not in seen:
                seen.add(q_clean)
                unique_questions.append(q_clean)
        
        print(f"✅ Loaded {len(unique_questions)} unique questions\n")
        return unique_questions
    
    def categorize_question(self, question: str) -> str:
        """Determine the category of a question."""
        question_lower = question.lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in question_lower for keyword in keywords):
                return category
        
        return "general"
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.relevance_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    async def evaluate_question(self, question: str) -> QuestionEvaluation:
        """
        Evaluate AILO's response to a single question.
        
        Args:
            question: The question to ask
            
        Returns:
            QuestionEvaluation object with detailed results
        """
        start_time = asyncio.get_event_loop().time()
        
        # Get response from AILO
        response = await self.ailo.chat(question)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        # Analyze response
        response_lower = response.lower()
        
        # Check for source citations
        has_source = bool(re.search(r'kilde:', response_lower) or 
                         re.search(r'https://utdanning\.no', response_lower))
        
        # Check for honest limitation admission
        is_honest = any(phrase in response_lower for phrase in [
            "finner ikke", "har ikke", "informasjon", "databasen", 
            "begrenset til", "ikke spesifikk"
        ]) and not has_source
        
        # Check for relevant content
        keywords_found = self.extract_keywords(response)
        has_relevant_content = len(keywords_found) > 0 or has_source
        
        # Check if response contains actual data (numbers, specific facts)
        contains_data = bool(
            re.search(r'\d+', response) or  # Numbers
            re.search(r'bachelor|master|fagbrev|år|studiepoeng', response_lower) or
            has_source
        )
        
        # Calculate score
        score = self._calculate_score(
            has_source=has_source,
            has_relevant_content=has_relevant_content,
            is_honest=is_honest,
            contains_data=contains_data,
            response_length=len(response),
            keywords_count=len(keywords_found)
        )
        
        # Categorize question
        category = self.categorize_question(question)
        
        return QuestionEvaluation(
            question=question,
            response=response,
            has_source=has_source,
            has_relevant_content=has_relevant_content,
            response_length=len(response),
            is_honest_about_limitation=is_honest,
            contains_data=contains_data,
            score=score,
            category=category,
            keywords_found=keywords_found,
            processing_time=processing_time
        )
    
    def _calculate_score(
        self,
        has_source: bool,
        has_relevant_content: bool,
        is_honest: bool,
        contains_data: bool,
        response_length: int,
        keywords_count: int
    ) -> float:
        """
        Calculate a score for the response (0-100).
        
        Scoring criteria:
        - Has source citation: 40 points
        - Has relevant content: 20 points
        - Contains specific data: 20 points
        - Appropriate response length: 10 points
        - Multiple relevant keywords: 10 points
        - OR honest about limitation: 30 points (alternative path)
        """
        score = 0.0
        
        if has_source:
            # Best case: Response with sources
            score += 40
            if has_relevant_content:
                score += 20
            if contains_data:
                score += 20
            if 200 <= response_length <= 2000:
                score += 10
            if keywords_count >= 3:
                score += 10
        elif is_honest:
            # Good case: Honest about not having data
            score += 30
            if response_length >= 100:  # Gave helpful response
                score += 20
            if "omformulere" in self.ailo.conversation_history[-1].content.lower():
                score += 10  # Suggested alternatives
        else:
            # Poor case: No source and not honest
            if has_relevant_content:
                score += 10
            if contains_data:
                score += 10
            # Penalty for generic response without sources
        
        return min(score, 100.0)
    
    async def run_evaluation(
        self,
        max_questions: Optional[int] = None,
        sample_categories: bool = True
    ) -> Dict[str, Any]:
        """
        Run the full evaluation.
        
        Args:
            max_questions: Maximum number of questions to test (None = all)
            sample_categories: If True, sample evenly from categories
            
        Returns:
            Evaluation results dictionary
        """
        questions = self.load_questions()
        
        if max_questions and max_questions < len(questions):
            if sample_categories:
                # Sample from each category
                questions = self._sample_by_category(questions, max_questions)
            else:
                questions = questions[:max_questions]
        
        print(f"🧪 Running evaluation on {len(questions)} questions...")
        print("=" * 70)
        print()
        
        for i, question in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] Testing: {question[:60]}...")
            
            try:
                evaluation = await self.evaluate_question(question)
                self.evaluations.append(evaluation)
                
                # Show quick result
                status = "✅" if evaluation.score >= 70 else "⚠️" if evaluation.score >= 40 else "❌"
                print(f"    {status} Score: {evaluation.score:.1f}/100 | "
                      f"Source: {evaluation.has_source} | "
                      f"Time: {evaluation.processing_time:.1f}s")
                print()
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                print()
        
        # Generate report
        return self._generate_report()
    
    def _sample_by_category(self, questions: List[str], target_count: int) -> List[str]:
        """Sample questions evenly from different categories."""
        from collections import defaultdict
        import random
        
        categorized = defaultdict(list)
        for q in questions:
            cat = self.categorize_question(q)
            categorized[cat].append(q)
        
        # Sample evenly
        per_category = max(1, target_count // len(categorized))
        sampled = []
        
        for category, cat_questions in categorized.items():
            sample_size = min(per_category, len(cat_questions))
            sampled.extend(random.sample(cat_questions, sample_size))
        
        # Fill remaining slots randomly
        if len(sampled) < target_count:
            remaining = [q for q in questions if q not in sampled]
            additional = min(target_count - len(sampled), len(remaining))
            sampled.extend(random.sample(remaining, additional))
        
        return sampled[:target_count]
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        if not self.evaluations:
            return {"error": "No evaluations to report"}
        
        total = len(self.evaluations)
        
        # Calculate statistics
        total_score = sum(e.score for e in self.evaluations)
        avg_score = total_score / total
        
        with_sources = sum(1 for e in self.evaluations if e.has_source)
        honest_responses = sum(1 for e in self.evaluations if e.is_honest_about_limitation)
        with_data = sum(1 for e in self.evaluations if e.contains_data)
        
        # Score distribution
        excellent = sum(1 for e in self.evaluations if e.score >= 80)
        good = sum(1 for e in self.evaluations if 60 <= e.score < 80)
        fair = sum(1 for e in self.evaluations if 40 <= e.score < 60)
        poor = sum(1 for e in self.evaluations if e.score < 40)
        
        # Category breakdown
        category_stats = {}
        from collections import defaultdict
        cat_scores = defaultdict(list)
        
        for e in self.evaluations:
            cat_scores[e.category].append(e.score)
        
        for category, scores in cat_scores.items():
            category_stats[category] = {
                "count": len(scores),
                "avg_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores)
            }
        
        # Performance metrics
        avg_processing_time = sum(e.processing_time for e in self.evaluations) / total
        
        # Best and worst responses
        best = max(self.evaluations, key=lambda e: e.score)
        worst = min(self.evaluations, key=lambda e: e.score)
        
        report = {
            "summary": {
                "total_questions": total,
                "average_score": round(avg_score, 2),
                "source_citation_rate": round(with_sources / total * 100, 1),
                "honest_limitation_rate": round(honest_responses / total * 100, 1),
                "data_containing_rate": round(with_data / total * 100, 1),
                "avg_processing_time": round(avg_processing_time, 2)
            },
            "score_distribution": {
                "excellent (80-100)": excellent,
                "good (60-79)": good,
                "fair (40-59)": fair,
                "poor (0-39)": poor
            },
            "category_performance": category_stats,
            "best_response": {
                "question": best.question,
                "score": best.score,
                "has_source": best.has_source
            },
            "worst_response": {
                "question": worst.question,
                "score": worst.score,
                "has_source": worst.has_source,
                "response_preview": worst.response[:200] + "..."
            },
            "recommendations": self._generate_recommendations(avg_score, with_sources, total)
        }
        
        return report
    
    def _generate_recommendations(self, avg_score: float, with_sources: int, total: int) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        source_rate = with_sources / total * 100
        
        if avg_score < 60:
            recommendations.append("⚠️  Overall score is low. Consider increasing max_context_docs to 8-10")
            recommendations.append("⚠️  Lower temperature to 0.3 for more factual responses")
        
        if source_rate < 50:
            recommendations.append("📚 Less than 50% of responses include sources")
            recommendations.append("   → Try a different LLM model in LM Studio")
            recommendations.append("   → Increase max_tokens to 2000 for longer responses with citations")
        elif source_rate < 70:
            recommendations.append("📚 Source citation rate could be improved")
            recommendations.append("   → Consider lowering temperature to 0.3-0.4")
        
        if avg_score >= 80:
            recommendations.append("✅ Excellent performance! AILO is working well")
        elif avg_score >= 60:
            recommendations.append("✅ Good performance with room for improvement")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save evaluation report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ailo_evaluation_report_{timestamp}.json"
        
        # Save full report
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Save detailed evaluations
        detail_file = filename.replace('.json', '_detailed.json')
        with open(detail_file, 'w', encoding='utf-8') as f:
            evaluations_dict = [asdict(e) for e in self.evaluations]
            json.dump(evaluations_dict, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Report saved to: {filename}")
        print(f"📋 Detailed results saved to: {detail_file}")
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted report to console."""
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 20 + "AILO EVALUATION REPORT" + " " * 25 + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        
        # Summary
        print("📊 SUMMARY")
        print("=" * 70)
        summary = report['summary']
        print(f"  Total Questions Tested: {summary['total_questions']}")
        print(f"  Average Score: {summary['average_score']}/100")
        print(f"  Source Citation Rate: {summary['source_citation_rate']}%")
        print(f"  Honest Limitation Rate: {summary['honest_limitation_rate']}%")
        print(f"  Data-Containing Responses: {summary['data_containing_rate']}%")
        print(f"  Average Processing Time: {summary['avg_processing_time']}s")
        print()
        
        # Score Distribution
        print("📈 SCORE DISTRIBUTION")
        print("=" * 70)
        dist = report['score_distribution']
        total = summary['total_questions']
        print(f"  Excellent (80-100): {dist['excellent (80-100)']} ({dist['excellent (80-100)']/total*100:.1f}%)")
        print(f"  Good      (60-79):  {dist['good (60-79)']} ({dist['good (60-79)']/total*100:.1f}%)")
        print(f"  Fair      (40-59):  {dist['fair (40-59)']} ({dist['fair (40-59)']/total*100:.1f}%)")
        print(f"  Poor      (0-39):   {dist['poor (0-39)']} ({dist['poor (0-39)']/total*100:.1f}%)")
        print()
        
        # Category Performance
        print("📁 CATEGORY PERFORMANCE")
        print("=" * 70)
        for category, stats in sorted(report['category_performance'].items(), 
                                      key=lambda x: x[1]['avg_score'], reverse=True):
            print(f"  {category:25s} | Avg: {stats['avg_score']:5.1f} | "
                  f"Count: {stats['count']:3d} | Range: {stats['min_score']:.0f}-{stats['max_score']:.0f}")
        print()
        
        # Best/Worst
        print("🏆 BEST RESPONSE")
        print("=" * 70)
        best = report['best_response']
        print(f"  Question: {best['question']}")
        print(f"  Score: {best['score']:.1f}/100")
        print(f"  Has Source: {best['has_source']}")
        print()
        
        print("⚠️  WORST RESPONSE")
        print("=" * 70)
        worst = report['worst_response']
        print(f"  Question: {worst['question']}")
        print(f"  Score: {worst['score']:.1f}/100")
        print(f"  Preview: {worst['response_preview']}")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("=" * 70)
        for rec in report['recommendations']:
            print(f"  {rec}")
        print()
        print("=" * 70)


async def main():
    """Main function to run evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AILO Evaluation Framework")
    parser.add_argument("--max-questions", type=int, default=None,
                       help="Maximum number of questions to test (default: all)")
    parser.add_argument("--sample-categories", action="store_true",
                       help="Sample evenly from categories")
    parser.add_argument("--output", type=str, default=None,
                       help="Output filename for report")
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = AILOEvaluationFramework()
    
    if not await framework.initialize():
        print("❌ Failed to initialize. Please check prerequisites.")
        return
    
    # Run evaluation
    report = await framework.run_evaluation(
        max_questions=args.max_questions,
        sample_categories=args.sample_categories
    )
    
    # Print and save report
    framework.print_report(report)
    framework.save_report(report, args.output)
    
    # Final grade
    avg_score = report['summary']['average_score']
    if avg_score >= 80:
        grade = "A - Excellent"
        emoji = "🌟"
    elif avg_score >= 70:
        grade = "B - Good"
        emoji = "✅"
    elif avg_score >= 60:
        grade = "C - Satisfactory"
        emoji = "👍"
    elif avg_score >= 50:
        grade = "D - Needs Improvement"
        emoji = "⚠️"
    else:
        grade = "F - Requires Major Improvements"
        emoji = "❌"
    
    print()
    print("╔" + "═" * 68 + "╗")
    print(f"║  FINAL GRADE: {grade:40s} {emoji}     ║")
    print("╚" + "═" * 68 + "╝")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
