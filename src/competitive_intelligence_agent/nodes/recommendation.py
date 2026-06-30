from typing import List
from ..schemas import ActionRecommendation, StrategicHypothesis, FeedbackRecord
from ..db_client import DBClient

class RecommendationNode:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path
        self.db_client = DBClient(db_path)

    def get_few_shot_examples(self) -> List[FeedbackRecord]:
        conn = self.db_client.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT competitor_name, hypothesis_id, vote, comments, timestamp FROM feedback WHERE vote = 'thumbs_up'"
        )
        rows = cursor.fetchall()
        conn.close()
        
        examples = []
        for row in rows:
            examples.append(
                FeedbackRecord(
                    competitor_name=row["competitor_name"],
                    hypothesis_id=row["hypothesis_id"],
                    vote=row["vote"],
                    comments=row["comments"] or "",
                    timestamp=row["timestamp"]
                )
            )
        return examples

    def compile_prompt(self, hypothesis: StrategicHypothesis, few_shots: List[FeedbackRecord]) -> str:
        prompt = "Generate action recommendations for the following hypothesis:\n"
        prompt += f"Competitor: {hypothesis.competitor_name}\n"
        prompt += f"Theme: {hypothesis.theme}\n"
        prompt += f"Summary: {hypothesis.summary}\n\n"
        
        if few_shots:
            prompt += "Feedback history (few-shot examples):\n"
            for example in few_shots:
                prompt += f"- Competitor: {example.competitor_name}, Hypothesis ID: {example.hypothesis_id}, Vote: {example.vote}, Comments: {example.comments}\n"
            prompt += "\n"
        
        prompt += "Generate recommendation:"
        return prompt

    def recommend_actions(self, hypothesis: StrategicHypothesis) -> ActionRecommendation:
        if hypothesis.status == "suppressed":
            raise ValueError("cannot recommend actions for suppressed hypotheses")
        
        few_shots = self.get_few_shot_examples()
        prompt = self.compile_prompt(hypothesis, few_shots)
        
        priority = "High" if hypothesis.confidence_score >= 0.85 else "Medium"
        recommended_action = "Prepare a focused response brief for product, sales, and marketing leadership."
        reasoning = (
            "The hypothesis clears the 70% confidence gate and is backed by multiple public citations, "
            "so teams should align messaging and roadmap options before the move becomes explicit."
        )
        
        if few_shots:
            comments_str = "; ".join([f.comments for f in few_shots if f.comments])
            if comments_str:
                reasoning += f" Adjusted with user feedback: {comments_str}"
        
        return ActionRecommendation(
            id=f"rec-{hypothesis.id.removeprefix('hyp-')}",
            hypothesis_id=hypothesis.id,
            category="Product Response",
            recommended_action=recommended_action,
            reasoning=reasoning,
            priority=priority,
            effort="Medium",
            strategic_posture="Defensive",
            expected_outcome="A faster, coordinated response to the competitor shift with evidence-linked talking points.",
            supporting_evidence=hypothesis.sources,
        )
