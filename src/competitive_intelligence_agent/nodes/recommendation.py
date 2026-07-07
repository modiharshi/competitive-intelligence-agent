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
        
        theme = hypothesis.theme
        priority = "High" if hypothesis.confidence_score >= 0.85 else "Medium"
        
        # Build contextual executive recommendations
        if "Enterprise Scaling" in theme:
            category = "Strategic Initiatives"
            recommended_action = "Initiate proactive enterprise compliance audit and speed up enterprise sales enablement."
            reasoning = "Correlated infrastructure hiring spikes and secure Kubernetes documentation changes indicate an imminent play into regulated SaaS sectors."
            posture = "Offensive"
            outcome = "Secured market share among compliance-sensitive institutional customers."
        elif "Pricing Strategy" in theme:
            category = "Product Response"
            recommended_action = "Draft a customer value survey and evaluate value-add bundle options for threatened tiers."
            reasoning = "Pricing modifications combined with negative user feedback signals high churn risk. Defensive bundles mitigate immediate loss."
            posture = "Defensive"
            outcome = "Reduced customer churn on price-sensitive accounts."
        elif "New Product Launch" in theme:
            category = "Marketing Response"
            recommended_action = "Launch target search campaign keyword conquesting and prepare comparative collateral for sales."
            reasoning = "Pre-launch documentation additions coupled with announcement frequency spikes warrant early positioning updates."
            posture = "Defensive"
            outcome = "Neutralized competitor's first-mover launch marketing spikes."
        else:
            category = "Strategic Initiatives"
            recommended_action = "Increase crawler telemetry frequency for core endpoints and monitor executive announcements."
            reasoning = "General strategy movement detected; gathering further context is recommended before committing capital."
            posture = "Opportunistic"
            outcome = "Clearer competitive intelligence baseline."

        if few_shots:
            comments_str = "; ".join([f.comments for f in few_shots if f.comments])
            if comments_str:
                reasoning += f" [Feedback Alignment: {comments_str}]"
        
        return ActionRecommendation(
            id=f"rec-{hypothesis.id.removeprefix('hyp-')}",
            hypothesis_id=hypothesis.id,
            category=category,
            recommended_action=recommended_action,
            reasoning=reasoning,
            priority=priority,
            effort="Medium",
            strategic_posture=posture,
            expected_outcome=outcome,
            supporting_evidence=hypothesis.sources,
        )
