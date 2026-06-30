from datetime import datetime, timedelta
from typing import List, Dict
from ..schemas import SignalEvent, SignalRelation

class IntelligenceAgent:
    def parse_timestamp(self, ts_str: str) -> datetime:
        # Handles standard ISO formats (with or without Z / Offset)
        ts_clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_clean)

    def correlate_timeline(self, signals: List[SignalEvent]) -> List[List[SignalEvent]]:
        if not signals:
            return []

        # Sort signals chronologically
        sorted_signals = sorted(signals, key=lambda s: self.parse_timestamp(s.timestamp))

        clusters = []
        current_cluster = []
        cluster_start_time = None

        for signal in sorted_signals:
            sig_time = self.parse_timestamp(signal.timestamp)
            if not current_cluster:
                current_cluster.append(signal)
                cluster_start_time = sig_time
            else:
                # Check if this signal falls within 30 days of the start of the current cluster
                if sig_time - cluster_start_time <= timedelta(days=30):
                    current_cluster.append(signal)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [signal]
                    cluster_start_time = sig_time

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    def map_relations(self, cluster: List[SignalEvent]) -> List[SignalRelation]:
        relations = []
        # Sort cluster chronologically to establish preceding links
        sorted_cluster = sorted(cluster, key=lambda s: self.parse_timestamp(s.timestamp))
        
        for i in range(len(sorted_cluster) - 1):
            source = sorted_cluster[i]
            target = sorted_cluster[i + 1]
            
            # 1. Check for opposing indicators (contradicts)
            source_content = source.content_diff.lower()
            target_content = target.content_diff.lower()
            if (("add" in source_content and "remov" in target_content) or
                ("remov" in source_content and "add" in target_content) or
                ("spik" in source_content and "drop" in target_content) or
                ("drop" in source_content and "spik" in target_content)):
                relation_type = "contradicts"
            
            # 2. Check for spikes/hiring triggers product shifts (causes)
            elif source.category == "Hiring" and target.category == "Product":
                relation_type = "causes"
                
            # 3. Check for same categories with increasing impact (amplifies)
            elif source.category == target.category:
                if target.impact_score > source.impact_score:
                    relation_type = "amplifies"
                else:
                    relation_type = "supports"
            
            # 4. Default temporal precedes
            else:
                relation_type = "precedes"
                
            relations.append(SignalRelation(
                source_id=source.id,
                target_id=target.id,
                relation_type=relation_type
            ))
            
        return relations

