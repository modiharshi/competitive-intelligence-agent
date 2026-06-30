from ..schemas import StrategicHypothesis, EarlyWarningAlert

class EarlyWarningEngine:
    def calculate_threat_score(self, hypothesis: StrategicHypothesis) -> EarlyWarningAlert:
        # 1. Map urgency from time_horizon
        horizon = hypothesis.time_horizon
        if horizon == "Short-Term":
            urgency_val = 1.0
            urgency = "High"
        elif horizon == "Mid-Term":
            urgency_val = 0.7
            urgency = "Medium"
        else:
            urgency_val = 0.4
            urgency = "Low"

        # 2. Determine business impact based on theme content
        theme_lower = hypothesis.theme.lower()
        if "pricing" in theme_lower:
            impact_val = 1.0
            business_impact = "Critical"
        elif "product" in theme_lower:
            impact_val = 0.8
            business_impact = "Major"
        else:
            impact_val = 0.5
            business_impact = "Minor"

        # w1 = 0.4, w2 = 0.6
        w1, w2 = 0.4, 0.6
        raw_score = hypothesis.confidence_score * (w1 * urgency_val + w2 * impact_val)
        # Scaled to 0-100 range, rounded to 1 decimal place
        score = round(raw_score * 100, 1)

        description = (
            f"Early warning alert for {hypothesis.competitor_name}: "
            f"Detected '{hypothesis.theme}' with score {score}."
        )

        return EarlyWarningAlert(
            id=f"ewa-{hypothesis.id.removeprefix('hyp-')}",
            hypothesis_id=hypothesis.id,
            early_warning_score=score,
            urgency=urgency,
            business_impact=business_impact,
            threat_description=description
        )
